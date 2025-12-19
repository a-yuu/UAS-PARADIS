import asyncio
import httpx
import random
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventPublisher:
    """Client simulator untuk mengirim event ke aggregator via HTTP."""

    def __init__(self, aggregator_url: str):
        # contoh: http://aggregator:8080
        self.aggregator_url = aggregator_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def simulate_at_least_once(self, num_events: int = 5000, duplicate_rate: float = 0.2):
        logger.info(f"Mulai simulasi: {num_events} events, {duplicate_rate*100:.0f}% duplikat")

        topics = ["user.created", "order.placed", "payment.processed"]
        events = []

        # 1) Event unik
        for i in range(num_events):
            events.append({
                "topic": random.choice(topics),
                "event_id": f"evt_{i:06d}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": "publisher-simulator",
                "payload": {"index": i, "data": f"Event {i}"},
            })

        # 2) Duplikat (at-least-once)
        num_duplicates = int(num_events * duplicate_rate)
        duplicate_events = random.choices(events, k=num_duplicates)
        all_events = events + duplicate_events
        random.shuffle(all_events)

        logger.info(f"Total event dikirim: {len(all_events)} (unik: {num_events})")

        # 3) Kirim batch
        batch_size = 50
        success_count = 0

        for i in range(0, len(all_events), batch_size):
            batch = all_events[i:i + batch_size]
            try:
                resp = await self.client.post(
                    f"{self.aggregator_url}/publish",
                    json={"events": batch},
                )
                resp.raise_for_status()
                success_count += len(batch)

                # progress tiap 10 batch
                if (i // batch_size) % 10 == 0:
                    logger.info(f"Progress: {success_count}/{len(all_events)}")
            except Exception as e:
                logger.error(f"Batch gagal dikirim: {e}")

            await asyncio.sleep(0.01)

        logger.info(f"Simulasi selesai: {success_count}/{len(all_events)} event terkirim")

        # 4) Ambil stats
        try:
            resp = await self.client.get(f"{self.aggregator_url}/stats")
            resp.raise_for_status()
            logger.info(f"Statistik akhir dari aggregator: {resp.json()}")
        except Exception as e:
            logger.error(f"Gagal mengambil statistik: {e}")

    async def close(self):
        await self.client.aclose()


async def wait_until_ready(client: httpx.AsyncClient, base_url: str, retries: int = 30):
    """
    Tunggu sampai aggregator siap.
    Pakai /stats (bukan /health) karena endpoint ini sudah ada di sistemmu.
    """
    base_url = base_url.rstrip("/")
    for attempt in range(1, retries + 1):
        try:
            r = await client.get(f"{base_url}/stats")
            if r.status_code == 200:
                return True
        except Exception:
            pass
        logger.info(f"Menunggu aggregator siap... ({attempt}/{retries})")
        await asyncio.sleep(1)
    return False


async def main():
    # ENV yang kamu pakai di docker-compose sebaiknya AGGREGATOR_URL=http://aggregator:8080
    aggregator_url = os.getenv("AGGREGATOR_URL", "http://aggregator:8080")
    num_events = int(os.getenv("NUM_EVENTS", "6000"))
    duplicate_rate = float(os.getenv("DUPLICATE_RATE", "0.2"))

    publisher = EventPublisher(aggregator_url)

    ready = await wait_until_ready(publisher.client, aggregator_url, retries=30)
    if not ready:
        logger.error("Aggregator tidak siap setelah ditunggu. Stop publisher (biar tidak misleading).")
        await publisher.close()
        return

    logger.info("Aggregator siap menerima event!")
    await publisher.simulate_at_least_once(num_events, duplicate_rate)
    await publisher.close()


if __name__ == "__main__":
    asyncio.run(main())
