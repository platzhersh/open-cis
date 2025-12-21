#!/bin/bash
# Wait for PostgreSQL to be ready before starting EHRbase

set -e

# Extract host and port from DB_URL
# DB_URL format: jdbc:postgresql://host:port/database
if [[ -z "$DB_URL" ]]; then
    echo "ERROR: DB_URL environment variable is not set"
    exit 1
fi

# Parse the JDBC URL to extract host and port
# Example: jdbc:postgresql://ehrbase-db.railway.internal:5432/ehrbase
DB_HOST=$(echo "$DB_URL" | sed -n 's|.*://\([^:/]*\).*|\1|p')
DB_PORT=$(echo "$DB_URL" | sed -n 's|.*://[^:]*:\([0-9]*\).*|\1|p')

# Default port if not specified
DB_PORT=${DB_PORT:-5432}

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

# Maximum wait time in seconds (5 minutes)
MAX_WAIT=300
WAIT_INTERVAL=5
ELAPSED=0

# Wait for the database to be ready
while [ $ELAPSED -lt $MAX_WAIT ]; do
    # Try to connect to PostgreSQL using bash's built-in TCP support
    if timeout 5 bash -c "cat < /dev/null > /dev/tcp/$DB_HOST/$DB_PORT" 2>/dev/null; then
        echo "PostgreSQL is available at $DB_HOST:$DB_PORT"
        break
    fi

    echo "PostgreSQL is not ready yet (waited ${ELAPSED}s)... retrying in ${WAIT_INTERVAL}s"
    sleep $WAIT_INTERVAL
    ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "ERROR: PostgreSQL did not become available within ${MAX_WAIT}s"
    exit 1
fi

# Additional wait to ensure PostgreSQL is fully initialized
echo "Waiting additional 10 seconds for PostgreSQL to fully initialize..."
sleep 10

echo "Starting EHRbase..."

# Execute the original entrypoint/command
exec java -jar /ehrbase.jar
