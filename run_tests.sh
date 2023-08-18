#!/bin/bash

MAX_RETRIES=20
RETRY_COUNT=0
SLEEP_DURATION=5
SERVER_DOCKER_COMPOSE_FILE="agentware_server/docker-compose.yaml"

# Start Docker services
docker-compose -f "${SERVER_DOCKER_COMPOSE_FILE}" up -d

# Wait for server to start
until $(curl --output /dev/null --silent --fail http://localhost:8741/ping) || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
  echo "Waiting for server to start..."
  sleep $SLEEP_DURATION
  ((RETRY_COUNT++))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "Server did not start within the maximum retry limit."
  exit 1
fi

# Run Python command
python3 run_tests.py

# Stop Docker services
docker-compose -f "${SERVER_DOCKER_COMPOSE_FILE}" down
