#!/usr/bin/env bash

# this is supposed to be in k8s init-container
function init_database() {
  ./main.py --mode=init --scripts=db/scripts
}

function wait_services() {
  set -eou pipefail
  ./wait-for-it.sh -t 20 postgres_test:5432
  ./wait-for-it.sh -t 20 kafka_test:9092
}

if [ "$KAFKA_BOOTSTRAP_SERVERS" == "kafka_test:9092" ]
then
  wait_services
fi

init_database && pytest tests "$@"
