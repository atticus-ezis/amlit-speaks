from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, engine
from typing import Literal
from contextlib import asynccontextmanager
from functions import (
    model_lookup,
    get_object_instance,
    check_if_audio_file_exists,
    generate_http_streaming_tts_chunks,
    upload_audio_to_storage_and_save,
)
import asyncio
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ DB connected")
    except Exception as e:
        print(f"❌ DB connection failed: {e}")
    yield


app = FastAPI(lifespan=lifespan)

ObjectType = Literal[tuple(model_lookup.keys())]


class TextToSpeechCall(BaseModel):
    object_id: int
    object_type: ObjectType
    contentHTML: str
    lang: str


@app.post("/api/v1/text-to-speech/")
async def text_to_speech(
    body: TextToSpeechCall,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    object_instance = get_object_instance(
        object_id=body.object_id, object_type=body.object_type, db=db
    )

    audio_url = check_if_audio_file_exists(
        object_instance=object_instance, lang=body.lang
    )
    if audio_url:
        return {"audio_url": audio_url}

    stream_queue = asyncio.Queue()
    save_queue = asyncio.Queue()

    async def add_chunks_to_queues():
        async for chunk in generate_http_streaming_tts_chunks(body.contentHTML):
            await stream_queue.put(chunk)
            await save_queue.put(chunk)
        # end stream
        await stream_queue.put(None)
        await save_queue.put(None)

    async def stream_chunks():
        while True:
            chunk = await stream_queue.get()
            if chunk is None:
                break
            yield chunk

    async def save_chunks():
        chunks = []
        while True:
            chunk = await save_queue.get()
            if chunk is None:
                break
            chunks.append(chunk)
        audio_bytes = b"".join(chunks)
        # try converting to webM
        await upload_audio_to_storage_and_save(
            audio_bytes=audio_bytes,
            object_type=body.object_type,
            object_id=body.object_id,
            lang=body.lang,
            object_instance=object_instance,
            db=db,
        )

    background_tasks.add_task(add_chunks_to_queues)
    background_tasks.add_task(save_chunks)

    return StreamingResponse(stream_chunks(), media_type="audio/webm")


@app.get("/api/v1/health-check/")
async def health_check():
    return {"status": "ok"}
