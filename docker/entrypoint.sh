#!/usr/bin/env bash

set -eu

mkdir -p ${HOME}/.ssh
ssh-keyscan $GIN_SSH_SERVER > ${HOME}/.ssh/known_hosts

git config --global user.name "gin-proc"
git config --global user.email "proc@g-node.org"

cd /app/backend
python3 server.py &
bpid=$!

cd /app/frontend
DEBUG=1 npm start &
fpid=$!

stopservices() {
    echo "Stopping services"
    kill ${bpid}
    kill ${fpid}
}

trap stopservices SIGINT

wait ${bpid} ${fpid}
echo "Done"
