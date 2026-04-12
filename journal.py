import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_supabase

def render_journal_tab():
    st.header(f"📓 {st.session_state.user}'s PRIVATE JOURNAL")
    supabase = get_supabase()
    
    response = supabase.table("trades").select("*").eq("trader_username", st.session_state.user).execute()
    df = pd.DataFrame(response.data)

    if df.empty:
        st.info("Journal is empty.")
        return

    df['date'] = pd.to_datetime(df['date'])
    cal_filter = st.radio("JOURNAL FILTER", ["All", "Month", "Week", "Day"], horizontal=True)
    
    now = datetime.now()
    if cal_filter == "Month": df = df[df['date'].dt.month == now.month]
    elif cal_filter == "Week": df = df[df['date'] >= (now - timedelta(days=7))]
    elif cal_filter == "Day": df = df[df['date'].dt.date == now.date()]

    st.divider()

    for _, row in df[::-1].iterrows():
        color = "🟢" if row['result'] == "WIN" else "🔴" if row['result'] == "LOSS" else "🟡"
        header = f"{color} {row['model_name']} | {row['market']} | {row['date'].strftime('%d %b')} | {round(row['rr'], 2)}R"
        
        with st.expander(header):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"**⏰ Time:** {row['entry_time']}")
                st.write(f"**🌍 Session:** {row['session']}")
                st.write(f"**⏱️ Duration:** {row['duration_mins']}m")
            with c2:
                st.write(f"**📏 TF:** {row['entry_tf']}")
                st.write(f"**🎯 TP:** {row['tp_handles']}")
                st.write(f"**🛑 SL:** {row['sl_handles']}")
            with c3:
                st.write(f"**🎲 Risk:** {row['risk_pc']}%")
                st.write(f"**📰 News:** {row.get('news_impact', 'N/A')}")
                st.write(f"**🧠 Hindsight:** {'✅' if row.get('hindsight') else '❌'}")

            st.info(f"**📝 Notes:** {row['notes']}")
            if row['screenshot_text']:
                st.image(f"data:image/png;base64,{row['screenshot_text']}", use_container_width=True)

            st.divider()
            edit_col, del_col = st.columns(2)
            
            with edit_col:
                if st.button("✏️ EDIT", key=f"edit_{row['id']}"):
                    st.session_state.editing_id = row['id']
            
            with del_col:
                if st.button("🗑️ DELETE", key=f"del_{row['id']}"):
                    supabase.table("trades").delete().eq("id", row['id']).execute()
                    st.rerun()

            if st.session_state.get('editing_id') == row['id']:
                with st.form(f"edit_form_{row['id']}"):
                    new_notes = st.text_area("Update Notes", value=row['notes'])
                    new_res = st.selectbox("Update Result", ["WIN", "LOSS", "BE"], index=["WIN", "LOSS", "BE"].index(row['result']))
                    if st.form_submit_button("SAVE"):
                        supabase.table("trades").update({"notes": new_notes, "result": new_res}).eq("id", row['id']).execute()
                        st.session_state.editing_id = None
                        st.rerun()