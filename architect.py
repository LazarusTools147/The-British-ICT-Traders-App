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

    # --- 1. MARKET ARCHITECT (CORE CONFIG) ---
    st.write("### 🌐 MARKET ARCHITECT")
    st.info("Register your markets here to enable smart bucketing and dropdowns in the Forge.")
    
    with st.form("new_market_form", clear_on_submit=True):
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            m_name = st.text_input("MARKET NAME (e.g. NQ, ES, OIL)").upper().strip()
        with mc2:
            m_profile = st.selectbox("VOLATILITY PROFILE", ["High (NQ/DAX)", "Mid (ES/Gold)", "Low/Decimal (Oil/FX)"])
        with mc3:
            # Suggestions for bucket sizes
            default_buckets = {"High (NQ/DAX)": 10.0, "Mid (ES/Gold)": 2.5, "Low/Decimal (Oil/FX)": 0.5}
            # We use a key to ensure it reacts to the selectbox if needed, 
            # though number_input value is static on first render
            m_bucket = st.number_input("BUCKET SIZE (HANDLES)", value=2.5, step=0.1, help="NQ=10, ES=2.5, Oil=0.5")

        if st.form_submit_button("💾 REGISTER NEW MARKET"):
            if m_name:
                # Profile to Bucket mapping override logic
                final_bucket = m_bucket
                m_data = {
                    "trader_username": st.session_state.user,
                    "market_name": m_name,
                    "volatility_profile": m_profile,
                    "bucket_size": final_bucket
                }
                try:
                    supabase.table("markets").insert(m_data).execute()
                    st.success(f"✔️ {m_name} REGISTERED SUCCESSFULLY")
                    st.rerun()
                except Exception as e:
                    st.error(f"DB Error: {e}")
            else:
                st.warning("Market name is mandatory.")

    # Display Current Markets
    try:
        m_res = supabase.table("markets").select("*").eq("trader_username", st.session_state.user).execute()
        if m_res.data:
            with st.expander("📊 REGISTERED MARKET REGISTRY", expanded=False):
                m_df = pd.DataFrame(m_res.data)
                for _, m_row in m_df.iterrows():
                    mk1, mk2 = st.columns([5, 1])
                    mk1.write(f"**{m_row['market_name']}** | {m_row['volatility_profile']} | Bucket: {m_row['bucket_size']}H")
                    if mk2.button("🗑️", key=f"rm_mkt_{m_row['id']}"):
                        supabase.table("markets").delete().eq("id", m_row['id']).execute()
                        st.rerun()
    except:
        pass

    st.divider()

    # --- 2. MODEL ARCHITECT ---
    st.write("### ✨ MODEL ARCHITECT")
    with st.expander("🏗️ DESIGN NEW MODEL", expanded=False):
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