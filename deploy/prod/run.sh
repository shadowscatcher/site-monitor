#!/usr/bin/env bash
docker-compose -f deploy/prod/docker-compose.yaml --env-file deploy/prod/.env up --build
#docker-compose -f deploy/prod/docker-compose.yaml --env-file deploy/prod/.env rm -v --force