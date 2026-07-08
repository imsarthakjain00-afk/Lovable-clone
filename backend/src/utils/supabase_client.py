from supabase import create_client, Client
from src.utils.settings import settings
import uuid

def get_supabase_client() -> Client:
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_SERVICE_ROLE_KEY
    return create_client(url, key)


def save_message_to_project(
    project_id: int,
    role: str,
    message_text: str,
    generated_code: str | None = None,
) -> dict:
    supabase = get_supabase_client()
    
    # We will insert into a 'chat_messages' table in Supabase
    message_data = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "role": role,
        "message_text": message_text,
        "generated_code": generated_code,
    }
    
    response = supabase.table("chat_messages").insert(message_data).execute()
    return response.data[0]


def get_all_messages_in_project(project_id: int) -> list[dict]:
    supabase = get_supabase_client()
    
    response = (
        supabase.table("chat_messages")
        .select("*")
        .eq("project_id", project_id)
        .order("created_at")
        .execute()
    )
    
    return response.data


def delete_all_messages_in_project(project_id: int):
    supabase = get_supabase_client()
    
    supabase.table("chat_messages").delete().eq("project_id", project_id).execute()
