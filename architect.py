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
    st.markdown('<h2 style="color: #FF4B4B;">📐 COMMAND CENTER</h2>', unsafe_allow_html=True)
    supabase = get_supabase()

    # --- 1. MARKET ARCHITECT (NEW SECTION) ---
    with st.expander("🌐 MARKET ARCHITECT", expanded=True):
        st.write("Define your markets and volatility profiles to enable smart analytics.")
        with st.form("new_market_form", clear_on_submit=True):
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                m_name = st.text_input("MARKET NAME (e.g. NQ, ES, OIL)").upper().strip()
            with mc2:
                m_profile = st.selectbox("VOLATILITY PROFILE", ["High (NQ/DAX)", "Mid (ES/Gold)", "Low/Decimal (Oil/FX)"])
            with mc3:
                # Default bucket suggestions based on profile
                default_buckets = {"High (NQ/DAX)": 10.0, "Mid (ES/Gold)": 2.5, "Low/Decimal (Oil/FX)": 0.5}
                m_bucket = st.number_input("BUCKET SIZE (HANDLES)", value=default_buckets[m_profile], step=0.1)

            if st.form_submit_button("REGISTER MARKET"):
                if m_name:
                    m_data = {
                        "trader_username": st.session_state.user,
                        "market_name": m_name,
                        "volatility_profile": m_profile,
                        "bucket_size": m_bucket
                    }
                    try:
                        supabase.table("markets").insert(m_data).execute()
                        st.success(f"✔️ {m_name} REGISTERED")
                        st.rerun()
                    except Exception as e:
                        st.error(f"DB Error: {e}")
                else:
                    st.warning("Market name required.")

        # Show registered markets
        try:
            m_res = supabase.table("markets").select("*").eq("trader_username", st.session_state.user).execute()
            if m_res.data:
                st.write("**Registered Markets:**")
                m_df = pd.DataFrame(m_res.data)
                for _, m_row in m_df.iterrows():
                    m_col1, m_col2 = st.columns([4, 1])
                    m_col1.caption(f"**{m_row['market_name']}** | Profile: {m_row['volatility_profile']} | Buckets: {m_row['bucket_size']}H")
                    if m_col2.button("🗑️", key=f"del_m_{m_row['id']}"):
                        supabase.table("markets").delete().eq("id", m_row['id']).execute()
                        st.rerun()
        except: pass

    st.divider()

    # --- 2. MODEL ARCHITECT ---
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

    # --- 3. MODEL REPOSITORY ---
    st.write("### 📚 MODEL REPOSITORY")
    
    try:
        res = supabase.table("models").select("*").eq("trader_username", st.session_state.user).order("created_at", desc=True).execute()
        models_df = pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Error fetching models: {e}")
        models_df = pd.DataFrame()

    if models_df.empty:
        st.info("No models architected yet.")
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
                    st.warning("Model purged.")
                    st.rerun()