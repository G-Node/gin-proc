<template>
  <div class="container">
    <sui-grid>
      <sui-grid-column :width="8" textAlign="left">
        <p class="title">gin-proc</p>
        <p class="subtitle">Workflow automation for GIN</p>
      </sui-grid-column>
      <sui-grid-column :width="8" verticalAlign="middle">
        <sui-form equalWidth @submit="login" @submit.stop.prevent>
            <sui-form-field>
              <sui-input v-model="loginData.username" type="text" placeholder="GIN Username" icon="user" />
            </sui-form-field>
            <sui-form-field>
              <sui-input v-model="loginData.password" type="password"
                placeholder="GIN password" icon="key" />
            </sui-form-field>
          <sui-form-field>
            <sui-label style="font-family: Menlo, Consolas, DejaVu Sans Mono, monospace;">Use your GIN credentials only.
            </sui-label>
          </sui-form-field>
          <br>
          <sui-button type="submit" animated color="black" basic fluid size="small">
            <sui-button-content visible>Login</sui-button-content>
            <sui-button-content hidden>
              <sui-icon name="right arrow" />
            </sui-button-content>
          </sui-button>
        </sui-form>
      </sui-grid-column>
    </sui-grid>
</div></template>

<script>
  import axios from "axios"

  export default {
    layout: 'login',
    data() {
      return {
        loginData: {
          username: null,
          password: null,
        },
        valid: true
      }
    },
    methods: {
      login() {
        this.$auth.loginWith('local', {
          data: {
            username: this.loginData.username,
            password: this.loginData.password
          }
        })
      }
    }
  }

</script>

<style>
  .container {
    margin: 0 auto;
    min-height: 80vh;
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
    font-size: 80px;
    color: black;
    letter-spacing: 1px;
  }

  .subtitle {
    font-weight: 300;
    font-size: 30px;
    color: slategray;
    word-spacing: 5px;
    padding-bottom: 15px;
  }

  .links {
    padding-top: 15px;
  }

</style>
