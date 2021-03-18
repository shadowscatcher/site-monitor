#!/usr/bin/env bash

# this is supposed to be in k8s init-container
function init_database() {
  ./main.py --mode=init --scripts=db/scripts
}

function wait_services() {
  ./wait-for-it.sh -t 20 postgres:5432
  ./wait-for-it.sh -t 20 kafka:9092
}

if [ "$KAFKA_BOOTSTRAP_SERVERS" == "kafka:9092" ]  # for local compose environment
then
   wait_services && init_database && ./main.py "$@"
else
    init_database && ./main.py "$@"
fi
