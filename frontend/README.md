# CoCo-Chat Vue Frontend

Vue 3 + Vite SPA for the CoCo-Chat 서비스 that reads messages from the Django REST API (`/api/messages`)
and writes its production build straight into `../frontend_build`, which is already mounted by nginx
in `docker-compose.yml`.

## Getting started

```bash
cd ~/app/frontend
npm install
npm run dev
```

- The dev server proxies any `/api/*` request to `http://localhost:8000` by default. Override the
  target with `VITE_API_PROXY_TARGET=http://127.0.0.1:9000 npm run dev` if you need another host.
- Set `VITE_API_BASE_URL` to change the API base URL in production builds (default: `/api`).

## Build for nginx

```bash
npm run build
```

The compiled assets replace the contents of `~/app/frontend_build`, so nginx can immediately serve
the latest SPA without additional copy steps.

## Project layout

- `src/services/api.js`: tiny wrapper around `fetch` that handles API base URLs.
- `src/App.vue`: fetches health and message data, displays the cards, and exposes a manual refresh
  action.
- `src/style.css`: global styles that mirror the existing static page design from
  `frontend_build/index.html`.
