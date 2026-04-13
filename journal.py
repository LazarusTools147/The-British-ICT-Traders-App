import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from database import get_supabase

def render_journal_tab():
    # 1. INSTITUTIONAL HEADER
    st.markdown('<h2 style="color: #FF4B4B;">📓 THE JOURNAL</h2>', unsafe_allow_html=True)
    st.write(f"Logged as: **{st.session_state.user}**")
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

    # --- 2. STATS & ANALYTICS OVERVIEW (The new Donut Layout) ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        # Donut Chart for Model Distribution (Replaces "Top Model" text)
        st.write("**MODEL DISTRIBUTION**")
        fig_mod = px.pie(df, names='model_name', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_mod.update_layout(showlegend=False, height=180, margin=dict(t=0, b=0, l=0, r=0))
        fig_mod.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_mod, use_container_width=True, key="journal_model_donut")

    with c2:
        # Donut Chart for Entry Type
        st.write("**ENTRY TYPES**")
        if 'entry_type' in df.columns and not df['entry_type'].dropna().empty:
            fig_ent = px.pie(df, names='entry_type', hole=0.6, color_discrete_sequence=px.colors.qualitative.Bold)
            fig_ent.update_layout(showlegend=False, height=180, margin=dict(t=0, b=0, l=0, r=0))
            fig_ent.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_ent, use_container_width=True, key="journal_entry_donut")
        else:
            st.info("No Entry Type data.")

    with c3:
        # High-level stats metric block
        winners = df[df['result'] == 'WIN']
        avg_rr = winners['rr'].mean() if not winners.empty else 0
        avg_dur = winners['duration_mins'].mean() if not winners.empty else 0
        st.metric("AVG WIN RR", f"{round(avg_rr, 2)}R")
        st.metric("AVG WIN DUR", f"{round(avg_dur, 1)}m")
    
    st.divider()

    # --- 3. HORIZONTAL CALENDAR & FILTER SYSTEM ---
    # Custom Radio styling to look like the image you provided
    cal_filter = st.radio(
        "TIMEFRAME SELECTOR", 
        ["All Sales", "By Year", "By Month", "By Week", "By Day"], 
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # MASTER FILTERS ROW
    f1, f2, f3 = st.columns(3)
    with f1:
        model_list = ["ALL MODELS"] + sorted(df['model_name'].unique().tolist())
        sel_model = st.selectbox("MODEL FILTER", model_list)
    with f2:
        var_list = ["ALL VARIATIONS"] + sorted(df['model_var'].dropna().unique().tolist())
        sel_var = st.selectbox("VARIATION FILTER", var_list)
    with f3:
        res_list = ["ALL RESULTS", "WIN", "LOSS", "BE"]
        sel_res = st.selectbox("RESULT FILTER", res_list)

    # Apply Filters
    df['date'] = pd.to_datetime(df['date'])
    now = datetime.now()
    
    if cal_filter == "By Year": df = df[df['date'].dt.year == now.year]
    elif cal_filter == "By Month": df = df[df['date'].dt.month == now.month]
    elif cal_filter == "By Week": df = df[df['date'] >= (now - timedelta(days=7))]
    elif cal_filter == "By Day": df = df[df['date'].dt.date == now.date()]

    if sel_model != "ALL MODELS": df = df[df['model_name'] == sel_model]
    if sel_var != "ALL VARIATIONS": df = df[df['model_var'] == sel_var]
    if sel_res != "ALL RESULTS": df = df[df['result'] == sel_res]

    # --- 4. TRADE ENTRIES ---
    for _, row in df.sort_values('date', ascending=False).iterrows():
        res = row['result']
        color = "#00FF00" if res == "WIN" else "#FF0000" if res == "LOSS" else "#808080"
        icon = "🟢" if res == "WIN" else "🔴" if res == "LOSS" else "🟡"
        
        # Expanded Header to include Variation as requested
        header = f"{icon} {row['model_name']} [{row.get('model_var', 'STD')}] | {row['market']} | {row['date'].strftime('%d %b %Y')} | {round(row['rr'], 2)}R"
        
        with st.expander(header):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**EXECUTION**")
                st.write(f"TIME: `{row.get('entry_time', 'N/A')}`")
                st.write(f"SESS: `{row.get('session', 'N/A')}`")
                st.write(f"DUR: `{row.get('duration_mins', 0)}m`")
                st.write(f"ENTRY: `{row.get('entry_type', 'STD')}`")
            with c2:
                st.markdown("**TECHNICAL**")
                st.write(f"TF: `{row.get('entry_tf', 'N/A')}`")
                st.write(f"VAR: `{row.get('model_var', 'N/A')}`")
                st.write(f"TP: `{row.get('tp_handles', 0)}` handles")
                st.write(f"SL: `{row.get('sl_handles', 0)}` handles")
            with c3:
                st.markdown("**RISK**")
                st.write(f"RISK: `{row.get('risk_pc', 0)}%`")
                st.write(f"RESULT: :{color}[**{res}**]")
                st.write(f"MODE: `{'HINDSIGHT' if row.get('hindsight') else 'LIVE'}`")
                
                if st.button("🗑️ PURGE", key=f"del_{row['id']}"):
                    supabase.table("trades").delete().eq("id", row['id']).execute()
                    st.rerun()
            
            st.divider()
            st.info(f"**CONFLUENCE NOTES:**\n\n{row['notes']}")
            
            if row.get('screenshot_text'):
                st.image(f"data:image/png;base64,{row['screenshot_text']}", use_container_width=True)

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