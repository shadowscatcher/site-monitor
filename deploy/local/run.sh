#!/usr/bin/env bash
# script for running project localy in docker compose environment

docker-compose -f deploy/local/docker-compose.yaml --env-file deploy/local/.env up --build
