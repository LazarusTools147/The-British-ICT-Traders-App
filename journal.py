import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_supabase

def render_journal_tab():
    # Restoring the Red Institutional Header from your old build
    st.markdown('<h2 style="color: #FF4B4B;">📓 TRADE JOURNAL</h2>', unsafe_allow_html=True)
    st.write(f"Logged as: {st.session_state.user}")
    supabase = get_supabase()
    
    try:
        response = supabase.table("trades").select("*").eq("trader_username", st.session_state.user).execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error connecting to Journal Vault: {e}")
        return

    if df.empty:
        st.info("Your private vault is currently empty.")
        return

    # --- 1. WINNERS DEEP DIVE (TOP STATS) ---
    winners = df[df['result'] == 'WIN']
    if not winners.empty:
        st.subheader("💎 WINNERS DEEP DIVE")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Avg Winner RR", f"{round(winners['rr'].mean(), 2)}R")
        with c2:
            st.metric("Top Model", winners['model_name'].mode()[0])
        with c3:
            avg_dur = winners['duration_mins'].mean() if 'duration_mins' in winners.columns else 0
            st.metric("Avg Win Duration", f"{round(avg_dur, 1)}m")
    
    st.divider()

    # --- 2. JOURNAL FILTERS ---
    df['date'] = pd.to_datetime(df['date'])
    # Swapped radio for selectbox to match high-density UI
    cal_filter = st.selectbox("TIMEFRAME", ["All", "Month", "Week", "Day"])
    
    now = datetime.now()
    if cal_filter == "Month": 
        df = df[df['date'].dt.month == now.month]
    elif cal_filter == "Week": 
        df = df[df['date'] >= (now - timedelta(days=7))]
    elif cal_filter == "Day": 
        df = df[df['date'].dt.date == now.date()]

    # --- 3. TRADE ENTRIES (REVERSE CHRONOLOGICAL) ---
    # Sorting newest at the top
    for _, row in df.sort_values('date', ascending=False).iterrows():
        res = row['result']
        color = "#00FF00" if res == "WIN" else "#FF0000" if res == "LOSS" else "#808080"
        icon = "🟢" if res == "WIN" else "🔴" if res == "LOSS" else "🟡"
        header = f"{icon} {row['model_name']} | {row['market']} | {row['date'].strftime('%d %b %Y')} | {round(row['rr'], 2)}R"
        
        with st.expander(header):
            # Restore 3-Column high density layout from old build
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**EXECUTION**")
                st.write(f"TIME: `{row.get('entry_time', 'N/A')}`")
                st.write(f"SESS: `{row.get('session', 'N/A')}`")
                st.write(f"DUR: `{row.get('duration_mins', 0)}m`")
                st.write(f"NEWS: `{row.get('news_impact', 'NONE')}`")
            with c2:
                st.markdown("**TECHNICAL**")
                st.write(f"TF: `{row.get('entry_tf', 'N/A')}`")
                st.write(f"TP: `{row.get('tp_handles', 0)}` handles")
                st.write(f"SL: `{row.get('sl_handles', 0)}` handles")
            with c3:
                st.markdown("**RISK**")
                st.write(f"RISK: `{row.get('risk_pc', 0)}%`")
                st.write(f"RESULT: :{color}[**{res}**]")
                h_val = row.get('hindsight', False)
                st.write(f"MODE: `{'HINDSIGHT' if h_val else 'LIVE'}`")
                
                if st.button("🗑️ PURGE", key=f"del_{row['id']}"):
                    supabase.table("trades").delete().eq("id", row['id']).execute()
                    st.rerun()
            
            st.divider()
            st.info(f"**CONFLUENCE NOTES:**\n\n{row['notes']}")
            
            if row.get('screenshot_text'):
                st.image(f"data:image/png;base64,{row['screenshot_text']}", use_container_width=True)

            # --- 4. EDIT LOGIC ---
            if st.button("✏️ EDIT DETAILS", key=f"edit_btn_{row['id']}"):
                st.session_state.editing_id = row['id']
            
            if st.session_state.get('editing_id') == row['id']:
                with st.form(f"edit_{row['id']}"):
                    new_notes = st.text_area("Update Notes", value=row['notes'], height=150)
                    new_res = st.selectbox("Update Result", ["WIN", "LOSS", "BE"], index=["WIN", "LOSS", "BE"].index(row['result']))
                    
                    if st.form_submit_button("💾 SAVE"):
                        supabase.table("trades").update({"notes": new_notes, "result": new_res}).eq("id", row['id']).execute()
                        st.session_state.editing_id = None
                        st.rerun()