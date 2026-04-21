import streamlit as st
import pandas as pd
import base64
from datetime import datetime
from database import get_supabase

def image_to_base64(uploaded_file):
    """Encodes uploaded images for cloud storage."""
    if uploaded_file is not None:
        return base64.b64encode(uploaded_file.read()).decode('utf-8')
    return None

def render_architect_tab():
    st.markdown('<h2 style="color: #FF4B4B;">📐 MODEL ARCHITECT</h2>', unsafe_allow_html=True)
    supabase = get_supabase()
    
    # 1. CREATE NEW MODEL SECTION
    with st.expander("✨ ARCHITECT NEW MODEL", expanded=False):
        with st.form("new_model_form", clear_on_submit=True):
            c1, c2 = st.columns([1, 1])
            with c1:
                new_name = st.text_input("MODEL NAME (e.g. SILVER BULLET)").upper()
                new_sess = st.multiselect("VALID SESSIONS", ["ASIA", "LONDON", "NY AM", "NY PM"])
            with c2:
                new_img = st.file_uploader("UPLOAD SCHEMATIC", type=['png', 'jpg', 'jpeg'])
                
            new_logic = st.text_area("CORE LOGIC & FVG REQUIREMENTS", height=150)
            
            if st.form_submit_button("SAVE TO ARCHITECTURE"):
                if new_name and new_logic:
                    img_b64 = image_to_base64(new_img) if new_img else None
                    data = {
                        "trader_username": st.session_state.user,
                        "name": new_name,
                        "logic": new_logic,
                        "sessions": ",".join(new_sess),
                        "screenshot_text": img_b64,
                        "created_at": str(datetime.now())
                    }
                    try:
                        supabase.table("models").insert(data).execute()
                        st.success(f"✔️ {new_name} ADDED TO REPOSITORY")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving model: {e}")
                else:
                    st.warning("Name and Logic are required.")

    st.divider()

    # 2. MODEL REPOSITORY (READ / UPDATE / DELETE)
    st.write("### 📚 MODEL REPOSITORY")
    
    try:
        # Fetch models ordered by newest first
        res = supabase.table("models").select("*").eq("trader_username", st.session_state.user).order("created_at", desc=True).execute()
        models_df = pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Error fetching models: {e}")
        models_df = pd.DataFrame()

    if models_df.empty:
        st.info("No models architected yet. Use the section above to create your first one.")
        return

    for _, row in models_df.iterrows():
        created_date = pd.to_datetime(row['created_at']).strftime('%d %b %Y')
        with st.expander(f"📁 {row['name']} | Created: {created_date}"):
            with st.form(f"edit_model_{row['id']}"):
                u_name = st.text_input("NAME", value=row['name']).upper()
                u_sess_list = row['sessions'].split(",") if row['sessions'] else []
                u_sess = st.multiselect("SESSIONS", ["ASIA", "LONDON", "NY AM", "NY PM"], default=u_sess_list)
                u_logic = st.text_area("LOGIC", value=row['logic'], height=200)
                
                if row.get('screenshot_text'):
                    st.image(f"data:image/png;base64,{row['screenshot_text']}", use_container_width=True)
                
                col_up, col_del = st.columns(2)
                if col_up.form_submit_button("💾 UPDATE ARCHITECTURE"):
                    up_data = {"name": u_name, "logic": u_logic, "sessions": ",".join(u_sess)}
                    supabase.table("models").update(up_data).eq("id", row['id']).execute()
                    st.success("Model updated.")
                    st.rerun()
                
                if col_del.form_submit_button("🗑️ DELETE MODEL"):
                    supabase.table("models").delete().eq("id", row['id']).execute()
                    st.warning("Model purged from repository.")
                    st.rerun()