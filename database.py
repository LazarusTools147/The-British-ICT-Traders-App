import streamlit as st
from supabase import create_client, Client

# --- 1. THE CONNECTION ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]

# Initialize the Supabase Client
supabase: Client = create_client(url, key)

def get_supabase():
    """Returns the authenticated Supabase client."""
    return supabase

def init_db():
    """Health check for cloud connection."""
    try:
        supabase.table("models").select("name").limit(1).execute()
    except Exception as e:
        st.error(f"SUPABASE CONNECTION ERROR: {e}")

def execute_query(table_name, data, operation="insert"):
    """Helper for cloud operations."""
    try:
        if operation == "insert":
            return supabase.table(table_name).insert(data).execute()
        elif operation == "upsert":
            return supabase.table(table_name).upsert(data).execute()
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None