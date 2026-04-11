import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection

def render_architect():
    """Tab 1: Building and editing trading models with schematics."""
    st.header("🏗️ MODEL_ARCHITECT")
    
    conn = get_connection()
    # Fetch existing models to populate the editor
    existing_models = pd.read_sql("SELECT * FROM models", conn)
    conn.close()

    # --- ARCHITECT MODE SELECTOR ---
    mode = st.radio("SELECT ARCHITECT MODE", ["CREATE NEW MODEL", "EDIT EXISTING MODEL"], horizontal=True)
    
    # Initialize form variables
    m_name = ""
    m_logic = ""
    m_sess = []
    current_img = None

    if mode == "EDIT EXISTING MODEL":
        if existing_models.empty:
            st.warning("No models found in the vault to edit.")
        else:
            target_model = st.selectbox("SELECT MODEL TO AMEND", existing_models['name'].tolist())
            # Extract data for the selected model
            model_row = existing_models[existing_models['name'] == target_model].iloc[0]
            m_name = model_row['name']
            m_logic = model_row['logic']
            # Convert comma-separated string back to list for multiselect
            if model_row['sessions']:
                m_sess = model_row['sessions'].split(",")
            # Get existing image if available
            if 'screenshot' in existing_models.columns:
                current_img = model_row['screenshot']

    # --- THE MODEL FORM ---
    with st.form("model_form", clear_on_submit=(mode == "CREATE NEW MODEL")):
        st.subheader("Model Specifications")
        
        name_input = st.text_input("MODEL NAME", value=m_name).upper()
        
        sess_input = st.multiselect(
            "ALLOWED SESSIONS", 
            ["ASIA", "LONDON", "NY AM", "NY PM"], 
            default=m_sess
        )
        
        logic_input = st.text_area(
            "CORE LOGIC & ENTRY RULES", 
            value=m_logic, 
            height=250,
            placeholder="Define your NWOG, FVG, and MSS criteria here..."
        )
        
        st.divider()
        st.subheader("Visual Schematic")
        st.info("Upload a 'Standard' example of this model for quick reference.")
        img_input = st.file_uploader("UPLOAD PNG/JPG SCHEMATIC", type=['png', 'jpg', 'jpeg'])
        
        if st.form_submit_button("ARCHIVE MODEL TO VAULT"):
            if name_input and logic_input:
                # If editing and no new image, retain the old one
                save_img = img_input.read() if img_input else current_img
                
                conn = get_connection()
                conn.execute(
                    "INSERT OR REPLACE INTO models (name, logic, sessions, screenshot) VALUES (?, ?, ?, ?)",
                    (name_input, logic_input, ",".join(sess_input), save_img)
                )
                conn.commit()
                conn.close()
                st.success(f"✔️ MODEL '{name_input}' HAS BEEN SECURED.")
                st.rerun()
            else:
                st.error("Model Name and Logic are mandatory fields.")

    # Show existing schematic if in edit mode and image exists
    if mode == "EDIT EXISTING MODEL" and current_img:
        st.divider()
        st.subheader(f"Current {m_name} Schematic")
        st.image(current_img, use_container_width=True)

def render_forge():
    """Tab 2: The high-speed trade logger."""
    conn = get_connection()
    models_df = pd.read_sql("SELECT name FROM models", conn)
    conn.close()
    
    models_list = models_df['name'].tolist()
    
    if not models_list:
        st.warning("⚠️ NO MODELS FOUND. CREATE ONE IN THE ARCHITECT TAB FIRST.")
        return

    st.header("🔥 THE FORGE: SESSION LOGGING")
    
    with st.form("forge_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            env = st.radio("ENVIRONMENT", ["LIVE", "BACKTEST/DEMO"], horizontal=True)
            mod = st.selectbox("MODEL", models_list)
            mvar = st.text_input("MODEL VARIATION (e.g., 2022, Silver Bullet)").upper()
            mkt = st.text_input("MARKET (e.g., NQ, ES, GOLD)").upper()
            
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
                # Math: TP / SL = RR
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
                st.success("🎯 DATA ARCHIVED SUCCESSFULLY.")

def render_compounder():
    """Tab 6: Advanced Equity Projector with Lifestyle Variables."""
    st.header("📈 ADVANCED EQUITY PROJECTOR")
    
    col_input, col_chart = st.columns([1, 2])
    
    with col_input:
        st.subheader("Strategy Parameters")
        start_bal = st.number_input("STARTING CAPITAL ($)", value=5000)
        monthly_ret = st.number_input("MONTHLY % RETURN", value=5.0)
        years_to_run = st.number_input("YEARS TO PROJECT", min_value=1, value=5)
        
        st.divider()
        st.subheader("Deposit Growth")
        monthly_deposit = st.number_input("ADDITIONAL DEPOSIT ($/mo)", value=100)
        annual_dep_increase = st.number_input("YEARLY DEPOSIT INCREASE (%)", value=0.0)
        
        st.divider()
        st.subheader("Withdrawal Logic")
        withdraw_amt = st.number_input("WITHDRAWAL AMOUNT ($)", value=0)
        withdraw_freq = st.selectbox(
            "WITHDRAWAL FREQUENCY", 
            ["WEEKLY", "MONTHLY", "QUARTERLY", "YEARLY"]
        )

    # Calculation logic for frequency
    freq_lookup = {"WEEKLY": 4, "MONTHLY": 1, "QUARTERLY": 3, "YEARLY": 12}
    
    # Projection Math
    balance_tracker = start_bal
    current_monthly_dep = monthly_deposit
    yearly_results = []
    
    total_months = int(years_to_run * 12)
    
    for month in range(1, total_months + 1):
        # 1. Apply Compound Interest
        balance_tracker *= (1 + (monthly_ret / 100))
        
        # 2. Add the Deposit
        balance_tracker += current_monthly_dep
        
        # 3. Handle Withdrawals based on selected frequency
        months_per_withdrawal = freq_lookup[withdraw_freq]
        if month % months_per_withdrawal == 0:
            # If weekly, we multiply by 4 to get the monthly total withdrawal
            actual_withdraw = withdraw_amt * (4 if withdraw_freq == "WEEKLY" else 1)
            balance_tracker -= actual_withdraw
            
        # 4. Handle Annual Deposit Increases
        if month % 12 == 0:
            current_monthly_dep *= (1 + (annual_dep_increase / 100))
            yearly_results.append({
                "Year": month // 12, 
                "Projected Balance": round(max(0, balance_tracker), 2)
            })
            
    results_df = pd.DataFrame(yearly_results)
    
    with col_chart:
        if not results_df.empty:
            st.line_chart(results_df.set_index("Year"))
            st.subheader("Year-End Capital Breakdown")
            st.table(results_df)
        else:
            st.info("Adjust parameters to generate projection.")