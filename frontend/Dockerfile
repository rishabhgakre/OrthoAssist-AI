# syntax=docker/dockerfile:1
#
# OrthoAssist AI — frontend image. Only needed if you're deploying the
# frontend via Docker/Kubernetes yourself; if you're using Vercel for the
# frontend (see the deployment guide), Vercel builds straight from the
# repo and this file is unused there.
#
# IMPORTANT: Vite bakes VITE_API_URL into the compiled JS at BUILD time,
# not read at container start — unlike a typical backend env var, you
# cannot change it by just restarting the container with a new -e flag.
# You must pass it as a --build-arg, and rebuild the image, whenever the
# backend URL changes:
#
#   docker build --build-arg VITE_API_URL=https://api.yourdomain.com \
#       -t orthoassist-frontend ./frontend

FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

ARG VITE_API_URL=""
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:80/ > /dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
