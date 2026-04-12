import streamlit as st
import pandas as pd
import base64
from datetime import datetime
from database import get_supabase

def image_to_base64(uploaded_file):
    if uploaded_file is not None:
        return base64.b64encode(uploaded_file.read()).decode('utf-8')
    return None

def render_architect():
    st.header(f"🏗️ {st.session_state.user}'s MODEL_ARCHITECT")
    supabase = get_supabase()
    
    # INTEGRATED CHANGE: Filter models so user only sees their own
    response = supabase.table("models").select("*").eq("trader_username", st.session_state.user).execute()
    existing_models = pd.DataFrame(response.data)

    mode = st.radio("ARCHITECT MODE", ["CREATE NEW MODEL", "EDIT EXISTING"], horizontal=True)
    m_name, m_logic, m_sess, current_img_b64 = "", "", [], None

    if mode == "EDIT EXISTING" and not existing_models.empty:
        target = st.selectbox("SELECT MODEL TO REFINE", existing_models['name'].tolist())
        row = existing_models[existing_models['name'] == target].iloc[0]
        m_name, m_logic = row['name'], row['logic']
        m_sess = row['sessions'].split(",") if row['sessions'] else []
        current_img_b64 = row.get('screenshot_text')

    with st.form("model_form"):
        name_in = st.text_input("MODEL NAME", value=m_name).upper()
        sess_in = st.multiselect("VALID SESSIONS", ["ASIA", "LONDON", "NY AM", "NY PM"], default=m_sess)
        logic_in = st.text_area("CORE LOGIC & FVG REQUIREMENTS", value=m_logic, height=250)
        img_in = st.file_uploader("UPLOAD IDEAL SCHEMATIC", type=['png', 'jpg', 'jpeg'])
        
        if st.form_submit_button("SECURE STRATEGY TO CLOUD"):
            if name_in and logic_in:
                final_img = image_to_base64(img_in) if img_in else current_img_b64
                data = {
                    "trader_username": st.session_state.user, # INTEGRATED STAMP
                    "name": name_in,
                    "logic": logic_in,
                    "sessions": ",".join(sess_in),
                    "screenshot_text": final_img
                }
                supabase.table("models").upsert(data).execute()
                st.success(f"✔️ {name_in} UPDATED FOR {st.session_state.user}")
                st.rerun()

    if current_img_b64:
        st.image(f"data:image/png;base64,{current_img_b64}", caption="Current Model Schematic")

def render_forge():
    st.header(f"🔥 {st.session_state.user}'s FORGE")
    supabase = get_supabase()
    
    # INTEGRATED CHANGE: Filter dropdown so user only selects their own models
    m_resp = supabase.table("models").select("name").eq("trader_username", st.session_state.user).execute()
    models = [r['name'] for r in m_resp.data]
    
    if not models:
        st.warning("No Private Models Found. Build one in Architect first."); return

    with st.form("forge_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            env = st.radio("ENVIRONMENT", ["LIVE", "BACKTEST/DEMO"], horizontal=True)
            mod = st.selectbox("MODEL", models)
            mvar = st.text_input("VARIATION").upper()
            mkt = st.text_input("MARKET").upper()
        with c2:
            tm, tf = st.text_input("TIME"), st.text_input("TF").upper()
            sess = st.text_input("SESSION").upper()
            dur = st.number_input("DURATION (MINS)", 1, 1440, 15)
        with c3:
            sl = st.number_input("SL", 0.1, 1000.0, 5.0)
            tp = st.number_input("TP", 0.1, 5000.0, 15.0)
            res = st.selectbox("RESULT", ["WIN", "LOSS", "BE"])
            rsk = st.number_input("RISK %", 0.1, 100.0, 1.0)
            dt = st.date_input("DATE", datetime.now())
            
        nts = st.text_area("NOTES (Include Sloppy Market Checklist?)")
        img = st.file_uploader("ENTRY SCREENSHOT", type=['png', 'jpg', 'jpeg'])
        
        if st.form_submit_button("FIRE INTO VAULT"):
            img_b64 = image_to_base64(img)
            rr = tp / sl if sl > 0 else 0
            trade_data = {
                "trader_username": st.session_state.user, # INTEGRATED STAMP
                "model_name": mod, "model_var": mvar, "type": env, "market": mkt,
                "entry_time": tm, "entry_tf": tf, "session": sess, "result": res,
                "risk_pc": rsk, "rr": rr, "sl_handles": sl, "tp_handles": tp,
                "notes": nts, "date": str(dt), "duration_mins": dur, "screenshot_text": img_b64
            }
            supabase.table("trades").insert(trade_data).execute()
            st.success("🎯 TRADE SECURED")

def render_compounder():
    st.header("📈 LIFESTYLE COMPOUNDER")
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
        bal = (bal * (1 + (ret / 100))) + cur_dep
        if m % freq_map[freq] == 0:
            bal -= (wit * (4 if freq == "WEEKLY" else 1))
        if m % 12 == 0:
            cur_dep *= (1 + (inc / 100))
            data.append({"Year": m // 12, "Balance": round(max(0, bal), 2), "Monthly Deposit": round(cur_dep, 2)})
    
    with c2:
        df = pd.DataFrame(data)
        if not df.empty:
            st.line_chart(df.set_index("Year")["Balance"])
            st.table(df)