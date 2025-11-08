#!/bin/bash

# This script serves as an entrypoint for a Redis container.
# It starts the Redis server, waits for it to be ready,
# pre-populates data, and then keeps the Redis server running.

# Redis connection details for redis-cli within this container
# These should always point to the Redis instance running in THIS container.
REDIS_CLI_HOST="127.0.0.1" # Always use localhost for redis-cli connecting to its own container
REDIS_CLI_PORT="6379"      # Default Redis port
REDIS_CLI_DB="${REDIS_DB:-0}" # Use env var, default to 0
# REDIS_CLI_PASSWORD="${REDIS_PASSWORD:-}" # Uncomment and set if Redis requires a password

# Path to the file containing Redis commands, now passed via environment variable
REDIS_COMMANDS_FILE="${REDIS_COMMANDS_FILE_PATH}"

# Function to execute a Redis command
execute_redis_command() {
  local command_string="$1" # Renamed to command_string for clarity
  echo "Executing Redis command: $command_string"

  # Construct the base redis-cli command
  local redis_cli_base="redis-cli -h \"$REDIS_CLI_HOST\" -p \"$REDIS_CLI_PORT\" -n \"$REDIS_CLI_DB\""
  if [ -n "$REDIS_CLI_PASSWORD" ]; then
    redis_cli_base+=" -a \"$REDIS_CLI_PASSWORD\""
  fi

  # Use eval to correctly parse the command string into separate arguments for redis-cli
  # This is crucial for commands like SET "key" "value" where key and value are quoted.
  eval "$redis_cli_base" "$command_string"

  if [ $? -ne 0 ]; then
    echo "Error executing Redis command: $command_string"
    return 1 # Indicate failure
  fi
  return 0 # Indicate success
}

echo "Starting Redis server in background..."
# Start the main Redis server process in the background
# "$@" will expand to "redis-server" as defined in docker-compose.yml's command
"$@" &
REDIS_PID=$! # Store the PID of the background Redis server process

echo "Waiting for Redis server to be ready..."
# Wait for Redis to become available
MAX_RETRIES=10
RETRY_INTERVAL=2 # seconds
for i in $(seq 1 $MAX_RETRIES); do
  # Removed 'local' keyword for ping_command as it's not in a function.
  # Also, explicitly check the output of 'redis-cli ping' for "PONG".
  PING_OUTPUT=$(redis-cli -h "$REDIS_CLI_HOST" -p "$REDIS_CLI_PORT" -n "$REDIS_CLI_DB" ${REDIS_CLI_PASSWORD:+-a "$REDIS_CLI_PASSWORD"} ping 2>&1)
  
  if [[ "$PING_OUTPUT" == "PONG" ]]; then
    echo "Redis server is ready."
    break
  else
    echo "Redis not ready yet. Retrying in $RETRY_INTERVAL seconds... ($i/$MAX_RETRIES)"
    echo "  (Ping output: $PING_OUTPUT)" # Added for debugging
    sleep "$RETRY_INTERVAL"
  fi
  if [ "$i" -eq "$MAX_RETRIES" ]; then
    echo "Error: Redis server did not become ready within the timeout."
    kill "$REDIS_PID" # Kill the background Redis process
    exit 1
  fi
done

echo "Starting Redis data pre-population..."

# Check if the commands file path variable is set
if [ -z "$REDIS_COMMANDS_FILE" ]; then
  echo "Error: REDIS_COMMANDS_FILE_PATH environment variable is not set."
  kill "$REDIS_PID"
  exit 1
fi

# Check if the commands file exists
if [ ! -f "$REDIS_COMMANDS_FILE" ]; then
  echo "Error: Redis commands file not found at $REDIS_COMMANDS_FILE"
  kill "$REDIS_PID"
  exit 1
fi

# Read commands from the file and execute them
echo "Reading and executing commands from $REDIS_COMMANDS_FILE"
while IFS= read -r line || [[ -n "$line" ]]; do
  # Skip empty lines and comments
  if [[ -z "$line" || "$line" =~ ^# ]]; then
    continue
  fi
  execute_redis_command "$line"
done < "$REDIS_COMMANDS_FILE"

echo "Redis data pre-population complete. Keeping Redis server running."

# Wait for the background Redis server process to finish.
# This will keep the container alive as long as Redis is running.
wait "$REDIS_PID"
