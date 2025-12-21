# EHRBase Clinical Data Repository
FROM ehrbase/ehrbase:2.0.0

# Copy wait-for-db script that ensures PostgreSQL is ready before starting
COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

EXPOSE 8080

# Use the wait script as entrypoint to ensure DB is ready before Flyway runs
ENTRYPOINT ["/wait-for-db.sh"]
