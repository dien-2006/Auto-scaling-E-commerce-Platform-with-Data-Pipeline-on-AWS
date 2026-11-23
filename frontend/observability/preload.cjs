"use strict";

// Loaded by the production standalone Node entry point before Next creates its
// HTTP server. Worker threads do not open another metrics listener.
const { isMainThread } = require("node:worker_threads");
const { createRegistry, createMetricsServer, installObserver } = require("./http-metrics.cjs");
const key = Symbol.for("coco.frontend.http.metrics");

if (isMainThread && !globalThis[key]) {
  const port = Number(process.env.COCO_FRONTEND_METRICS_PORT || 9091);
  if (!Number.isInteger(port) || port < 1024 || port > 65535 || port === Number(process.env.PORT || 3000)) {
    console.error("Frontend metrics disabled: invalid internal metrics port");
  } else {
    const registry = createRegistry();
    const server = createMetricsServer(registry);
    installObserver(registry, server);
    globalThis[key] = { registry, server };
    server.on("error", () => console.error("Frontend internal metrics listener unavailable"));
    server.listen(port, "0.0.0.0");
    server.unref();
  }
}
