// Production static server for the brain UI.
// Serves the built Astro site from ./dist on $PORT
// (Railway provides this). Uses serve-handler — a tiny dep installed
// in the runtime stage of the Dockerfile.

import http from "node:http"
import handler from "serve-handler"

const port = Number.parseInt(process.env.PORT ?? "8080", 10)
const host = process.env.HOST ?? "0.0.0.0"

const server = http.createServer((req, res) =>
  handler(req, res, {
    public: "dist",
    cleanUrls: true,
    // serve-handler auto-serves /404.html on misses — Astro emits one.
  }),
)

server.listen(port, host, () => {
  console.log(`brain ui listening on http://${host}:${port}`)
})
