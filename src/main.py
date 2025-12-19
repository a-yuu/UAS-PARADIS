from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

from src.model import Event
from src.aggregator import EventAggregator
from src.dedup_store import DeduplicationStore

app = FastAPI()

dedup = DeduplicationStore("/app/data/dedup.db")
aggregator = EventAggregator(dedup)

class PublishBody(BaseModel):
    events: List[Event]

@app.on_event("startup")
async def startup():
    await aggregator.start()

@app.on_event("shutdown")
async def shutdown():
    await aggregator.stop()

@app.post("/publish")
async def publish(body: PublishBody):
    return await aggregator.publish(body.events)

@app.get("/stats")
async def stats():
    return await aggregator.get_stats()

@app.get("/health")
async def health():
    return {"status": "ok"} 

@app.get("/events")
async def events():
    return await aggregator.get_events()
