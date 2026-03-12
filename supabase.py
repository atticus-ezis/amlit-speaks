from supabase import create_client
from config import get_settings

settings = get_settings()

supabase = create_client(
    settings.supabase_project_url, settings.supabase_service_role_key
)


def supabase_storage(path, bytes):
    supabase.storage.from_("audio").upload(path, bytes, {"content-type": "audio/webm"})
    return supabase.storage.from_("audio").get_public_url(path)
