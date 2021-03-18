#!/usr/bin/env bash
# script for running tests localy in docker compose environment
docker-compose -f deploy/test/docker-compose.yaml --env-file deploy/test/.env up --build --abort-on-container-exit --exit-code-from tests
test_exit_code=$?
docker-compose -f deploy/test/docker-compose.yaml --env-file deploy/test/.env down --volumes
docker-compose -f deploy/test/docker-compose.yaml --env-file deploy/test/.env rm -v --force
exit $test_exit_code
