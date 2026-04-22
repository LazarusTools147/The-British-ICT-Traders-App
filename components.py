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

def render_forge():
    st.markdown('<h2 style="color: #FF4B4B;">🔥 THE FORGE</h2>', unsafe_allow_html=True)
    supabase = get_supabase()
    
    # Sync available models for the dropdown
    try:
        m_resp = supabase.table("models").select("name").eq("trader_username", st.session_state.user).execute()
        models = [r['name'] for r in m_resp.data]
    except:
        models = []
    
    if not models:
        st.warning("No models found. Build a model in the Architect tab first."); return

    with st.form("forge_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            env = st.radio("ENVIRONMENT", ["LIVE", "BACKTEST/DEMO"], horizontal=True)
            mod = st.selectbox("MODEL", models)
            mvar = st.text_input("VARIATION (e.g. ODA, MACRO)").upper()
            mkt = st.text_input("MARKET (e.g. NQ, ES)").upper()
            is_hindsight = st.checkbox("MARK AS HINDSIGHT / STUDY")
            news = st.selectbox("NEWS IMPACT", ["NONE", "LOW", "MEDIUM", "HIGH", "NFP/CPI"])
        
        with c2:
            etype = st.text_input("ENTRY TYPE (e.g. SILVER BULLET, MSS)").upper()
            tm = st.text_input("ENTRY TIME (EST)")
            tf = st.text_input("TF (e.g. 1m, 5m)").upper()
            sess = st.selectbox("SESSION", ["ASIA", "LONDON", "NY AM", "NY PM"])
            dur = st.number_input("DURATION (MINS)", 1, 1440, 15)
            target_val = st.text_input("TARGET (DOL/LEVEL)").upper()

        with c3:
            res = st.selectbox("RESULT", ["WIN", "LOSS", "BE"])
            # PRICE LEVEL INPUTS
            e_price = st.number_input("ENTRY PRICE", value=0.0, format="%.2f")
            sl_price = st.number_input("STOP LOSS PRICE", value=0.0, format="%.2f")
            tp_price = st.number_input("TAKE PROFIT PRICE", value=0.0, format="%.2f")
            rsk = st.number_input("RISK %", 0.1, 100.0, 1.0)
            dt = st.date_input("DATE", datetime.now())
            
        st.divider()
        st.write("### 📏 RELEVANT SESSION RANGES (HANDLES)")
        # Dynamic Selection Logic
        selected_sessions = st.multiselect("SELECT SESSIONS TO LOG VOLATILITY", ["CBDR", "ASIA", "LONDON", "NY AM", "NY PM"])
        
        # Dictionary to store session range values - maps dropdown label to DB column
        ranges = {"CBDR": None, "ASIA": None, "LONDON": None, "NY AM": None, "NY PM": None}
        
        if selected_sessions:
            # Create dynamic columns based on how many sessions are selected
            r_cols = st.columns(len(selected_sessions))
            for i, sess_name in enumerate(selected_sessions):
                # 0.25 step for handle precision
                ranges[sess_name] = r_cols[i].number_input(f"{sess_name} Handles", value=0.0, step=0.25)

        st.divider()
        nts = st.text_area("CONFLUENCE NOTES / PSYCHOLOGY")
        img = st.file_uploader("ENTRY SCREENSHOT", type=['png', 'jpg', 'jpeg'])
        
        if st.form_submit_button("FIRE INTO PRIVATE VAULT"):
            # AUTOMATIC MATH Logic
            sl_h = abs(e_price - sl_price)
            tp_h = abs(e_price - tp_price)
            calc_rr = tp_h / sl_h if sl_h > 0 else 0
            
            trade_data = {
                "trader_username": st.session_state.user,
                "model_name": mod, "model_var": mvar, "type": env, "market": mkt,
                "entry_time": tm, "entry_tf": tf, "session": sess, "result": res,
                "risk_pc": rsk, "rr": calc_rr, "sl_handles": sl_h, "tp_handles": tp_h,
                "entry_price": e_price, "sl_price": sl_price, "tp_price": tp_price,
                "notes": nts, "date": str(dt), "duration_mins": dur, 
                "screenshot_text": image_to_base64(img), 
                "hindsight": is_hindsight, "news_impact": news,
                "entry_type": etype, "target": target_val,
                "cbdr_size": ranges["CBDR"], 
                "asia_size": ranges["ASIA"],
                "london_size": ranges["LONDON"], 
                "ny_am_size": ranges["NY AM"],
                "ny_pm_size": ranges["NY PM"]
            }
            try:
                supabase.table("trades").insert(trade_data).execute()
                st.success(f"🎯 TRADE SECURED | RR: {round(calc_rr, 2)}R")
                st.rerun()
            except Exception as e:
                st.error(f"DATABASE ERROR: {e}")

def render_compounder():
    st.markdown('<h2 style="color: #FF4B4B;">📈 COMPOUNDER</h2>', unsafe_allow_html=True)
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