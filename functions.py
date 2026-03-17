from pydantic import ValidationError
from config import get_settings
from models import ShortStory, Chapter, ChildrenStory
from database import Base
from sqlalchemy.orm import Session
import re
from bs4 import BeautifulSoup
from openai import OpenAI
import asyncio
from voice_generate import GenerateVoices
from sqlalchemy import text
from supabase import create_client
from enums import stream_media_type


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


# remove /n and replace with .
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
):
    print("running save and upload")
    from database import SessionLocal

    column_name = f"audio_url_{lang}"
    url_path = f"{object_type}/{object_id}/{lang}.opus"
    if settings.use_supabase:
        # this op is blocking, this to_thread frees it
        url = await asyncio.to_thread(supabase_storage, url_path, audio_bytes)
        # url = "https://irsgiycezqtbsiialijx.supabase.co/storage/v1/object/public/amlit-audio/chapter/1/en.opus"
    else:
        url = ""  # amazon s3 -- async operation no need for thread

    print("url path: ", url_path)
    session = SessionLocal()
    try:
        model = model_lookup[object_type]
        object_instance = session.get(model, object_id)
        print("object instance: ", object_instance)
        if object_instance:
            setattr(object_instance, column_name, url)
            session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def supabase_storage(url_path: str, audio_bytes: bytes) -> str:
    supabase = create_client(
        settings.supabase_project_url, settings.supabase_service_role_key
    )
    # this is failing
    supabase.storage.from_("amlit-audio").upload(
        url_path, audio_bytes, {"content-type": stream_media_type}
    )
    return supabase.storage.from_("amlit-audio").get_public_url(url_path)


def convert_to_opus(audio_bytes: bytes) -> bytes:
    """
    Convert audio bytes to Opus format using ffmpeg.
    Input can be various formats (Ogg, WebM, WAV, MP3, etc.); ffmpeg auto-detects.
    """
    import os
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.mp3")
        output_path = os.path.join(temp_dir, "output.opus")

        with open(input_path, "wb") as f:
            f.write(audio_bytes)

        subprocess.run(
            [
                "ffmpeg",
                "-y",  # overwrite output
                "-i",
                input_path,
                "-c:a",
                "libopus",
                "-b:a",
                "128k",
                "-f",
                "opus",
                output_path,
            ],
            check=True,
            capture_output=True,
        )

        with open(output_path, "rb") as f:
            return f.read()


# ------------- REFERENCE FOR OPENAI TTS -------------

# async def generate_tts_chunks(contentHTML: str):
#     clean_text = parse_html(contentHTML)
#     async with openai_client.audio.speech.with_streaming_response.create(
#         model="tts-1", voice="alloy", input=clean_text, response_format="webm"
#     ) as response:
#         async for chunk in response.iter_bytes(chunk_size=4096):
#             yield chunk
