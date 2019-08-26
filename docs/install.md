<a name="install"></a>
## Installation

<a name="cloud"></a>
### GIN's Hosted Cloud

We are currently deploying the utility for our cloud environment. Please check back after some time.

<a name="local"></a>
### Local Environment (D-I-Y)

<br>

<a name="docker-compose"></a>
#### Docker Compose

You can simply run `the docker-compose` file included in the repositoy which is configured to run all the 3 services := GIN, Drone and gin-proc for you.

<a name="manual"></a>
#### Manual Set-Up

Use the following tutorial to st up all 3 containers separately.

**Prerequisites**

* [Docker](https://docs.docker.com/)
* [g-node/gin-web](https://hub.docker.com/r/gnode/gin-web) node running in a docker container. If you don't have this then folow steps until [#install-gin](#install-gin)

It's advisable to use all the **gin micro-services** inside docker containers and further connect all containers to interact with each other for increased fault tolerance.

<br>

**Steps**

<a name="create-network"></a>
**[1]** In order to allow all gin containers to interact with each other, create a **docker network** and connect all containers to this network.

`docker network create <docker-network-name>`

**[2]** If you already have a **gin** service container running, then attach it to the new network.

`docker network connect <docker-network-name> <gin-container-name>`

<a name="install-gin"></a>
**Or** if you do not have a **gin** service container running already, then start a new one with the following command.
To keep things easier, we'll attach a static IP `172.19.0.2` to this container so that we don't have to inspect the docker network for changes in IP later.

`docker run --name=gin --net <network-name> --ip 172.19.0.2 -p 10022:22 -p 3000:3000 -v /var/gogs:/data gnode/gin-web:rebased`

If you already had a gin container running, then run the following command to check and copy IP address of **gin** service container.

`docker network inspect <network-name>`

Copy the IP of your GIN container from `containers` section.

**[3]** Set-up GIN Service.

If you have already set-up a gin container previuosly, then create a custom configuration file ([check GOGS docs for custom config](https://gogs.io/docs/features/custom_template)) with the following details.

<a name="config"></a>
```
DOMAIN           = 172.19.0.2
HTTP_PORT        = 3000
ROOT_URL         = http://172.19.0.2:3000/
```

Keep everything else the same.

If you have set-up the gin service for the first time through this tutorial, then access `172.19.0.2:3000` in your browser. You will be treated with the configuration page.

Mention the same config details as [above](#config) and leave everything else the same.

Save the details. Register for a new account and login.

**[4]** Create your first repository on the gin service. Clone the repository anywhere on your machine.

**[5]** Create **drone** CI/CD service container.

```
docker run --volume=/var/run/docker.sock:/var/run/docker.sock --volume=/gin-proc/cache:/cache --env=DRONE_GIT_ALWAYS_AUTH=false  --env=DRONE_GOGS_SERVER=http://172.19.0.2:3000 --env=DRONE_RUNNER_CAPACITY=2 --env=DRONE_RUNNER_NETWORKS=gin --env=DRONE_SERVER_HOST=172.19.0.3 --env=DRONE_SERVER_PROTO=http --env=DRONE_TLS_AUTOCERT=false --publish=80:80 --publish=443:443 --publish=2224:22 --restart=always  --detach=true --net gin --name=drone drone/drone:latest
 ```

Access drone at `172.19.0.3:80` in your browser.

**[6]** Create **gin-proc** service.

```
docker run --net gin --name=gin-proc gnode/proc:<version>
```

**Additional Environment Variables**

`DEBUG=True` - Serves log messages from the lowest DEBUG level i.e. DEBUG, INFO, WARNING, ERROR, EXCEPTION.

`DEBUG=False` or simply, not assigning the var - Servers log messages from and above INFO level i.e. INFO, WARNING, ERROR, EXCEPTION.

`LOG_DIR=/path/to/your/log/dir` - Specific location to store your logs in. Otherwise, the logs are simply printed on your console in real time.
