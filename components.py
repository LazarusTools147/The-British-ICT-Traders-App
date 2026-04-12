import streamlit as st
import pandas as pd
import base64
from datetime import datetime
# Note: Ensure database.py is present in your directory
from database import get_supabase

def image_to_base64(uploaded_file):
    """Encodes uploaded images to base64 for storage in Supabase text columns."""
    if uploaded_file is not None:
        return base64.b64encode(uploaded_file.read()).decode('utf-8')
    return None

def render_architect():
    st.header(f"🏗️ {st.session_state.user}'s MODEL_ARCHITECT")
    st.write("Define your institutional models and FVG requirements here.")
    supabase = get_supabase()
    
    # PRIVACY FILTER: Fetch only the models belonging to the logged-in user
    try:
        response = supabase.table("models").select("*").eq("trader_username", st.session_state.user).execute()
        existing_models = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching models: {e}")
        existing_models = pd.DataFrame()

    mode = st.radio("ARCHITECT MODE", ["CREATE NEW MODEL", "EDIT/REFINE EXISTING"], horizontal=True)
    m_name, m_logic, m_sess, current_img_b64 = "", "", [], None

    if mode == "EDIT/REFINE EXISTING" and not existing_models.empty:
        target = st.selectbox("SELECT MODEL TO REFINE", existing_models['name'].tolist())
        row = existing_models[existing_models['name'] == target].iloc[0]
        m_name, m_logic = row['name'], row['logic']
        m_sess = row['sessions'].split(",") if row['sessions'] else []
        current_img_b64 = row.get('screenshot_text')

    with st.form("model_form"):
        name_in = st.text_input("MODEL NAME (e.g., 2022 MENTORSHIP)", value=m_name).upper()
        sess_in = st.multiselect("VALID SESSIONS", ["ASIA", "LONDON", "NY AM", "NY PM"], default=m_sess)
        logic_in = st.text_area("CORE LOGIC & FVG REQUIREMENTS", value=m_logic, height=250)
        img_in = st.file_uploader("UPLOAD IDEAL SCHEMATIC (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
        
        if st.form_submit_button("SECURE STRATEGY TO PRIVATE CLOUD"):
            if name_in and logic_in:
                final_img = image_to_base64(img_in) if img_in else current_img_b64
                data = {
                    "trader_username": st.session_state.user,
                    "name": name_in,
                    "logic": logic_in,
                    "sessions": ",".join(sess_in),
                    "screenshot_text": final_img
                }
                try:
                    supabase.table("models").upsert(data).execute()
                    st.success(f"✔️ {name_in} SECURED FOR {st.session_state.user}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save model: {e}")
            else:
                st.error("Model Name and Logic are required.")

    if current_img_b64:
        st.divider()
        st.subheader("Current Model Schematic")
        st.image(f"data:image/png;base64,{current_img_b64}", use_container_width=True)

def render_forge():
    st.header(f"🔥 {st.session_state.user}'s FORGE: EXECUTION LOG")
    supabase = get_supabase()
    
    # PRIVACY FILTER: User can only select from their own models
    try:
        m_resp = supabase.table("models").select("name").eq("trader_username", st.session_state.user).execute()
        models = [r['name'] for r in m_resp.data]
    except:
        models = []
    
    if not models:
        st.warning("No Private Models Found. Build your first strategy in the Architect tab first."); return

    with st.form("forge_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            env = st.radio("ENVIRONMENT", ["LIVE", "BACKTEST/DEMO"], horizontal=True)
            mod = st.selectbox("MODEL", models)
            mvar = st.text_input("VARIATION (e.g. 5m FVG Inversion)").upper()
            mkt = st.text_input("MARKET (e.g. NQ, ES, GBPUSD)").upper()
            is_hindsight = st.checkbox("MARK AS HINDSIGHT / STUDY")
            news_impact = st.selectbox("NEWS IMPACT", ["NONE", "LOW", "MEDIUM", "HIGH", "NFP/CPI"])
        with c2:
            tm, tf = st.text_input("ENTRY TIME (EST)"), st.text_input("TF (e.g. 1m, 5m)").upper()
            sess = st.text_input("SESSION (e.g. NY AM)").upper()
            dur = st.number_input("DURATION (MINS)", 1, 1440, 15)
        with c3:
            sl = st.number_input("SL (HANDLES)", 0.1, 1000.0, 5.0)
            tp = st.number_input("TP (HANDLES)", 0.1, 5000.0, 15.0)
            res = st.selectbox("RESULT", ["WIN", "LOSS", "BE"])
            rsk = st.number_input("RISK %", 0.1, 100.0, 1.0)
            dt = st.date_input("DATE", datetime.now())
            
        nts = st.text_area("CONFLUENCE NOTES (Sloppy Market Checklist?)")
        img = st.file_uploader("ENTRY SCREENSHOT", type=['png', 'jpg', 'jpeg'])
        
        if st.form_submit_button("FIRE INTO PRIVATE VAULT"):
            img_b64 = image_to_base64(img)
            rr = tp / sl if sl > 0 else 0
            
            trade_data = {
                "trader_username": st.session_state.user,
                "model_name": mod, "model_var": mvar, "type": env, "market": mkt,
                "entry_time": tm, "entry_tf": tf, "session": sess, "result": res,
                "risk_pc": rsk, "rr": rr, "sl_handles": sl, "tp_handles": tp,
                "notes": nts, "date": str(dt), "duration_mins": dur, 
                "screenshot_text": img_b64, 
                "hindsight": is_hindsight,
                "news_impact": news_impact
            }
            
            try:
                # Execution Attempt
                supabase.table("trades").insert(trade_data).execute()
                st.success(f"🎯 TRADE SECURED FOR {st.session_state.user}")
                st.rerun()
            except Exception as e:
                # Detailed Error Mentor Guidance
                error_msg = str(e)
                if "column" in error_msg and "hindsight" in error_msg:
                    st.error("❌ DATABASE MISMATCH: You need to add a 'hindsight' column (boolean) to your Supabase 'trades' table.")
                elif "column" in error_msg and "news_impact" in error_msg:
                    st.error("❌ DATABASE MISMATCH: You need to add a 'news_impact' column (text) to your Supabase 'trades' table.")
                else:
                    st.error(f"DATABASE ERROR: {e}")

def render_compounder():
    st.header("📈 LIFESTYLE COMPOUNDER")
    st.write("Visualizing long-term wealth through disciplined R-multiple extraction.")
    c1, c2 = st.columns([1, 2])
    with c1:
        start = st.number_input("STARTING CAPITAL ($)", value=5000)
        ret = st.number_input("MONTHLY RETURN (%)", value=5.0)
        yrs = st.number_input("YEARS", value=5)
        dep = st.number_input("MONTHLY DEPOSIT ($)", value=100)
        inc = st.number_input("YEARLY DEPOSIT INCREASE (%)", value=10.0)
        wit = st.number_input("RECURRING WITHDRAWAL ($)", value=0)
        freq = st.selectbox("WITHDRAWAL FREQUENCY", ["WEEKLY", "MONTHLY", "QUARTERLY", "YEARLY"])

    freq_map = {"WEEKLY": 4, "MONTHLY": 1, "QUARTERLY": 3, "YEARLY": 12}
    bal, cur_dep, data = start, dep, []
    
    for m in range(1, int(yrs * 12) + 1):
        # Add return and monthly deposit
        bal = (bal * (1 + (ret / 100))) + cur_dep
        # Handle withdrawals
        if m % freq_map[freq] == 0:
            bal -= (wit * (4 if freq == "WEEKLY" else 1))
        # Handle yearly deposit increase
        if m % 12 == 0:
            cur_dep *= (1 + (inc / 100))
            data.append({"Year": m // 12, "Balance": round(max(0, bal), 2), "Monthly Deposit": round(cur_dep, 2)})
    
    with c2:
        df = pd.DataFrame(data)
        if not df.empty:
            st.line_chart(df.set_index("Year")["Balance"])
            st.table(df)