from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from typing import Literal
from functions import (
    model_lookup,
    check_if_audio_file_exists,
    generate_tts_chunks,
    upload_audio_to_storage_and_save,
)
import asyncio
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse

app = FastAPI()

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
    audio_url = check_if_audio_file_exists(
        body.object_id, body.object_type, body.lang, db
    )
    if audio_url:
        return {"audio_url": audio_url}

    stream_queue = asyncio.Queue()
    save_queue = asyncio.Queue()

    async def add_chunks_to_queues():
        async for chunk in generate_tts_chunks(body.contentHTML):
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
        # stream completed
        audio_bytes = b"".join(chunks)
        await upload_audio_to_storage_and_save(
            audio_bytes=audio_bytes,
            object_id=body.object_id,
            object_type=body.object_type,
            lang=body.lang,
            db=db,
        )

    background_tasks.add_task(add_chunks_to_queues)
    background_tasks.add_task(save_chunks)

    return StreamingResponse(stream_chunks(), media_type="audio/webm")


@app.get("/api/v1/health-check/")
async def health_check():
    return {"status": "ok"}
