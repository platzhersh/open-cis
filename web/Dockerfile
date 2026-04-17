FROM node:20-slim

# Enable corepack for pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

# Copy package files (paths relative to repo root since Railway uses repo root as build context)
COPY web/package.json web/pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source files
COPY web/ .

# Vite build-time env vars — Railway passes values from service variables into
# --build-arg. Vars must be re-exported via ENV so `pnpm run build` sees them.
ARG VITE_API_URL
ARG VITE_OIDC_ISSUER
ARG VITE_OIDC_CLIENT_ID
ARG VITE_APP_MODE
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_OIDC_ISSUER=${VITE_OIDC_ISSUER}
ENV VITE_OIDC_CLIENT_ID=${VITE_OIDC_CLIENT_ID}
ENV VITE_APP_MODE=${VITE_APP_MODE}

# Build the application
RUN pnpm run build

# Install serve globally using npm (pnpm global install has issues in Docker)
RUN npm install -g serve

# Change ownership to the built-in node user for security
RUN chown -R node:node /app

USER node

EXPOSE 3000

# Use Railway's $PORT if available, otherwise default to 3000
CMD sh -c "echo 'Starting serve on port ${PORT:-3000}...' && serve dist -s -l ${PORT:-3000}"
