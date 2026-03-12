from pydantic import ValidationError
from config import get_settings
from models import ShortStory, Chapter, ChildrenStory
from database import Base
from sqlalchemy.orm import Session
import re
from bs4 import BeautifulSoup
from openai import OpenAI
from supabase import supabase_storage
import asyncio

settings = get_settings()

openai_client = OpenAI(api_key=settings.openai_api_key)

model_lookup = {
    "short_story": ShortStory,
    "chapter": Chapter,
    "children_story": ChildrenStory,
}


def get_model_instance(object_id: int, object_type: str, db: Session):
    model = model_lookup[object_type]
    return db.query(model).filter(model.id == object_id).first() or None


def audio_url_for_language(lang: str, instance: Base) -> str | None:
    """Return the audio URL for the given language from a model instance."""
    column_name = f"audio_url_{lang}"
    return getattr(instance, column_name, None)


def check_if_audio_file_exists(
    object_id: int, object_type: str, lang: str, db: Session
) -> str | None:
    model_instance = get_model_instance(object_id, object_type, db)
    if model_instance:
        audio_url = audio_url_for_language(lang, model_instance)
        return audio_url or None

    else:
        if settings.development_mode:
            model_type = model_lookup[object_type]
            db.add(model_type(id=object_id))
            db.commit()
            return None
        else:
            raise ValueError(
                f"In production DB: Model {object_type} with id {object_id} does not exist"
            )


def parse_html(html: str) -> str:
    """Parse the HTML and return the text."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n+", "\n", text)
    text = text.replace("\n", ". ")
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


async def generate_tts_chunks(contentHTML: str):
    clean_text = parse_html(contentHTML)
    async with openai_client.audio.speech.with_streaming_response.create(
        model="tts-1", voice="alloy", input=clean_text, response_format="webm"
    ) as response:
        async for chunk in response.iter_bytes(chunk_size=4096):
            yield chunk


async def upload_audio_to_storage_and_save(
    audio_bytes: bytes, object_id: int, object_type: str, lang: str, db: Session
):
    storage_path = f"{object_type}/{object_id}/{lang}.webm"
    if settings.development_mode:
        # this op is blocking, this threads frees it
        url = await asyncio.to_thread(supabase_storage, storage_path, audio_bytes)
    else:
        url = ""  # amazon s3 -- async operation
    model_instance = get_model_instance(object_id, object_type, db)
    if model_instance is None:
        raise ValueError("Can't find model to save audiofile")

    column_name = f"audio_url_{lang}"
    if not hasattr(model_instance, column_name):
        raise ValidationError(f"Model has no attribute '{column_name}'")

    setattr(model_instance, column_name, url)
    db.commit()
