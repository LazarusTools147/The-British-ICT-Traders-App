import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection

def render_architect():
    """Tab 1: Building and archiving trading models."""
    st.header("🏗️ MODEL_ARCHITECT")
    
    with st.container():
        m_name = st.text_input("MODEL NAME (e.g., THE LONDON MODEL)").upper()
        m_sess = st.multiselect("ALLOWED SESSIONS", ["ASIA", "LONDON", "NY AM", "NY PM"])
        m_logic = st.text_area("CORE LOGIC & ENTRY RULES", height=200)
        
        if st.button("SAVE MODEL TO VAULT"):
            if m_name and m_logic:
                conn = get_connection()
                conn.execute(
                    "INSERT OR REPLACE INTO models (name, logic, sessions) VALUES (?, ?, ?)",
                    (m_name, m_logic, ",".join(m_sess))
                )
                conn.commit()
                conn.close()
                st.success(f"✔️ {m_name} ARCHIVED SUCCESSFULLY")
            else:
                st.error("Model Name and Logic are required.")

def render_forge():
    """Tab 2: The high-speed trade logger."""
    conn = get_connection()
    models_df = pd.read_sql("SELECT name FROM models", conn)
    conn.close()
    
    models = models_df['name'].tolist()
    
    if not models:
        st.warning("⚠️ NO MODELS FOUND. CREATE ONE IN THE ARCHITECT TAB FIRST.")
        return

    st.header("🔥 THE FORGE: SESSION LOGGING")
    
    with st.form("forge_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            env = st.radio("ENVIRONMENT", ["LIVE", "BACKTEST/DEMO"], horizontal=True)
            mod = st.selectbox("MODEL", models)
            mvar = st.text_input("MODEL VARIATION").upper()
            mkt = st.text_input("MARKET (e.g., NQ, GOLD)").upper()
            
        with c2:
            tm = st.text_input("ENTRY TIME (HH:MM)")
            tf = st.text_input("TIMEFRAME").upper()
            sess = st.text_input("SESSION").upper()
            dur = st.number_input("DURATION (MINS)", min_value=1, value=15)
            
        with c3:
            sl_h = st.number_input("SL HANDLES", min_value=0.1, value=5.0, step=0.1)
            tp_h = st.number_input("TP HANDLES", min_value=0.1, value=15.0, step=0.1)
            res = st.selectbox("RESULT", ["WIN", "LOSS", "BE"])
            rsk = st.number_input("RISK %", value=1.0, step=0.1)
            dt = st.date_input("DATE", datetime.now())
            
        nts = st.text_area("JOURNAL NOTES (Context, Mistakes, Wins)")
        img = st.file_uploader("UPLOAD CHART SCREENSHOT", type=['png', 'jpg', 'jpeg'])
        
        if st.form_submit_button("SAVE DATA TO JOURNAL"):
            if not mkt or not tm:
                st.error("Market and Time are mandatory fields.")
            else:
                # Institutional RR Calculation: TP / SL
                calculated_rr = tp_h / sl_h if sl_h > 0 else 0
                img_data = img.read() if img else None
                
                conn = get_connection()
                conn.execute('''
                    INSERT INTO trades (
                        model_name, model_var, type, market, entry_time, entry_tf, 
                        session, result, risk_pc, rr, sl_handles, tp_handles, 
                        notes, date, duration_mins, screenshot
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (mod, mvar, env, mkt, tm, tf, sess, res, rsk, calculated_rr, 
                     sl_h, tp_h, nts, dt.strftime("%Y-%m-%d"), dur, img_data)
                )
                conn.commit()
                conn.close()
                st.success("🎯 DATA SECURED. CHECK THE JOURNAL.")

def render_compounder():
    """Tab 6: Long-term equity projection."""
    st.header("📈 THE COMPOUNDER")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        p = st.number_input("STARTING BALANCE", value=5000)
        r = st.number_input("MONTHLY % TARGET", value=5.0)
        y = st.number_input("YEARS TO PROJECT", value=5)
        
    bal = p
    data = []
    total_months = int(y * 12)
    
    for m in range(1, total_months + 1):
        bal *= (1 + (r / 100))
        if m % 12 == 0:
            data.append({"Year": m // 12, "Balance": round(bal, 2)})
            
    df = pd.DataFrame(data)
    
    with c2:
        if not df.empty:
            st.line_chart(df.set_index("Year"))
            st.table(df)