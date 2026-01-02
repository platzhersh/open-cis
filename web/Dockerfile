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

# Build the application
RUN pnpm run build

# Install serve globally using npm (pnpm global install has issues in Docker)
RUN npm install -g serve

EXPOSE 3000

# Use Railway's $PORT if available, otherwise default to 3000
CMD sh -c "echo 'Starting serve on port ${PORT:-3000}...' && serve dist -s -l ${PORT:-3000}"
