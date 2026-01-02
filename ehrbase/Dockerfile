# EHRBase Clinical Data Repository
FROM ehrbase/ehrbase:2.0.0

# Install netcat and bind-tools for database connectivity check
# The base image uses Alpine Linux, so we use apk
USER root
RUN apk add --no-cache netcat-openbsd bind-tools

# Copy wait-for-db script that ensures PostgreSQL is ready before starting
COPY ehrbase/wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

# Switch back to non-root user if the base image uses one
USER ehrbase

EXPOSE 8080

# Use CMD instead of ENTRYPOINT to preserve the base image's entrypoint
# The wait script will run first, then exec into the EHRbase JAR
CMD ["/wait-for-db.sh"]
