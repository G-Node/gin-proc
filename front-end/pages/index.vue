<template>
<div>
  <sui-container>

      <sui-message header="Heads Up!" style="text-align:left">
        <sui-list bulleted>
          <sui-list-item>Don't separate files by commas. Use the `+` button to add a new file.</sui-list-item>
          <sui-list-item>Write file paths from your project's root. Use nested notation "<span class="log">subfolder/file</span>" if required.</sui-list-item>
          <sui-list-item>Go home and thank INCF for making your life easier!</sui-list-item>
        </sui-list>
      </sui-message>

      <sui-divider />

      <transition>
     <sui-message
     v-if="success_message.visible"
      info
      :content="success_message.content"
      dismissable
      @dismiss="dismissMessage('success')"
      />
      </transition>
      <transition>
     <sui-message
     v-if="error_message.visible"
      error
      :content="error_message.content"
      dismissable
      @dismiss="dismissMessage('error')"
      />
      </transition>
      <!--
      <sui-progress
      v-if="action.progress > 100"
      state="success"
      :percent="action.progress"
      size="small"
    />
    -->
      <sui-message
      v-if="repos.length == 0"
      color="red"
      header="We have a problem!"
      content="You don't seem to have any repositories."
      />

        <sui-form @submit.stop.prevent @submit="onSubmit" @reset="onReset">
          <sui-grid>

            <sui-grid-row>
          <sui-grid-column :width="16" textAlign="left">
            <sui-form-field required=true>
              <label><i class="icon folder outline" />Repository</label>
              <sui-dropdown placeholder="Choose One" search selection :options="repos" v-model="form.repo" />
            </sui-form-field>
          </sui-grid-column>
            </sui-grid-row>

            <sui-grid-row v-show="form.repo">
          <sui-grid-column :width="8" textAlign="left">
            <sui-form-field>
              <label>
                <i class="icon file alternate outline" />
                <span v-if="form.workflow =='custom'">Commands</span>
                <span v-else>SnakeFile Path</span>
                <a style="float:right; color:black" data-inverted='' data-tooltip="Files will be executed in the same order you add them in.">
                  <i class="icon help circle" /> </a>
                <i v-if="form.workflow =='custom'" class="icon plus" style="float:right" v-on:click="inputCounter += 1" />
                <i v-if="form.workflow =='custom' && inputCounter > 1" class="icon minus" style="float:right" v-on:click="removeInput" /></label>
              <sui-input v-for="x in inputCounter" :key="x" v-model="userInputs[x]" />
            </sui-form-field>
            <sui-form-field>
              <label>
                <i class="icon file alternate outline" />
                Annex files
                <a style="float:right; color:black" data-inverted='' data-tooltip="If no files are mentioned, then all required files will be annexed."><i class="icon help circle" /> </a>
                <i class="icon plus" style="float:right" v-on:click="annexCounter += 1" />
                <i class="icon minus" style="float:right" v-if="annexCounter > 1" v-on:click="removeAnnex" />
                </label>
              <sui-input v-for="x in annexCounter" :key="x" v-model="annexFiles[x]"></sui-input>
            </sui-form-field>
            <sui-form-field>
              <label>
                <i class="icon file alternate outline" />
                Backpush files
                <a style="float:right; color:black" data-inverted='' data-tooltip="These are the output files which will be pushed to a separate gin-proc branch in your repo."><i class="icon help circle" /> </a>
                <i class="icon plus" style="float:right" v-on:click="backpushCounter += 1" />
                <i class="icon minus" style="float:right" v-if="backpushCounter > 1" v-on:click="removeBackPush" /></label>
              <sui-input v-for="x in backpushCounter" :key="x" v-model="backpushFiles[x]"></sui-input>
            </sui-form-field>
            </sui-grid-column>
          <sui-grid-column :width="8" textAlign="left">
                          <sui-form-field>
              <label>
                <i class="icon file alternate outline" />
                Choose Workflow Style
                </label>
              <sui-dropdown selection :options="workflow" v-model="form.workflow" />
            </sui-form-field>
            <sui-form-field>
              <label><i class="icon paper plane outline" />Commit Message</label>
              <sui-input v-model="form.commitMessage" />
            </sui-form-field>
            <sui-form-field>
              <label><i class="icon bell outline" />Notifications</label>
              <sui-checkbox
              v-for="notification in form.notifications" 
              :key="notification.name"
              toggle 
              v-model="notification.value"> <sui-icon :name="notification.icon" /> {{notification.name}} &emsp;</sui-checkbox>
            </sui-form-field>
            </sui-grid-column>
            </sui-grid-row>
            <sui-grid-row v-show="form.repo">
              <sui-grid-column :width="8" textAlign="left">
                <i class="icon cog blue loading" v-if="action.active" />
          <sui-button type="submit" size="small" compact="true" color="green" :disabled="action.active" >
            Submit
            </sui-button>
          <sui-button type="reset" size="small" compact="true" basic="true" color="red">Reset</sui-button>
          </sui-grid-column>
              <sui-grid-column :width="8" textAlign="right">
          <span is=sui-button size="small" compact="true" basic="true" icon="archive" v-on:click="logs = !logs">Logs</span>
          <span is=sui-button size="small" compact="true" basic="true" icon="code" v-on:click="debug = !debug">Debug</span>
          <span is=sui-button size="small" compact="true" basic="true" icon="user secret" v-on:click="dev = !dev">Dev</span>
          </sui-grid-column>
          </sui-grid-row>
            <sui-grid-row>
              <sui-grid-column :width="16" textAlign="left">
                <sui-divider v-show="form.workflow" />

                <sui-segment inverted v-show="logs">
            <p class="log" v-for="log in  execution_status" :key="log">{{log}}</p>
                </sui-segment>
                <sui-segment inverted v-show="debug">
            <div class="log">
            <p>Form: {{ form }}</p>
            <p>user inpts: {{ userInputs }}</p>
            <p>Backpush Files: {{ backpushFiles }}</p>
            <p>Annex Files: {{ annexFiles }}</p>
            </div>
                </sui-segment>
                <sui-segment inverted v-show="dev">
            <p class="log">
              Logged In: {{this.$auth.loggedIn}} <br>
              Username: {{this.$auth.user.username}} <br>
              Token: {{$nuxt.$auth.getToken('local')}}
            </p>
                </sui-segment>
          </sui-grid-column>
          </sui-grid-row>
          </sui-grid>
        </sui-form>


  </sui-container>
  </div>
</template>

<script>
  import axios from "axios"
  var API = "http://127.0.0.1:8000/api"

  export default {

    async asyncData({
      params
    }) {
      let repos = await axios.get(API + '/repos')
      return {
        repos: repos.data
      }
    },
    data() {
      return {
        workflow: [
          {'text': 'Custom', 'value': 'custom'}, {'text': 'Snakemake', 'value': 'snakemake'}
        ],
        form: {
          repo: null,
          workflow: 'custom',
          notifications: [{
            'name': 'Slack',
            'value': false,
            'icon': 'slack hash'
          }],
          commitMessage: 'gin-proc is awesome',
        },
        success_message: {
          visible: false,
          content: "Complete! Check your Drone service for updates."
        },
        error_message: {
          visible: false,
          content: "Workflow failed. Kindly check logs for reports."
        },
        backpushFiles: {},
        userInputs: {},
        inputCounter: 1,
        backpushCounter: 1,
        annexFiles: {},
        annexCounter: 1,
        logs: false,
        debug: false,
        dev: false,
        execution_status: ["Waiting for your workflow."],
        action: {
          text: 'Submit',
          btn_state: true,
          active: false,
          variant: 'primary',
          progress: 0,
          complete: false,
          content: "Complete! Check your Drone service for updates."
        }
      }
    },
    methods: {
      removeInput() {
        delete this.userInputs[this.inputCounter]
        this.inputCounter -= 1
      },
      removeAnnex() {
        delete this.annexFiles[this.annexCounter]
        this.annexCounter -= 1
      },
      removeBackPush() {
        delete this.backpushFiles[this.backpushCounter]
        this.backpushCounter -= 1
      },
      dismissMessage(type) {
        if (type == "success") {this.success_message.visible = !this.success_message.visible}
        else {this.error_message.visible = !this.error_message.visible}
      },
      onReset() {
        this.form = {
          repo: null,
          notifications: [{
            'name': 'Slack',
            'value': false,
            'icon': 'slack hash'
          }],
          commitMessage: 'gin-proc is awesome',
          workflow: 'custom',
          },
          this.userInputs = {},
          this.backpushFiles = {},
          this.annexFiles = {},
        this.inputCounter = 1,
        this.backpushCounter = 1,
        this.annexCounter = 1,
          this.action = {
            text: 'Submit',
            btn_state: true,
            active: false,
            variant: 'primary',
            progress: 0
          },
          this.execution_status = ["Waiting for your workflow"]
      },
      onSubmit() {
        this.action.progress += 10,
        axios({
            method: "post",
            url: API + "/execute",
            data: {
              repo: this.form.repo,
              notifications: this.form.notifications,
              workflow: this.form.workflow,
              userInputs: this.userInputs,
              backpushFiles: this.backpushFiles,
              annexFiles: this.annexFiles,
              commitMessage: this.form.commitMessage,
            }
          })
          .then(
            this.action.text = "Processing", this.action.active = true, this.action.btn_state = false, this.action
            .progress += 50,
            this.execution_status.push("Designing workflow..."),
          )
          .then((response) => {
            if (response.status == 200) {
              this.execution_status.push(response.data),
                this.action.text = "Access Drone", this.action.active = false, this
                .action.variant = 'info', this.action.progress = 100,
                this.action.complete = true, this.success_message.visible = true
            }
              else {
              this.error_message.visible = true, this.execution_status.push(response),
                this.action.text = "Failed", this.action.active = false, this.action.progress = 100,
                this.action.complete = true, this.action.btn_state = true,
                this.action.content = "Workflow Failed. Kindly check the logs."
            }
          })
      },
    }
  }

</script>

<style>
  .container {
    margin: 0 auto;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    text-align: center;
  }

  .title {
    font-family: 'Quicksand', 'Source Sans Pro', -apple-system, BlinkMacSystemFont,
      'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    display: block;
    font-weight: 300;
    font-size: 100px;
    color: #35495e;
    letter-spacing: 1px;
  }

  .subtitle {
    font-weight: 300;
    font-size: 32px;
    color: #526488;
    word-spacing: 5px;
    padding-bottom: 15px;
  }

  .links {
    padding-top: 15px;
  }

  .log {
    font-family: Menlo, Consolas, DejaVu Sans Mono, monospace;
    font-size: 12px;
  }
</style>
