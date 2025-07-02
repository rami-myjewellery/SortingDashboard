import base64
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

from app.data.store import get_db
from app.models import Person

router = APIRouter()


class PubSubMessage(BaseModel):
    message: Dict[str, Any]
    subscription: str


@router.post("/pubsub/sorting-action")
async def handle_pubsub_push(pubsub_msg: PubSubMessage):
    try:
        # Decode base64 message data
        print('COPY THIS ',pubsub_msg)
        encoded_data = pubsub_msg.message.get("data", "")
        decoded_json = base64.b64decode(encoded_data).decode("utf-8")
        job_data = json.loads(decoded_json)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decode base64 payload: {e}")

    # Extract values
    job_id = job_data.get("ID")
    job_type = job_data.get("NAME", "").strip()
    profile = job_data.get("PROFILE", "").strip()
    target_server = job_data.get("TARGETSERVER", "")
    error_value = job_data.get("segment_6", 0) or job_data.get("segment_error", 0)

    # Access dashboard
    db = get_db()["default"]

    # Append to people as a rolling action log
    action = Person(
        name=f"{profile} → {job_type}",
        speed=100,
        idleSeconds=0
    )

    db.people.append(action)
    db.people = db.people[-5:]  # Keep last 5 only

    print(f"✅ Updated dashboard for job {job_id} / {job_type}")
    return {"status": "success", "job_id": job_id}
