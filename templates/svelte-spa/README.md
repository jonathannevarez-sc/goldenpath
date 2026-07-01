# {{SERVICE_NAME}}

Svelte SPA (Vite + nginx) on the Shop Golden Path.

## Local

```bash
npm ci
npm run dev
```

## Deploy

Build runs in Docker. Push to `main` → deploys to `dev`. Health: `/health`.