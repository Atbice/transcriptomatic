# Build stage
FROM docker.io/node:18-slim

ENV DEBIAN_FRONTEND=noninteractive

# Work around user namespace issues with apt
RUN echo 'APT::Sandbox::User "root";' > /etc/apt/apt.conf.d/90sandbox && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy all frontend files and build
COPY . .
RUN npm run build

# Production stage
FROM docker.io/nginx:alpine

# Copy built files from build stage to nginx serve directory
COPY --from=0 /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]