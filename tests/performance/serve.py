"""Test-only Uvicorn process with a file-triggered graceful shutdown."""

import asyncio
import os
from pathlib import Path

import uvicorn

assert os.environ.get("MARKETPLACE_ENVIRONMENT") == "test"
assert os.environ.get("MARKETPLACE_DB_NAME") == "marketplace_test"


async def main():
    server = uvicorn.Server(
        uvicorn.Config(
            "app.main:create_app",
            factory=True,
            host="127.0.0.1",
            port=int(os.environ["PERF_REPLICA_PORT"]),
            access_log=False,
        )
    )

    async def stop():
        while not Path(os.environ["PERF_STOP_FILE"]).exists():
            await asyncio.sleep(0.1)
        server.should_exit = True

    monitor = asyncio.create_task(stop())
    try:
        await server.serve()
    finally:
        monitor.cancel()


asyncio.run(main())
