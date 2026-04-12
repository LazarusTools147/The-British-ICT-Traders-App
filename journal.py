import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_supabase

def render_journal_tab():
    st.header(f"📓 {st.session_state.user}'s PRIVATE JOURNAL")
    st.write("Institutional Trade Log & Performance Review")
    supabase = get_supabase()
    
    # PRIVACY FILTER: Strictly pull only the current user's trades
    response = supabase.table("trades").select("*").eq("trader_username", st.session_state.user).execute()
    df = pd.DataFrame(response.data)

    if df.empty:
        st.info("Your private vault is currently empty. Log a trade in The Forge to see it here.")
        return

    # --- 1. WINNERS DEEP DIVE SECTION ---
    # This provides high-level insight into what is working for your specific account
    st.subheader("💎 WINNERS DEEP DIVE")
    winners = df[df['result'] == 'WIN']
    if not winners.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            avg_rr = winners['rr'].mean()
            st.metric("Avg Winner RR", f"{round(avg_rr, 2)}R")
        with c2:
            # Finds the model name with the most wins
            best_model = winners['model_name'].mode()[0]
            st.metric("Most Profitable Model", best_model)
        with c3:
            avg_dur = winners['duration_mins'].mean()
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
        # Status icon based on result
        color = "🟢" if row['result'] == "WIN" else "🔴" if row['result'] == "LOSS" else "🟡"
        header = f"{color} {row['model_name']} | {row['market']} | {row['date'].strftime('%d %b %Y')} | {round(row['rr'], 2)}R"
        
        with st.expander(header):
            # THE FULL STAT READOUT (EVERYTHING FROM THE FORGE)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"**⏰ Entry Time:** {row['entry_time']}")
                st.write(f"**🌍 Session:** {row['session']}")
                st.write(f"**⏱️ Duration:** {row['duration_mins']}m")
                st.write(f"**📰 News Impact:** {row.get('news_impact', 'NONE')}")
            with c2:
                st.write(f"**📏 Timeframe:** {row['entry_tf']}")
                st.write(f"**🎯 TP Handles:** {row['tp_handles']}")
                st.write(f"**🛑 SL Handles:** {row['sl_handles']}")
            with c3:
                st.write(f"**🎲 Risk:** {row['risk_pc']}%")
                st.write(f"**📊 Result:** {row['result']}")
                st.write(f"**🧠 Hindsight:** {'✅ STUDY' if row.get('hindsight') else '❌ LIVE'}")
                
                # DELETE FUNCTIONALITY
                if st.button("🗑️ DELETE ENTRY", key=f"del_{row['id']}"):
                    supabase.table("trades").delete().eq("id", row['id']).eq("trader_username", st.session_state.user).execute()
                    st.success("Entry Purged from Vault.")
                    st.rerun()
            
            st.divider()
            
            # NOTES & SCREENSHOT
            st.info(f"**CONFLUENCE NOTES:**\n\n{row['notes']}")
            if row['screenshot_text']:
                st.image(f"data:image/png;base64,{row['screenshot_text']}", use_container_width=True, caption="Execution Screenshot")

            # --- 4. EDIT FUNCTIONALITY ---
            st.divider()
            if st.button("✏️ EDIT TRADE DETAILS", key=f"edit_btn_{row['id']}"):
                st.session_state.editing_id = row['id']
            
            if st.session_state.get('editing_id') == row['id']:
                with st.form(f"edit_form_{row['id']}"):
                    st.subheader("Refine Trade Data")
                    new_notes = st.text_area("Update Notes", value=row['notes'], height=150)
                    new_res = st.selectbox("Update Result", ["WIN", "LOSS", "BE"], index=["WIN", "LOSS", "BE"].index(row['result']))
                    
                    c_save, c_cancel = st.columns(2)
                    with c_save:
                        if st.form_submit_button("💾 SAVE CHANGES"):
                            # Update the record in Supabase
                            update_data = {"notes": new_notes, "result": new_res}
                            supabase.table("trades").update(update_data).eq("id", row['id']).eq("trader_username", st.session_state.user).execute()
                            st.session_state.editing_id = None
                            st.rerun()
                    with c_cancel:
                        if st.form_submit_button("❌ CANCEL"):
                            st.session_state.editing_id = None
                            st.rerun()