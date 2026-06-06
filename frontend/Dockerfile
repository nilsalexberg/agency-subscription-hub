FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN pnpm install
COPY frontend/ .
RUN pnpm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf