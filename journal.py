import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_supabase

def render_journal_tab():
    # Personalize the header based on who is logged in
    st.header(f"📓 {st.session_state.user}'s PRIVATE JOURNAL")
    supabase = get_supabase()
    
    # PRIVACY FILTER: Strictly pull data for the logged-in user only
    response = supabase.table("trades").select("*").eq("trader_username", st.session_state.user).execute()
    df = pd.DataFrame(response.data)

    if df.empty:
        st.info("Your private vault is empty. Log a trade in The Forge to see it here.")
        return

    df['date'] = pd.to_datetime(df['date'])
    cal_filter = st.radio("JOURNAL FILTER", ["All", "Month", "Week", "Day"], horizontal=True)
    
    now = datetime.now()
    if cal_filter == "Month": 
        df = df[df['date'].dt.month == now.month]
    elif cal_filter == "Week": 
        df = df[df['date'] >= (now - timedelta(days=7))]
    elif cal_filter == "Day": 
        df = df[df['date'].dt.date == now.date()]

    st.divider()

    # Iterate through the filtered dataframe
    for _, row in df[::-1].iterrows():
        header = f"📁 {row['model_name']} — {row['date'].strftime('%Y-%m-%d')} — {row['result']}"
        with st.expander(header):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.write(f"**TIME:** {row['entry_time']} | **TF:** {row['entry_tf']} | **SESS:** {row['session']}")
                st.write(f"**RR:** {round(row['rr'], 2)}R | **RISK:** {row['risk_pc']}%")
                st.info(f"**NOTES:** {row['notes']}")
                
                # Ensure the delete button also respects the user filter for safety
                if st.button("🗑️ DELETE ENTRY", key=f"del_{row['id']}"):
                    supabase.table("trades").delete().eq("id", row['id']).eq("trader_username", st.session_state.user).execute()
                    st.success("Entry Deleted.")
                    st.rerun()
            with c2:
                if row['screenshot_text']:
                    st.image(f"data:image/png;base64,{row['screenshot_text']}", use_container_width=True)