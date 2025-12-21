# EHRBase Clinical Data Repository
FROM ehrbase/ehrbase:2.0.0

# Install netcat for database connectivity check
# The base image uses Alpine Linux, so we use apk
USER root
RUN apk add --no-cache netcat-openbsd

# Copy wait-for-db script that ensures PostgreSQL is ready before starting
COPY ehrbase/wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

# Switch back to non-root user if the base image uses one
USER ehrbase

EXPOSE 8080

# Use the wait script as entrypoint to ensure DB is ready before Flyway runs
ENTRYPOINT ["/wait-for-db.sh"]
