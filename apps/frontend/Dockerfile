FROM node:20-alpine

WORKDIR /app

# Install deps first (cached)
COPY package.json ./
# Copy lockfile
COPY package-lock.json* ./

# Install deps using the lockfile you actually have
RUN corepack enable && \
    if [ -f pnpm-lock.yaml ]; then pnpm install --frozen-lockfile; \
    elif [ -f yarn.lock ]; then yarn install --frozen-lockfile; \
    elif [ -f package-lock.json ]; then npm ci; \
    else npm install; fi

# Copy the rest of the app
COPY . .

EXPOSE 3000

# Next dev must listen on 0.0.0.0 in containers
CMD ["sh", "-lc", "npm run dev -- -H 0.0.0.0 -p 3000"]
