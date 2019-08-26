# gin-proc Microservice for [GIN](https://gin.g-node.org)

<br>

[![G-Node](./images/favicon.png)](https://gin.g-node.org)

This repository contains documentation for using the **gin-proc** microservice for **[GIN](https://gin.g-node.org)** with INCF **as a part of Google Summer of Code (GSoC) 2019 programme**, as well as its setup and support scripts.

<br>

## Table of Contents
* **[Introduction](#introduction)**
  - [Problem statement](#problem)
  - [Rationale and Significance](#rationale)
* **[Installation](docs/install.md)**
  - [GIN's hosted cloud](docs/install.md#cloud)
  - [Local environment](docs/install.md#local)
    - [Docker Compose](docs/install.md#docker-compose)
    - [Manual](docs/install.md#manual)
* **[Usage](docs/usage.md)**
  - [Workflows](docs/usage.md#workflows)
  - [User's Files](docs/usage.md#files)
* **[Operations](docs/operations.md)**
  - [After Login](docs/operations.md#after-login)
  - [API](http://<GIN-PROC-SERVER>:8000/docs/api/)
  - [Inside Pipeline](docs/operations.md#pipeline)
* **[FAQ](docs/faq.md)**
* **[Authors & Contribution](#authors)**
* **[License](#license)**

<br>

<a name="introduction"></a>
## Introduction

**gin--proc** is a GIN micro-service which allows the users to design efficient workflows for their work - by automating Snakemake, and build the workflows with open-source version of Continuous Integration (CI) service [Drone](https://drone.io/).

<br>

<a name="problem"></a>
### Problem Statement

INCF is hosting a GIN service designed above GOGS with Git to serve as a repository management utility categorically for the Neuroinformatics data. The users (from non-tech backgrounds) find it tough to automate their workflows - precisely going from the input phase to the output phase. A lot of data makes writing workflows a repetitive and redundant task for them. Even if they are using tools like Snakemake. If they are past this stage, still testing all their workflows for potential errors and/or bugs for exorbitant amount of data and their workflows, consumes even more amount of time and reduces their efficiency.

<br>

<a name="rationale"></a>
### Rationale and Significance

This tool/micro-service is required since, given the GIN user base of neuroscientists and other pro-fessionals from the related fields, shouldn’t be involved in writing thousands of repeated workflows for their data, and then testing it manually. This tool will increase their efficiency by almost exponential levels by eradicating redundancy from their work.


<br>

<a name="authors"></a>
## Authors and Contributions

<table><tbody>
<tr><th align="left">Achilleas Koutsou</th><td><a href="https://github.com/achilleas-k">GitHub/achilleas-k</a></td><td></td></tr>
<tr><th align="left">Michael Sonntag</th><td><a href="https://github.com/mpsonntag">GitHub/mpsonntag</a></td><td></td></tr>
<tr><th align="left">Mrinal Wahal</th><td><a href="https://gitlab.com/wahal">GitLab/wahal</a></td><td><a href="https://mrinalwahal.com/rvagg">MrinalWahal.com</a></td></tr>
</tbody></table>

Contributions are welcome from anyone wanting to improve this project!

Please file an issue if you are experiencing a problem or would like to discuss something related to the microservice.

Pull requests are encouraged if you have changes you believe would improve the setup process or increase compatibility across deployment environments.

<br>

<a name="license"></a>
## License

This microservice is licensed under the BSD 3-Clause license. All rights not explicitly granted in the MIT license are reserved. See the included [LICENSE.md](./LICENSE.md) file for more details.

------------------------------------------------------------------

*Supported with :heart: by [Achilleas Koutsou](https://github.com/achilleas-k), [Michael Sonntag](https://github.com/mpsonntag) and the [G-Node](https://github.com/orgs/G-Node/people) team.*

*This project was completed as part of *Google Summer of Code (GSoC) 2019.* and is affiliated with [G-Node](http://www.g-node.org/) and [GIN](https://gin.g-node.org).*

<br>

*Neither G-Node nor GIN owns the trademark for Drone.*
