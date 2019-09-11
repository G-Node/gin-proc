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


# List of shell commands required initially in the execution step to prepare
# workspace for pipeline.
prep_commands = (
    'eval $(ssh-agent -s)',
    'mkdir -p /root/.ssh',
    'echo "$SSH_KEY" > /root/.ssh/id_rsa',
    'chmod 0600 /root/.ssh/id_rsa',
    'mkdir -p /etc/ssh',
    'echo "StrictHostKeyChecking no" >> /etc/ssh/ssh_config',
    'ssh-add /root/.ssh/id_rsa',
    'git config --global user.name "gin-proc"',
    'git config --global user.email "gin-proc@local"',
    'ssh-keyscan -t rsa "$DRONE_GOGS_SERVER" > /root/.ssh/authorized_keys',
    '''if [ -d "$DRONE_REPO_NAME" ]; then
           cd "$DRONE_REPO_NAME"/;
           git fetch --all;
           git checkout -f "$DRONE_COMMIT";
       else
           git clone "$DRONE_GIT_SSH_URL";
           cd "$DRONE_REPO_NAME"/;
       fi'''
)


def create_step(name, image, volumes=None, settings=None, environment=None,
                commands=None):

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


def join_drone_files(files, location=''):

    """
    Join filenames from user's entered list in a single string
    to make it processible.
    """

    return ' '.join(
        '"{}"'.format(
            os.path.join(location, filename)) for filename in files)


def add_output_files(files, commands):

    """
    Adds commands to execution step for pushing the user's output files
    back to gin-proc branch in the GIN repository.
    """

    if len(files) > 0:
        input_drone_files = join_drone_files(files)

        commands.append('TMPLOC=`mktemp -d`')
        commands.append(f'mv {input_drone_files} "$TMPLOC"')

        commands.append('git checkout gin-proc || git checkout -b gin-proc')
        commands.append('git reset --hard')
        commands.append('mkdir "$DRONE_BUILD_NUMBER"')

        input_drone_files = join_drone_files(files, "$TMPLOC")

        commands.append(f'mv {input_drone_files} "$DRONE_BUILD_NUMBER"/')

        commands.append('git annex add -c annex.largefiles="largerthan=10M" '
                        '"$DRONE_BUILD_NUMBER"/')
        commands.append('git commit "$DRONE_BUILD_NUMBER"/ -m "Back-Push"')
        commands.append('git push origin gin-proc')
        commands.append('git annex copy --to=origin --all')

    return commands


def add_input_files(files, commands):
    """
    Adds commands to 'git annex get' input files to ensure annexed content
    """
    if len(files) > 0:
        input_drone_files = join_drone_files(files)
        commands.append("git annex init gin-proc")
        commands.append(f"git annex get {input_drone_files}")

    return commands


def create_workflow(workflow, commands, user_commands=None):
    """
    Adds appropriate shell commands based on user's specified workflow
    """
    if workflow == 'snakemake':
        if user_commands:
            commands.append(
                f'snakemake --snakefile {user_commands[0]}/snakefile'
            )
        else:
            commands.append('snakemake')
    else:
        for command in user_commands:
            commands.append(command)
    return commands


def generate_config(workflow, commands, input_files, output_files,
                    notifications):
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
            'clone': {'disable': True},
            'steps': [
                create_step(
                    name='restore-cache',
                    image='drillster/drone-volume-cache',
                    volumes=[{'name': 'cache', 'path': '/cache'}],
                    settings={
                        'restore': True,
                        'mount': '/drone/src'
                        },
                ),
                create_step(
                    name='execute',
                    image='falconshock/gin-proc:micro-test',
                    volumes=[{'name': 'repo', 'path': '/repo'}],
                    environment={
                        'SSH_KEY': {'from_secret': 'DRONE_PRIVATE_SSH_KEY'}
                    },
                    commands=prep_commands
                ),
                create_step(
                    name='rebuild-cache',
                    image='drillster/drone-volume-cache',
                    volumes=[{'name': 'cache', 'path': '/cache'}],
                    settings={'rebuild': True, 'mount': '/drone/src'},
                ),
            ],
            'volumes': [{'name': 'cache',
                         'host': {'path': '/gin-proc/cache'}}],
            'trigger': {
                'branch': ['master'],
                'event': ['push'],
                'status': ['success']
            }
        }

        data['steps'][1]['commands'] = modify_config_files(
            workflow=workflow,
            input_files=input_files,
            output_files=output_files,
            commands=commands,
            data=data['steps'][1]['commands']
        )

        data['steps'] = add_notifications(
            notifications=notifications,
            data=data['steps']
        )

        log("debug", "Configuration complete.")

        return data

    except Exception as e:
        log('exception', e)
        return False


def modify_config_files(data, input_files, workflow, output_files, commands):
    """
    Modifies the workflow and notification steps as required
    on existing pipeline configuration.
    """
    try:
        log("debug", "Adding user's files.")
        data = add_input_files(input_files, data)
        data = create_workflow(workflow, data, commands)
        data = add_output_files(output_files, data)
        return data
    except Exception as e:
        log('exception', e)


def add_notifications(notifications, data):
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
            slackhook = ("https://hooks.slack.com/services/TFZHJ0RC7/"
                         "BK9MDBKHQ/VvPkhb4q6odutAkjw6t7Ssr3")

            data.append(
                create_step(
                    name='notification',
                    image='plugins/slack',
                    settings={
                        'webhook': slackhook
                    }
                )
            )

    return data


def ensure_config(config_path, user_commands, workflow='snakemake',
                  input_files=None, output_files=None, notifications=None):
    """
    First line of defense!

    Runs following checks:

        1. Whether or not a pipeline configuration already exists.
        2. If it exists, is it corrupt or un-processable?
        3. If not, do the preparation commands required in
        execution step match our standards.

    Resolutions to above checks:

        For case 1: Initiates generation of a fresh configuration, if doesn't.
        For cases 2 and 3: Raises error and initiates overwriting of existing
        configuration with a yet fresh one -- this will delete user's
        manual changes to configuration.

    Complete documentation for all operations in this function
    can also be accessed at:

    https://github.com/G-Node/gin-proc/blob/master/docs/operations.md
    """
    if not input_files:
        input_files = list()
    if not output_files:
        output_files = list()
    if not notifications:
        notifications = list()
    dronefile = os.path.join(config_path, '.drone.yml')
    execution_step = None

    try:
        if not os.path.exists(dronefile) or os.path.getsize(dronefile) <= 0:
            raise ConfigurationError(
                "CI Config either not found in repo or is corrupt."
            )
        else:
            log("debug", "Updating already existing CI Configuration.")
            with open(dronefile, 'r') as stream:
                config = yaml.load(stream, Loader=yaml.FullLoader)

                execution_step = [step for step in config['steps']
                                  if step['name'] == 'execute'][0]

                pcmds = execution_step["commands"][:len(prep_commands)]
                if pcmds != prep_commands:
                    raise ConfigurationError(
                        "Existing CI Config does not match correct "
                        "preparation mechanism for pipeline."
                    )

            with open(dronefile, 'w') as stream:

                config['steps'][config['steps'].index(
                    execution_step)]['commands'] = modify_config_files(
                    workflow=workflow,
                    input_files=input_files,
                    output_files=output_files,
                    commands=user_commands,
                    data=config['steps'][config['steps'].index(execution_step)]
                    ['commands'][:len(prep_commands)]
                )

                config['steps'] = add_notifications(
                    notifications=notifications,
                    data=config['steps']
                )

                yaml.dump(config, stream, default_flow_style=False)

    except ConfigurationError as e:
        log('error', e)
        log('info', 'Generating fresh configuration.')
        with open(os.path.join(config_path, '.drone.yml'), 'w') as new_config:
            generated_config = generate_config(workflow=workflow,
                                               commands=user_commands,
                                               input_files=input_files,
                                               output_files=output_files,
                                               notifications=notifications)
            if not generated_config:
                return False
            yaml.dump(generated_config, new_config, default_flow_style=False)


def create_drone_file(config_path, user_commands, workflow='snakemake',
                      input_files=None, output_files=None, notifications=None):
    with open(os.path.join(config_path, '.drone.yml'), 'w') as new_config:
        generated_config = generate_config(workflow=workflow,
                                           commands=user_commands,
                                           input_files=input_files,
                                           output_files=output_files,
                                           notifications=notifications)
        if not generated_config:
            return False
        yaml.dump(generated_config, new_config, default_flow_style=False)

    return True
