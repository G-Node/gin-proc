# ------------------------------------------------------------------#
# Service: gin-proc
# Project: GIN - https://gin.g-node.org
# Documentation: https://github.com/G-Node/gin-proc/blob/master/docs
# Package: Config
# ------------------------------------------------------------------#


import os
import yaml
from logger import log
from errors import ConfigurationError


def preparationCommands():

    """
    Returns list of exact bash commands required initially in the
    execution step to prepare workspace for pipeline.
    """

    return [
            'eval $(ssh-agent -s)',
            'mkdir -p /root/.ssh && echo "$SSH_KEY" > \
/root/.ssh/id_rsa && chmod 0600 /root/.ssh/id_rsa',
            'mkdir -p /etc/ssh',
            'echo "StrictHostKeyChecking no" >> \
/etc/ssh/ssh_config',
            'ssh-add /root/.ssh/id_rsa',
            'git config --global user.name "gin-proc"',
            'git config --global user.email "gin-proc@local"',
            'ssh-keyscan -t rsa "$DRONE_GOGS_SERVER" > \
/root/.ssh/authorized_keys',
            'if [ -d "$DRONE_REPO_NAME" ]; then cd "$DRONE_REPO_NAME"/ \
&& git fetch --all && git checkout "$DRONE_COMMIT"; \
else git clone "$DRONE_GIT_SSH_URL" \
&& cd "$DRONE_REPO_NAME"/ && pip3 install -r requirements.txt; fi',
    ]


def createVolume(name, path):

    """
    Returns a new volume dictionary.
    """

    return {'name': name, 'path': path}


def createEnv(name, secret):

    """
    Returns a new environment variable dictionary with name and secret.
    """

    return {name: {'from_secret': secret}}


def createStep(
        name,
        image,
        volumes=None,
        settings=None,
        environment=None,
        commands=None
        ):

    """
    Generates a new pipeline step configuration.
    """

    PAYLOAD = {}
    PAYLOAD['name'] = name
    PAYLOAD['image'] = image
    if volumes:
        PAYLOAD['volumes'] = volumes
    if settings:
        PAYLOAD['settings'] = settings
    if environment:
        PAYLOAD['environment'] = environment
    if commands:
        PAYLOAD['commands'] = commands

    return PAYLOAD


def joindronefiles(files, location=''):

    """
    Join filenames from user's entered list in a single string
    to make it processible.
    """

    return ' '.join(
        '"{}"'.format(
            os.path.join(location, filename)) for filename in files)


def addBackPush(files, commands):

    """
    Adds commands to execution step for pushing the user's output files
    back to gin-proc branch in the GIN repository.
    """

    if len(files) > 0:
        inputdronefiles = joindronefiles(files)

        commands.append('TMPLOC=`mktemp -d`')
        commands.append(('mv {} "$TMPLOC"').format(inputdronefiles))

        commands.append('git checkout gin-proc || git checkout -b gin-proc')
        commands.append('git reset --hard')
        commands.append('mkdir "$DRONE_BUILD_NUMBER"')

        inputdronefiles = joindronefiles(files, "$TMPLOC")

        commands.append('mv {} "$DRONE_BUILD_NUMBER"/'.format(
            inputdronefiles))

        commands.append('git annex add -c annex.largefiles="largerthan=10M" \
"$DRONE_BUILD_NUMBER"/')
        commands.append('git commit "$DRONE_BUILD_NUMBER"/ -m "Back-Push"')
        commands.append('git push origin gin-proc')
        commands.append('git annex copy --to=origin --all')

    return commands


def addAnnex(files, commands):

    """
    Adds bash commands to get annex files required in workflow.
    """

    try:
        if len(files) > 0:
            inputdronefiles = joindronefiles(files)

            commands.append('git annex init "$DRONE_REPO_NAME"-drone-annexe')
            commands.append("git annex get {}".format(inputdronefiles))

    except Exception as e:
        log('exception', e)

    finally:
        return commands


def createWorkflow(workflow, commands, user_commands=None):

    """
    Adds approriate bash commands as per user's specified workflow
    i.e.
        either Snakemake file's location
        or Custom commands.
    """

    try:
        if workflow == 'snakemake':
            if user_commands:
                commands.append('snakemake --snakefile {}/snakefile'.format(
                    user_commands[0]))
            else:
                commands.append('snakemake')
        else:
            for command in user_commands:
                commands.append(command)

    except Exception as e:
        log('exception', e)

    finally:
        return commands


def integrateVolumes(volumes):

    """
    Returns a new volume dictionary provided name and path values.
    """

    PAYLOAD = []

    for volume in volumes:
        PAYLOAD.append(
            {
                'name': volume[0],
                'host': {'path': volume[1]}
            }
        )

    return PAYLOAD


def generateConfig(
        workflow,
        commands,
        annexFiles,
        backPushFiles,
        notifications
        ):

    """
    Automates generation of a fresh configuration for Drone
    by adding necessary vanilla state pipeline steps and
    integrating required volumes as per requirements.

    Two of the most important steps added in this functions
    are:

        (a) restore-cache - for restoring entire cached volume
        to speed up (or potentially) avoid the future repo cloning
        opertaion.

        (b) rebuild-cache - for rebuilding the latest volume cache
        after workflow execution has compeleted.

    Any notification steps or triggers or volumes that have to be
    mounted are only added after the step which has rebuilt cache.
    """

    try:

        log("debug", "Writing fresh configuration.")

        data = {
            'kind': 'pipeline',
            'name': 'gin-proc',

            'clone': {
                'disable': True
            },

            'steps': [
                createStep(
                    name='restore-cache',
                    image='drillster/drone-volume-cache',
                    volumes=[createVolume('cache', '/cache')],
                    settings={
                        'restore': True,
                        'mount': '/drone/src'
                        },
                ),
                createStep(
                    name='execute',
                    image='falconshock/gin-proc:micro-test',
                    volumes=[createVolume('repo', '/repo')],
                    environment=createEnv(
                        'SSH_KEY',
                        'DRONE_PRIVATE_SSH_KEY'
                        ),
                    commands=preparationCommands()
                ),
                createStep(
                    name='rebuild-cache',
                    image='drillster/drone-volume-cache',
                    volumes=[createVolume('cache', '/cache')],
                    settings={
                        'rebuild': True,
                        'mount': '/drone/src'
                        },
                ),
            ],
            'volumes': integrateVolumes([
                ('cache', '/gin-proc/cache'),
                ]),
            'trigger': {
                'branch': ['master'],
                'event': ['push'],
                'status': ['success']
            }
        }

        data['steps'][1]['commands'] = modifyConfigFiles(
            workflow=workflow,
            annexFiles=annexFiles,
            backPushFiles=backPushFiles,
            commands=commands,
            data=data['steps'][1]['commands']
        )

        data['steps'] = addNotifications(
            notifications=notifications,
            data=data['steps']
        )

        log("debug", "Configuration complete.")

        return data

    except Exception as e:
        log('exception', e)
        return False


def modifyConfigFiles(
        data,
        annexFiles,
        workflow,
        backPushFiles,
        commands
        ):

    """
    Modifies the workflow and notification steps as required
    on existing pipeline configuration.
    """

    try:
        log("debug", "Adding user's files.")

        data = addAnnex(annexFiles, data)

        data = createWorkflow(workflow, data, commands)

        data = addBackPush(backPushFiles, data)

        return data

    except Exception as e:
        log('exception', e)


def addNotifications(notifications, data):

    """
    Adds additional pipeline step for notifying the user
    post completion of build job on service of choice
    - mostly Slack.
    """

    notifications = [n for n in notifications if n['value']]

    for step in data:
        if step['name'] == "notification":
            del data[data.index(step)]

    for notification in notifications:
        if notification['name'] == 'Slack':

            log("info", "Adding notification: {}".format(notification['name']))

            data.append(
                createStep(
                    name='notification',
                    image='plugins/slack',
                    settings={
                        'webhook': "https://hooks.slack.com/services/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"
                    }
                )
            )

    return data


def ensureConfig(
        config_path,
        userInputs,
        workflow='snakemake',
        annexFiles=[],
        backPushFiles=[],
        notifications=[]
        ):

    """
    First line of defense!

    Runs following checks:

        1. Whether or not a pipeline configuration already exists.
        2. If it exists, is it corrupt or un-processible?
        3. If not, do the preparation commands required in
        execution step match our standards.

    Resolutions to above checks:

        For case 1: Initiates generation of a fresh configuration, if doesn't.
        For cases 2 and 3: Raises error and initiates overriting of existing
        configuration with a yet fresh one -- this will delete user's
        manual changes to configuration.

    Complete documentation for all operations in this function
    can also be accessed at:

    https://github.com/G-Node/gin-proc/blob/master/docs/operations.md

    """

    dronefile = os.path.join(config_path, '.drone.yml')
    execution_step = None

    try:
        if not os.path.exists(dronefile) or os.path.getsize(dronefile) <= 0:
            raise ConfigurationError("CI Config either not found in repo or is corrupt.")

        else:

            log("debug", "Updating already existing CI Configuration.")

            config = []
            with open(dronefile, 'r') as stream:
                config = yaml.load(stream, Loader=yaml.FullLoader)

                execution_step = [
                    step for step in config['steps'] if
                    step['name'] == 'execute'
                        ][0]

                if execution_step['commands'][:len(
                        preparationCommands())] != preparationCommands():

                    raise ConfigurationError(
                        "Existing CI Config does not match correct \
preparation mechanism for pipeline.")

            with open(dronefile, 'w') as stream:

                config['steps'][config['steps'].index(
                    execution_step)]['commands'] = modifyConfigFiles(
                    workflow=workflow,
                    annexFiles=annexFiles,
                    backPushFiles=backPushFiles,
                    commands=userInputs,
                    data=config['steps'][config['steps'].index(execution_step)]
                    ['commands'][:len(
                        preparationCommands())]
                )

                config['steps'] = addNotifications(
                    notifications=notifications,
                    data=config['steps']
                )

                yaml.dump(
                    config,
                    stream,
                    default_flow_style=False)

    except ConfigurationError as e:
        log('error', e)
        log('info', 'Generating fresh configuration.')

        with open(os.path.join(config_path, '.drone.yml'), 'w') \
            as new_config:
            generated_config = generateConfig(
                    workflow=workflow,
                    commands=userInputs,
                    annexFiles=annexFiles,
                    backPushFiles=backPushFiles,
                    notifications=notifications
                    )

            if not generated_config:
                return False
            else:
                yaml.dump(
                    generated_config,
                    new_config,
                    default_flow_style=False)
