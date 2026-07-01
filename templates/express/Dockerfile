FROM node:20-alpine

WORKDIR /app
ENV NODE_ENV=production

RUN addgroup -S nodejs && adduser -S appuser -G nodejs
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev
COPY src ./src

USER appuser
EXPOSE 3000
CMD ["node", "src/index.js"]