import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_connection

def render_journal_tab():
    """
    Tab 5: The Master Journal.
    Features EE-style filtering, Trade Expanders, and Inline Editing.
    """
    st.header("📓 THE MASTER JOURNAL")
    
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM trades", conn)
    conn.close()

    if df.empty:
        st.info("THE VAULT IS EMPTY. LOG YOUR FIRST SESSION IN THE FORGE.")
        return

    # --- 1. EE-STYLE CALENDAR NAVIGATION ---
    st.markdown("### 📅 CALENDAR NAVIGATION")
    cal_filter = st.radio(
        "FILTER BY", 
        ["All Trades", "By Year", "By Month", "By Week", "By Day"], 
        horizontal=True, 
        label_visibility="collapsed"
    )
    
    df['date'] = pd.to_datetime(df['date'])
    now = datetime.now()

    if "Year" in cal_filter:
        df = df[df['date'].dt.year == now.year]
    elif "Month" in cal_filter:
        df = df[(df['date'].dt.month == now.month) & (df['date'].dt.year == now.year)]
    elif "Week" in cal_filter:
        df = df[df['date'] >= (now - timedelta(days=7))]
    elif "Day" in cal_filter:
        df = df[df['date'].dt.date == now.date()]

    # --- 2. VARIATION SUB-TABS ---
    vars_available = ["ALL VARIATIONS"] + list(df['model_var'].dropna().unique())
    v_select = st.selectbox("MODEL VARIATION SUB-FILTER", vars_available)
    if v_select != "ALL VARIATIONS":
        df = df[df['model_var'] == v_select]

    st.divider()

    # --- 3. THE FEED (Reverse Chronological) ---
    for _, row in df[::-1].iterrows():
        # Dynamic Header with Result Coloring
        header_text = f"📁 {row['model_name']} [{row['model_var']}] — {row['date'].strftime('%Y-%m-%d')} — {row['result']}"
        
        with st.expander(header_text):
            edit_key = f"edit_mode_{row['id']}"
            
            # Initialize Edit State
            if edit_key not in st.session_state:
                st.session_state[edit_key] = False

            if not st.session_state[edit_key]:
                # --- VIEW MODE ---
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.write(f"**TIME:** {row['entry_time']} | **TF:** {row['entry_tf']} | **SESS:** {row['session']}")
                    st.write(f"**SL:** {row['sl_handles']}h | **TP:** {row['tp_handles']}h | **RR:** {round(row['rr'], 2)}R")
                    st.info(f"**NOTES:** {row['notes']}")
                    
                    # Actions
                    col_e, col_d = st.columns(2)
                    if col_e.button("✏️ EDIT ENTRY", key=f"btn_edit_{row['id']}"):
                        st.session_state[edit_key] = True
                        st.rerun()
                    if col_d.button("🗑️ DELETE", key=f"btn_del_{row['id']}"):
                        conn = get_connection()
                        conn.execute("DELETE FROM trades WHERE id=?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
                with c2:
                    if row['screenshot']:
                        st.image(row['screenshot'], caption="Trade Setup", use_container_width=True)
            else:
                # --- EDIT MODE (Repaired Logic) ---
                with st.form(key=f"form_edit_{row['id']}"):
                    st.subheader("Edit Trade Parameters")
                    new_nts = st.text_area("NOTES", value=str(row['notes'] or ""))
                    
                    ec1, ec2, ec3 = st.columns(3)
                    with ec1:
                        new_res = st.selectbox("RESULT", ["WIN", "LOSS", "BE"], index=["WIN", "LOSS", "BE"].index(row['result']))
                    with ec2:
                        new_sl = st.number_input("SL HANDLES", value=float(row['sl_handles'] or 0.0))
                    with ec3:
                        new_tp = st.number_input("TP HANDLES", value=float(row['tp_handles'] or 0.0))
                    
                    new_var = st.text_input("VARIATION", value=str(row['model_var'] or ""))
                    
                    # Form Actions
                    save_c, cancel_c = st.columns(2)
                    if save_c.form_submit_button("💾 SAVE CHANGES"):
                        # Calculate new RR based on edited handles
                        new_rr = new_tp / new_sl if new_sl > 0 else 0
                        conn = get_connection()
                        conn.execute('''
                            UPDATE trades 
                            SET notes=?, result=?, model_var=?, sl_handles=?, tp_handles=?, rr=? 
                            WHERE id=?
                        ''', (new_nts, new_res.upper(), new_var.upper(), new_sl, new_tp, new_rr, row['id']))
                        conn.commit()
                        conn.close()
                        st.session_state[edit_key] = False
                        st.rerun()
                    
                    if cancel_c.form_submit_button("❌ CANCEL"):
                        st.session_state[edit_key] = False
                        st.rerun()