import asyncio
import logging
from signal import SIGINT, SIGTERM

logger = logging.getLogger(__name__)


async def shutdown(signal, loop):
    logger.info(f"{signal.name} received. Going to shutdown...")
    for task in asyncio.all_tasks():
        if task is not asyncio.current_task():
            task.cancel()

    loop.stop()


def add_shutdown_handlers(loop):
    for signal in (SIGINT, SIGTERM):
        loop.add_signal_handler(signal, lambda: asyncio.create_task(shutdown(signal, loop)))
