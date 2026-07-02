# syntax=docker/dockerfile:1
# ===========================================================================
# Frontend image: build the Vite/Vue 3 SPA, then serve it with nginx.
# nginx also reverse-proxies /api, /admin, /static, /media, /ws to the backend,
# so the whole app lives behind a single domain (no CORS).
# Build context: ./frontend
# ===========================================================================

# --- Build stage (Debian, not Alpine: avoids esbuild/rollup musl native-binary issues) ---
FROM node:20-slim AS build
WORKDIR /app

# Install dependencies (cached unless the lockfile changes).
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# Build. VITE_API_URL is relative by default so the SPA calls the same origin,
# which nginx proxies to the backend. Override at build time for split domains.
ARG VITE_API_URL=/api/v1
ARG VITE_APP_BASE_NAME=/
COPY . .
RUN printf "VITE_API_URL=%s\nVITE_APP_BASE_NAME=%s\n" "$VITE_API_URL" "$VITE_APP_BASE_NAME" > .env.production \
    && npm run build

# --- Runtime stage ---
FROM nginx:1.27-alpine AS runtime
RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/app.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
# Use 127.0.0.1 (not localhost): inside the container localhost resolves to IPv6
# ::1, but nginx listens on IPv4 only.
HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
    CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
