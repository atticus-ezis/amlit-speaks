from pydantic import ValidationError
from config import get_settings
from models import ShortStory, Chapter, ChildrenStory
from database import Base
from sqlalchemy.orm import Session
import re
from bs4 import BeautifulSoup
from openai import OpenAI
from supabase_client import supabase_storage
import asyncio
from voice_generate import GenerateVoices
from sqlalchemy import text
# from enums import model_lookup


settings = get_settings()

openai_client = OpenAI(api_key=settings.openai_api_key)

model_lookup = {
    "short_story": ShortStory,
    "chapter": Chapter,
    "children_story": ChildrenStory,
}


def get_object_instance(object_id: int, object_type: str, db: Session):
    model = model_lookup[object_type]
    model_instance = db.query(model).filter(model.id == object_id).first()
    if not model_instance:
        if settings.use_supabase:
            try:
                db.execute(
                    text("SET LOCAL statement_timeout = 0")
                )  # disable timeout for this transaction
                db.add(model(id=object_id))
                db.commit()
                db.refresh(model_instance := db.get(model, object_id))
                return model_instance
            except Exception as e:
                db.rollback()
                raise e
        else:
            raise ValidationError(
                f"Model: {object_type} ID: {object_id} not found in prod database!"
            )
    return model_instance


def check_if_audio_file_exists(object_instance: Base, lang: str) -> str | None:
    column_name = f"audio_url_{lang}"
    audio_url = getattr(object_instance, column_name, None)
    return audio_url or None


def parse_html(html: str) -> str:
    """Parse the HTML and return the text."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n+", "\n", text)
    text = text.replace("\n", ". ")
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


async def generate_http_streaming_tts_chunks(contentHTML: str):
    clean_text = parse_html(contentHTML)
    generate_voices = GenerateVoices()
    async for chunk in generate_voices.elevenlabs_http_streaming(clean_text):
        yield chunk


async def upload_audio_to_storage_and_save(
    audio_bytes: bytes,
    object_type: str,
    object_id: int,
    object_instance: Base,
    lang: str,
    db: Session,
):
    column_name = f"audio_url_{lang}"
    url_path = f"{object_type}/{object_id}/{lang}.opus"
    if settings.use_supabase:
        # this op is blocking, this to_thread frees it
        url = await asyncio.to_thread(supabase_storage, url_path, audio_bytes)
    else:
        url = ""  # amazon s3 -- async operation no need for thread

    setattr(object_instance, column_name, url)
    db.commit()


# ------------- REFERENCE FOR OPENAI TTS -------------

# async def generate_tts_chunks(contentHTML: str):
#     clean_text = parse_html(contentHTML)
#     async with openai_client.audio.speech.with_streaming_response.create(
#         model="tts-1", voice="alloy", input=clean_text, response_format="webm"
#     ) as response:
#         async for chunk in response.iter_bytes(chunk_size=4096):
#             yield chunk
