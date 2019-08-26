<a name="usage"></a>
## Usage

Go to your `gin-proc` address on port 3000 to access the service UI. Only use your GIN credentials to login. Users are not required to signup separately for `gin-proc`.

<a name="workflows"></a>
### Types of Workflows

**Snakemake** - If you choose this workflow, you can enter the location of your Snakefile in your repo. If nothing is mentioned in location on during submission, then default location will be assumed to be the root of the repository.

**Custom** - Users can enter the exact commands they want to run inside containers post cloning of the repository. Commands will be executed in the same exact order they are added to the workflow in.

<a name="files"></a>
### User's files

**Annex Files** - Users can mention whether any files have to be especially `git-annex`ed before executing the workflow.

**BackPush Files** - Users can mention the output files produced post execution of the workflow to be pushed back to user's GIN repository. Files will be pushed to a separate `gin-proc` branch in the repository.
