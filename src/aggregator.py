import asyncio
import logging
from dataclasses import dataclass
from src.dedup_store import DeduplicationStore
import time

@dataclass
class StatsResponse:
    received: int
    unique_processed: int
    duplicate_dropped: int
    topics: dict
    uptime: float

class EventAggregator:
    def __init__(self, dedup_store: DeduplicationStore):
        self.dedup_store = dedup_store
        self.stats = {"received": 0, "unique_processed": 0, "duplicate_dropped": 0}
        self.start_time = time.time()
        self.queue = asyncio.Queue()
        self._worker_task = None

    async def start(self):
        self.dedup_store.connect()
        self._worker_task = asyncio.create_task(self._worker())
        logging.info("Aggregator Worker started")

    async def stop(self):
        if self._worker_task:
            self._worker_task.cancel()
        await self.dedup_store.close()


    async def _worker(self):
        while True:
            event = await self.queue.get()
            try:
                is_new = self.dedup_store.try_insert_event(
                    event.topic, event.event_id, event.timestamp, event.payload
                )
                if is_new:
                    self.stats["unique_processed"] += 1
                else:
                    self.stats["duplicate_dropped"] += 1
            except Exception as e:
                logging.error(f"Worker Error: {e}")
            finally:
                self.queue.task_done()

    async def publish(self, events):
        for e in events:
            self.stats["received"] += 1
            await self.queue.put(e)

    async def get_stats(self):
        store_stats = await self.dedup_store.get_stats()
        uptime = time.time() - self.start_time

        return StatsResponse(
            received=self.stats["received"],
            unique_processed=self.stats["unique_processed"],
            duplicate_dropped=self.stats["duplicate_dropped"],
            topics=store_stats.get("topics", {}),
            uptime=uptime,
        )
    
    async def get_events(self, topic: str | None = None):
        return self.dedup_store.get_events(topic)



