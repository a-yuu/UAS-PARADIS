from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, Any, Optional, List
from datetime import datetime


class Event(BaseModel):
    """Representasi satu event log yang dikirim ke aggregator."""

    # Contoh format JSON otomatis di dokumentasi API (FastAPI)
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic": "user.created",
                "event_id": "evt_123456",
                "timestamp": "2025-10-19T10:30:00Z",
                "source": "auth-service",
                "payload": {"user_id": 42, "email": "user@example.com"},
            }
        }
    )

    # Kolom utama event
    topic: str = Field(..., min_length=1, description="Nama topik atau kategori event")
    event_id: str = Field(..., min_length=1, description="ID unik untuk event ini")
    timestamp: str = Field(..., description="Waktu event dalam format ISO8601")
    source: str = Field(..., min_length=1, description="Sumber pembangkit event")
    payload: Dict[str, Any] = Field(
        default_factory=dict, description="Data tambahan dari event"
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        """
        Validasi format waktu agar sesuai ISO8601.
        Contoh: 2025-10-19T10:30:00Z → dikonversi ke zona UTC.
        """
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError:
            raise ValueError("timestamp harus dalam format ISO8601 yang valid")


class EventBatch(BaseModel):
    """Model untuk menerima beberapa event sekaligus dalam satu request."""
    events: List[Event]  # daftar event yang akan dikirim ke aggregator


class StatsResponse(BaseModel):
    """Struktur data untuk hasil endpoint /stats."""
    received: int = Field(description="Total event diterima sejak startup")
    unique_processed: int = Field(description="Jumlah event unik yang diproses")
    duplicate_dropped: int = Field(description="Jumlah event duplikat yang diabaikan")
    topics: Dict[str, int] = Field(description="Jumlah event per topik")
    uptime: float = Field(description="Durasi aktif layanan (detik)")