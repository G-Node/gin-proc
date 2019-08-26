<a name="operations"></a>
## Operations

<a name="after-login"></a>
#### What happens just after you Log-In

To read API operations after `login`, please visit: `<YOUR_GIN-PROC_SERVER_ADDRESS>:8000/docs/api`

<br>

<a name="after-workflow"></a>
#### What happens after you run the workflow from front-end

Your input data from the front-end is sent to the REST API running on port `8000` on the same address. And the API takes over the job from there.

Read API Documentation for more info at: `<YOUR_GIN-PROC_SERVER_ADDRESS>:8000/docs/api`

<br>

<a name="pipeline"></a>
### Inside the Pipeline

The Drone config `gin-proc` service writes for you essentially does the following inside Drone containers (/runners) in chronological order:

**+** Run a check whether you have run any previous builds on the repository in question, and if yes - then restore the repo from cache in order to speed up the clone process afterwards.

**+** Starts the SSH agent.

**+** Creates an SSH direcotory and writes your `priv-key` from Drone secrets of that repository to that directory, for Drone's use to clone your repository from GIN afterwards.

**+** Disables `Strict Host Checking` for all authorized keys.

**+** Adds your newly written `priv-key` to the SSH agent.

**+** Runs a keyscan on your GIN container and writes the returned SSH fingerprint to `authorized_keys`

**+** Clones your repository from GIN.

**+** Installs Python dependencies if a `requirements.txt` file exists in your repo.

**+** Annex your files if you had mentioned any files to be annexed - after initialising an annex repo in the working directory.

**+** Attaches the commands or runs the Snakefile depending on your workflow chosen.

**+** Add the backpush files, if you added any, and push them back to your repository in a separate `gin-proc` branch after completion of build job.

**+** Pushes the produced output files back finally.

**+** Rebuilds the latest cache of the repo after final operations.

**+** Integrates the required volumes := `/cache` and `/repo`

**+** Tells Drone to only run the build job in the event if you **pushed** to the **master** branch of your repository. Not in any otherwise case.

 **+** Attaches Slack or Email notification plugin if you had selected it from the front-end.