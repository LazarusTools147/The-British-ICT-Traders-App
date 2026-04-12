import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_supabase

def render_journal_tab():
    st.header(f"📓 {st.session_state.user}'s PRIVATE JOURNAL")
    st.write("Institutional Trade Log & Performance Review")
    supabase = get_supabase()
    
    # PRIVACY FILTER: Strictly pull only the current user's trades
    try:
        response = supabase.table("trades").select("*").eq("trader_username", st.session_state.user).execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error connecting to Journal Vault: {e}")
        return

    if df.empty:
        st.info("Your private vault is currently empty. Log a trade in The Forge to see it here.")
        return

    # --- 1. WINNERS DEEP DIVE SECTION ---
    st.subheader("💎 WINNERS DEEP DIVE")
    winners = df[df['result'] == 'WIN']
    if not winners.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            avg_rr = winners['rr'].mean()
            st.metric("Avg Winner RR", f"{round(avg_rr, 2)}R")
        with c2:
            best_model = winners['model_name'].mode()[0]
            st.metric("Most Profitable Model", best_model)
        with c3:
            # Handle duration safety if column is empty
            avg_dur = winners['duration_mins'].mean() if 'duration_mins' in winners.columns else 0
            st.metric("Avg Win Duration", f"{round(avg_dur, 1)}m")
    else:
        st.info("Log some winning trades to activate the Deep Dive analytics.")

    st.divider()

    # --- 2. JOURNAL FILTERS ---
    df['date'] = pd.to_datetime(df['date'])
    cal_filter = st.radio("JOURNAL TIMEFRAME", ["All", "Month", "Week", "Day"], horizontal=True)
    
    now = datetime.now()
    if cal_filter == "Month": 
        df = df[df['date'].dt.month == now.month]
    elif cal_filter == "Week": 
        df = df[df['date'] >= (now - timedelta(days=7))]
    elif cal_filter == "Day": 
        df = df[df['date'].dt.date == now.date()]

    # --- 3. TRADE ENTRIES (REVERSE CHRONOLOGICAL) ---
    for _, row in df[::-1].iterrows():
        color = "🟢" if row['result'] == "WIN" else "🔴" if row['result'] == "LOSS" else "🟡"
        header = f"{color} {row['model_name']} | {row['market']} | {row['date'].strftime('%d %b %Y')} | {round(row['rr'], 2)}R"
        
        with st.expander(header):
            # THE FULL STAT READOUT
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"**⏰ Entry Time:** {row.get('entry_time', 'N/A')}")
                st.write(f"**🌍 Session:** {row.get('session', 'N/A')}")
                st.write(f"**⏱️ Duration:** {row.get('duration_mins', 0)}m")
                # Safety check for news_impact
                st.write(f"**📰 News Impact:** {row.get('news_impact', 'NONE')}")
            with c2:
                st.write(f"**📏 Timeframe:** {row.get('entry_tf', 'N/A')}")
                st.write(f"**🎯 TP Handles:** {row.get('tp_handles', 0)}")
                st.write(f"**🛑 SL Handles:** {row.get('sl_handles', 0)}")
            with c3:
                st.write(f"**🎲 Risk:** {row.get('risk_pc', 0)}%")
                st.write(f"**📊 Result:** {row['result']}")
                # Safety check for hindsight
                h_val = row.get('hindsight', False)
                st.write(f"**🧠 Mode:** {'✅ HINDSIGHT' if h_val else '❌ LIVE'}")
                
                # DELETE FUNCTIONALITY
                if st.button("🗑️ DELETE ENTRY", key=f"del_{row['id']}"):
                    supabase.table("trades").delete().eq("id", row['id']).eq("trader_username", st.session_state.user).execute()
                    st.success("Purged.")
                    st.rerun()
            
            st.divider()
            
            # NOTES & SCREENSHOT
            st.info(f"**CONFLUENCE NOTES:**\n\n{row['notes']}")
            if row.get('screenshot_text'):
                st.image(f"data:image/png;base64,{row['screenshot_text']}", use_container_width=True)

            # --- 4. EDIT FUNCTIONALITY ---
            st.divider()
            # Toggle edit mode in session state
            edit_requested = st.button("✏️ EDIT DETAILS", key=f"edit_btn_{row['id']}")
            if edit_requested:
                st.session_state.editing_id = row['id']
            
            if st.session_state.get('editing_id') == row['id']:
                with st.form(f"edit_form_{row['id']}"):
                    st.subheader("Update Execution Data")
                    new_notes = st.text_area("Update Notes", value=row['notes'], height=150)
                    # Find index for result selectbox
                    res_options = ["WIN", "LOSS", "BE"]
                    res_index = res_options.index(row['result']) if row['result'] in res_options else 0
                    new_res = st.selectbox("Update Result", res_options, index=res_index)
                    
                    c_save, c_cancel = st.columns(2)
                    with c_save:
                        if st.form_submit_button("💾 SAVE"):
                            update_data = {"notes": new_notes, "result": new_res}
                            supabase.table("trades").update(update_data).eq("id", row['id']).eq("trader_username", st.session_state.user).execute()
                            st.session_state.editing_id = None
                            st.success("Updated!")
                            st.rerun()
                    with c_cancel:
                        if st.form_submit_button("❌ CANCEL"):
                            st.session_state.editing_id = None
                            st.rerun()