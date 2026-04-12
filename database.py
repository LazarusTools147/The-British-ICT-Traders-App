import streamlit as st
from supabase import create_client, Client

# --- 1. THE CONNECTION ---
# Using @st.cache_resource ensures the connection is persistent and fast
@st.cache_resource
def get_supabase():
    """
    Initializes and returns the authenticated Supabase client.
    Uses Streamlit secrets for security.
    """
    try:
        url: str = st.secrets["SUPABASE_URL"]
        key: str = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except KeyError:
        st.error("MISSING SECRETS: Please ensure SUPABASE_URL and SUPABASE_KEY are in your secrets.toml or Streamlit Cloud settings.")
        st.stop()
    except Exception as e:
        st.error(f"AUTHENTICATION ERROR: {e}")
        st.stop()

# Initialize the global client instance
supabase = get_supabase()

def init_db():
    """
    Institutional Health Check.
    Verifies the terminal can talk to the Cloud Vault.
    """
    try:
        # A simple ping to verify connectivity
        supabase.table("users").select("username").limit(1).execute()
    except Exception as e:
        st.error(f"🛰️ CLOUD CONNECTION FAILURE: {e}")
        st.info("Check your internet connection and Supabase project status.")

def execute_query(table_name, data, operation="insert"):
    """
    Standardized Helper for Cloud Operations.
    Reduces redundant code across the terminal.
    """
    try:
        if operation == "insert":
            return supabase.table(table_name).insert(data).execute()
        elif operation == "upsert":
            return supabase.table(table_name).upsert(data).execute()
        elif operation == "delete":
            # Added delete support to match the new Journal functionality
            return supabase.table(table_name).delete().execute()
    except Exception as e:
        st.error(f"⚖️ DATABASE TRANSACTION ERROR: {e}")
        return None