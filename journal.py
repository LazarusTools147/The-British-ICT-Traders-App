import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_supabase

def render_journal_tab():
    st.header(f"📓 {st.session_state.user}'s PRIVATE JOURNAL")
    supabase = get_supabase()
    
    # INTEGRATED CHANGE: Strictly pull only current user's trades
    response = supabase.table("trades").select("*").eq("trader_username", st.session_state.user).execute()
    df = pd.DataFrame(response.data)

    if df.empty:
        st.info("Your journal is currently empty.")
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

    for _, row in df[::-1].iterrows():
        # Added more details to header
        header = f"📁 {row['model_name']} | {row['market']} | {row['date'].strftime('%Y-%m-%d')} | {row['result']}"
        with st.expander(header):
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                st.write(f"**⏰ Time:** {row['entry_time']}")
                st.write(f"**🌍 Session:** {row['session']}")
                st.write(f"**⏱️ Duration:** {row['duration_mins']}m")
            with c2:
                st.write(f"**📏 TF:** {row['entry_tf']}")
                st.write(f"**🛑 SL:** {row['sl_handles']}")
                st.write(f"**🎯 TP:** {row['tp_handles']}")
            with c3:
                st.write(f"**🎲 Risk:** {row['risk_pc']}%")
                st.write(f"**📊 Result:** {row['result']}")
                
                # INTEGRATED SECURITY: Delete only your own data
                if st.button("🗑️ DELETE ENTRY", key=f"del_{row['id']}"):
                    supabase.table("trades").delete().eq("id", row['id']).eq("trader_username", st.session_state.user).execute()
                    st.success("Deleted.")
                    st.rerun()
            
            st.divider()
            st.info(f"**NOTES:** {row['notes']}")
            if row['screenshot_text']:
                st.image(f"data:image/png;base64,{row['screenshot_text']}", use_container_width=True)