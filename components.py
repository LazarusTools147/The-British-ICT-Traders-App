import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection

def render_architect():
    """Tab 1: Building and editing trading models with schematics."""
    st.header("🏗️ MODEL_ARCHITECT")
    
    conn = get_connection()
    # Fetch existing models to see if we need to edit
    existing_models = pd.read_sql("SELECT * FROM models", conn)
    conn.close()

    # --- MODE SELECTOR ---
    mode = st.radio("ARCHITECT MODE", ["CREATE NEW MODEL", "EDIT/AMEND EXISTING"], horizontal=True)
    
    m_name = ""
    m_logic = ""
    m_sess = []
    current_img = None

    if mode == "EDIT/AMEND EXISTING":
        if existing_models.empty:
            st.warning("No models found in the vault to edit.")
        else:
            target = st.selectbox("SELECT MODEL TO AMEND", existing_models['name'].tolist())
            row = existing_models[existing_models['name'] == target].iloc[0]
            m_name = row['name']
            m_logic = row['logic']
            m_sess = row['sessions'].split(",") if row['sessions'] else []
            # Safety check for the screenshot column
            current_img = row['screenshot'] if 'screenshot' in existing_models.columns else None

    # --- THE ARCHITECT FORM ---
    with st.form("model_form", clear_on_submit=(mode == "CREATE NEW MODEL")):
        st.subheader("Model Specifications")
        name_input = st.text_input("MODEL NAME (e.g., THE LONDON MODEL)", value=m_name).upper()
        sess_input = st.multiselect("ALLOWED SESSIONS", ["ASIA", "LONDON", "NY AM", "NY PM"], default=m_sess)
        logic_input = st.text_area("CORE LOGIC & ENTRY RULES", value=m_logic, height=250)
        
        st.divider()
        st.subheader("Visual Schematic")
        img_input = st.file_uploader("UPLOAD MODEL EXAMPLE (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
        
        if st.form_submit_button("ARCHIVE TO VAULT"):
            if name_input and logic_input:
                # Logic: If editing and no new image uploaded, keep the old one.
                final_img = img_input.read() if img_input else current_img
                
                conn = get_connection()
                conn.execute(
                    "INSERT OR REPLACE INTO models (name, logic, sessions, screenshot) VALUES (?, ?, ?, ?)",
                    (name_input, logic_input, ",".join(sess_input), final_img)
                )
                conn.commit()
                conn.close()
                st.success(f"✔️ {name_input} UPDATED AND SECURED")
                st.rerun()
            else:
                st.error("Name and Logic are mandatory.")

    # Display the current schematic if it exists
    if current_img:
        st.divider()
        st.subheader(f"Current {m_name} Schematic")
        st.image(current_img, use_container_width=True)

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
            mkt = st.text_input("MARKET").upper()
            
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
            
        nts = st.text_area("JOURNAL NOTES")
        img = st.file_uploader("UPLOAD CHART SCREENSHOT", type=['png', 'jpg', 'jpeg'])
        
        if st.form_submit_button("SAVE DATA"):
            if not mkt or not tm:
                st.error("Market and Time are mandatory.")
            else:
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
                st.success("🎯 DATA ARCHIVED")

def render_compounder():
    """Tab 6: Advanced Equity Projector with Lifestyle Variables."""
    st.header("📈 ADVANCED EQUITY PROJECTOR")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("Core Strategy")
        start_bal = st.number_input("STARTING CAPITAL ($)", value=5000)
        monthly_ret = st.number_input("MONTHLY % RETURN TARGET", value=5.0)
        years = st.number_input("YEARS TO PROJECT", min_value=1, value=5)
        
        st.divider()
        st.subheader("Deposit Plan")
        dep_amt = st.number_input("ADDITIONAL DEPOSIT ($/month)", value=100)
        dep_inc = st.number_input("YEARLY DEPOSIT INCREASE (%)", value=0.0)
        
        st.divider()
        st.subheader("Withdrawal Plan")
        wit_amt = st.number_input("WITHDRAWAL AMOUNT ($)", value=0)
        wit_freq = st.selectbox("FREQUENCY", ["WEEKLY", "MONTHLY", "QUARTERLY", "YEARLY"])

    # Frequency mapping to months
    freq_map = {"WEEKLY": 4, "MONTHLY": 1, "QUARTERLY": 3, "YEARLY": 12}
    
    current_bal = start_bal
    current_dep = dep_amt
    plot_data = []
    
    for m in range(1, int(years * 12) + 1):
        # 1. Trading Gains
        current_bal *= (1 + (monthly_ret / 100))
        # 2. Add External Deposits
        current_bal += current_dep
        # 3. Apply Scheduled Withdrawals
        if m % freq_map[wit_freq] == 0:
            withdrawal_total = wit_amt * (4 if wit_freq == "WEEKLY" else 1)
            current_bal -= withdrawal_total
            
        # 4. Yearly Deposit Scaling
        if m % 12 == 0:
            current_dep *= (1 + (dep_inc / 100))
            plot_data.append({"Year": m // 12, "Projected Balance": round(max(0, current_bal), 2)})
            
    df = pd.DataFrame(plot_data)
    
    with c2:
        if not df.empty:
            st.line_chart(df.set_index("Year"))
            st.subheader("Year-End Breakdown")
            st.table(df)