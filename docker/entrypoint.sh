#!/usr/bin/env bash

set -eu

mkdir -p ${HOME}/.ssh
ssh-keyscan -H ${GIN_SSH_SERVER} > ${HOME}/.ssh/known_hosts

git config --global user.name "GIN Proc"
git config --global user.email "proc@g-node.org"

cd /app/backend
python3 -u server.py &
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
trap stopservices SIGKILL

wait ${bpid} ${fpid}
echo "Done"
