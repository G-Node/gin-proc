# ------------------------------------------------------------------#
# Service: gin-proc
# Project: GIN - https://gin.g-node.org
# Documentation: https://github.com/G-Node/gin-proc/blob/master/docs
# Package: Service
# ------------------------------------------------------------------#
# Env variables assigned
# export GIN_SERVER=http://172.19.0.2:3000
# export DRONE_SERVER=http://172.19.0.3
# DRONE_TOKEN=AAAAAAAAAA000000000000000XXXXXXXXX
# ------------------------------------------------------------------#


import requests
import os
from shutil import rmtree
import tempfile

from http import HTTPStatus
from config import ensureConfig
from logger import log
from subprocess import call
from errors import ServiceError, ServerError

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

GIN_ADDR = os.environ['GIN_SERVER']
DRONE_ADDR = os.environ['DRONE_SERVER']

PRIV_KEY = 'gin_id_rsa'
PUB_KEY = '{}.pub'.format(PRIV_KEY)
SSH_PATH = os.path.join(os.environ['HOME'], 'gin-proc', 'ssh')


def userData(token):

    """
    Returns logged-in user's data from GIN.
    """

    return requests.get(
        GIN_ADDR + "/api/v1/user",
        headers={'Authorization': 'token {}'.format(token)}
        ).json()


def ensureToken(username, password):

    """
    Retrieves the personal access token `gin-proc`
    from user's GIN account to be used further in session.

    In case, the specific token for gin-proc doesn't exists,
    it registers a fresh token to GIN for that user.
    """

    try:
        res = requests.get(
            GIN_ADDR + "/api/v1/users/{}/tokens".format(username),
            auth=(username, password)).json()

        for token in res:
            if token['name'] == 'gin-proc':
                return token['sha1']

        res = requests.post(
            GIN_ADDR + "/api/v1/users/{}/tokens".format(username),
            auth=(username, password),
            data={'name': 'gin-proc'}
        ).json()

        return res['sha1']

    except Exception.ConnectionError as e:
        raise ServerError(e)


def writeSecret(key, repo, user):

    """
    Writes the key as a secret title `DRONE_PRIVATE_SSH_KEY`
    to specified repository in Drone.
    """

    try:
        res = requests.post(
            DRONE_ADDR + "/api/repos/{0}/{1}/secrets".format(user, repo),
            headers={
                'Authorization': 'Bearer {}'.format(os.environ['DRONE_TOKEN']),
                'Content-Type': "application/json"
                },
            json={
                "name": "DRONE_PRIVATE_SSH_KEY",
                "data": key,
                "pull_request": False
                }
        )

    except Exception.ConnectionError as e:
        raise ServerError(e)

    if res.status_code == HTTPStatus.OK:
        log('debug', 'Secret installed in `{}`'.format(repo))
        return True
    else:
        log('critical', res.json()['message'])
        raise ServerError('Secret could not be installed in `{}`'.format(repo),
            HTTPStatus.INTERNAL_SERVER_ERROR)


def updateSecret(secret, data, user, repo):

    """
    Ensure the secret DRONE_PRIVATE_SSH_KEY already exists,
    and if true, update the secret with latest key.
    Else, register the key as a secret.
    """

    res = requests.patch(
        DRONE_ADDR + "/api/repos/{user}/{repo}/secrets/{secret}".format(
            user=user,
            repo=repo,
            secret=secret),
        headers={'Authorization': 'Bearer ' + os.environ['DRONE_TOKEN']},
        json={
            "data": data,
            "pull_request": False
        })

    if res.status_code == HTTPStatus.OK:
        log('debug', 'Secret updated in `{}`'.format(repo))
        return True
    else:
        raise ServerError('Secret could not be updated in `{}`'.format(repo),
            HTTPStatus.INTERNAL_SERVER_ERROR)


def ensureSecrets(user):

    """
    Runs a check on all of user's ACTIVATED Drone repositories
    if each of them has the secret DRONE_PRIVATE_SSH_KEY and is updated
    with the latest key.

    Initiates the installation process for secret, if it doesn't exists.
    """

    repos = requests.get(
        DRONE_ADDR + "/api/user/repos",
        headers={
            'Authorization': 'Bearer {}'.format(os.environ['DRONE_TOKEN'])
            }).json()

    for repo in [repo for repo in repos if repo['active']]:

        secrets = requests.get(
            DRONE_ADDR + "/api/repos/{0}/{1}/secrets".format(
                user, repo['name']),
            headers={'Authorization': 'Bearer {}'.format(
                os.environ['DRONE_TOKEN'])}
            ).json()

        with open(os.path.join(SSH_PATH, PRIV_KEY), 'r') as key:

            for secret in secrets:
                if secret['name'] == 'DRONE_PRIVATE_SSH_KEY':
                    log('debug', 'Secret found in repo `{}`'.format(
                        repo['name']))

                    updateSecret(
                        secret=secret['name'],
                        data=key.read(),
                        repo=repo['name'],
                        user=user
                    )
                    break

            log('debug', 'Secret not found in `{}`'.format(repo['name']))
            writeSecret(key.read(), repo['name'], user)

    return True


def getKeysFromServer(token):

    """
    Fetches all SSH public keys from user's GIN account.
    """

    return requests.get(
        GIN_ADDR + "/api/v1/user/keys",
        headers={'Authorization': 'token {}'.format(token)}
        ).json()


def ensureKeysOnServer(token):

    """
    Confirms whether the public key 'gin-proc' is installed
    on usre's GIN account or not.
    """

    for key in getKeysFromServer(token):
        if key['title'] == PRIV_KEY:
            return True


def deleteKeysOnServer(token):

    """
    Deletes key 'gin-proc' from user's GIN account.
    """

    for key in getKeysFromServer(token):
        if key['title'] == PRIV_KEY:
            response = requests.delete(
                key['url'],
                headers={'Authorization': 'token {}'.format(token)}
                )

            if response.status_code == 204:
                log('warning', 'Deleted keys from server.')
                return True
            else:
                log('error', response.text)
                raise ServerError(
                    "You'll have to manually delete the keys from the server.",
                    HTTPStatus.SERVICE_UNAVAILABLE)


def ensureKeysOnLocal(path):

    """
    Confirms whether SSH Private key exists locally or not.
    """

    return os.path.exists(os.path.join(path, PRIV_KEY))


def installFreshKeys(SSH_PATH, token):

    """
    Generates a fresh pair of public and private keys.
    And installs them on user's GIN account.
    """

    key = rsa.generate_private_key(
        backend=default_backend(),
        public_exponent=65537,
        key_size=2048
    )
    private_key = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
        )
    public_key = key.public_key().public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH
    )

    os.makedirs(SSH_PATH, exist_ok=True)

    with open(
        os.path.join(SSH_PATH, PRIV_KEY),
            'w+') as private_key_file:

        private_key_file.write(private_key.decode('utf-8'))

    with open(
        os.path.join(SSH_PATH, PUB_KEY),
            'w+') as public_key_file:

        public_key_file.write(public_key.decode('utf-8'))

    os.chmod(SSH_PATH, 0o700)
    os.chmod(os.path.join(SSH_PATH, PRIV_KEY), 0o600)
    os.chmod(os.path.join(SSH_PATH, PUB_KEY), 0o600)

    requests.post(
        GIN_ADDR + "/api/v1/user/keys",
        headers={'Authorization': 'token ' + token},
        data={'title': PRIV_KEY, 'key': public_key}
    )

    log('info', 'Fresh key pair installed with pub key {}'.format(PUB_KEY))


def ensureKeys(token):

    """
    Runs following checks for required SSH key pair:

        1. Do keys exist both locally and GIN server?
        2. Do keys exist only locally but not on server?
        3. Do keys exist only on server but not locally?

    Resolution for above cases:

        Case 1: Returns positive response.
        Case 2: Delete keys locally and install a fresh pair both
        locally and on server.
        Case 3: Delete keys on server and install a fresh pair both
        locally and on server.
    """

    try:
        if ensureKeysOnServer(token) and ensureKeysOnLocal(SSH_PATH):
            log("debug", "Keys ensured both on server and locally.")

            return True

        elif ensureKeysOnServer(token) and not ensureKeysOnLocal(SSH_PATH):
            log("debug", "Key is installed on the server but not locally.")

            deleteKeysOnServer(token)

        elif not ensureKeysOnServer(token) and ensureKeysOnLocal(SSH_PATH):
            log("debug", "Key is installed locally but not on the server.")

            os.remove(os.path.join(SSH_PATH, PRIV_KEY))
            os.remove(os.path.join(SSH_PATH, PUB_KEY))
            log("warning", "Removed local keys.")

        installFreshKeys(SSH_PATH, token)

    except:
        log('critical', 'Failed to ensure keys.')
        raise ServerError('Cannot ensure keys.', HTTPStatus.INTERNAL_SERVER_ERROR)


def getRepos(user, token):

    """
    Fetches list of all repositories from user's GIN account.
    """

    return requests.get(
        GIN_ADDR + "/api/v1/users/{}/repos".format(user),
        headers={'Authorization': 'token {}'.format(token)},
        ).json()


def getRepoData(user, repo, token):

    """
    Fetches complete data of a repository from user's GIN account.
    """

    return requests.get(
        GIN_ADDR + "/api/v1/repos/{0}/{1}".format(user, repo),
        headers={'Authorization': 'token {}'.format(token)}
        ).json()


def clone(repo, author, path):

    """
    Clones the repository in question in a temporary location (path).
    """

    clone_path = os.path.join(path, author, repo['name'])
    os.makedirs(clone_path, exist_ok=True)

    call(['git', 'clone', '--depth=1', repo['clone_url'], clone_path])

    log("debug", "Repo cloned at {}".format(clone_path))
    return clone_path


def push(path, commitMessage):

    """
    Commits and pushes the updates from temporary location (path) the
    repository is stored at on to the GIN server.
    """

    call(['git', 'add', '.'], cwd=path)
    call(['git', 'commit', '-m', commitMessage], cwd=path)
    call(['git', 'push'], cwd=path)

    log("info", "Updates pushed from {}".format(path))


def clean(path):

    """
    Removes the cloned repository data and free the temporary space (path).
    """

    rmtree(path)
    log("debug", "Repo cleaned from {}".format(path))


def configure(
        repoName,
        userInputs,
        backPushFiles,
        annexFiles,
        commitMessage,
        notifications,
        token,
        username,
        workflow
        ):

    """
    First line of action!

    This function is reposible for integrating the entire workflow
    together and executing the following in chronological order:

        1. Fetches the repository data for repo in question.

        2. Specifies the 'GIT_SSH_COMMAND' to locally stored
        private key, in order to use it for all git operations henceforth.

        3. Generates a temporary location for all future git operations
        to take place in.

        4. Runs operation to ensure configuration.
        Complete documentation for all operations executed in 'ensureConfig'
        function can also be accessed at:

        https://github.com/G-Node/gin-proc/blob/master/docs/operations.md

        5. Commits and pushes any updates in the cloned repository
        after workflow configuration is complete and successfull.

        6. Deletes the cloned repository data and deletes temporary location.
    """

    try:
        repo = getRepoData(username, repoName, token)

    except Exception as e:
        log('error', e)
        raise ServiceError(e)

    os.environ['GIT_SSH_COMMAND'] = "ssh -i {}".format(
    os.path.join(SSH_PATH, PRIV_KEY))

    with tempfile.TemporaryDirectory() as temp_clone_path:
        clone_path = clone(repo, username, temp_clone_path)

        ensureConfig(
            config_path=clone_path,
            workflow=workflow,
            userInputs=userInputs,
            annexFiles=annexFiles,
            backPushFiles=backPushFiles,
            notifications=notifications
        )

        push(clone_path, commitMessage)
        clean(clone_path)
