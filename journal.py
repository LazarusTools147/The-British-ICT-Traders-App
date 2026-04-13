import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from database import get_supabase

def render_journal_tab():
    st.markdown('<h2 style="color: #FF4B4B;">📓 THE JOURNAL</h2>', unsafe_allow_html=True)
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

    # --- 1. STATS OVERVIEW & COUNTERS ---
    # Fact-check: Adding specific counts for Live, Demo, and Hindsight as requested.
    live_count = len(df[df['type'] == 'LIVE'])
    demo_count = len(df[df['type'] == 'BACKTEST/DEMO'])
    hind_count = len(df[df['hindsight'] == True])

    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("**MODEL DISTRIBUTION**")
        fig_mod = px.pie(df, names='model_name', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_mod.update_layout(showlegend=False, height=180, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_mod, use_container_width=True, key="journal_model_donut")
    with c2:
        st.write("**ENTRY TYPES**")
        if 'entry_type' in df.columns and not df['entry_type'].dropna().empty:
            fig_ent = px.pie(df, names='entry_type', hole=0.6, color_discrete_sequence=px.colors.qualitative.Bold)
            fig_ent.update_layout(showlegend=False, height=180, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_ent, use_container_width=True, key="journal_entry_donut")
    with c3:
        st.metric("LIVE TRADES", live_count)
        st.metric("DEMO TRADES", demo_count)
        st.metric("HINDSIGHT", hind_count)

    st.divider()

    # --- 2. HORIZONTAL CALENDAR & FILTERS ---
    cal_filter = st.radio(
        "TIMEFRAME", 
        ["All Trades", "By Year", "By Month", "By Week", "By Day"], 
        horizontal=True, label_visibility="collapsed"
    )
    
    f1, f2, f3 = st.columns(3)
    with f1:
        sel_model = st.selectbox("MODEL", ["ALL MODELS"] + sorted(df['model_name'].unique().tolist()))
    with f2:
        sel_var = st.selectbox("VARIATION", ["ALL VARIATIONS"] + sorted(df['model_var'].dropna().unique().tolist()))
    with f3:
        sel_res = st.selectbox("RESULT", ["ALL RESULTS", "WIN", "LOSS", "BE"])

    # --- 3. FILTERING LOGIC ---
    df['date'] = pd.to_datetime(df['date']).dt.date # Strip time for clean comparison
    today = datetime.now().date()
    
    if cal_filter == "By Year": df = df[pd.to_datetime(df['date']).dt.year == today.year]
    elif cal_filter == "By Month": df = df[pd.to_datetime(df['date']).dt.month == today.month]
    elif cal_filter == "By Week": df = df[df['date'] >= (today - timedelta(days=7))]
    elif cal_filter == "By Day": df = df[df['date'] == today]

    if sel_model != "ALL MODELS": df = df[df['model_name'] == sel_model]
    if sel_var != "ALL VARIATIONS": df = df[df['model_var'] == sel_var]
    if sel_res != "ALL RESULTS": df = df[df['result'] == sel_res]

    # --- 4. GROUPING SYSTEM (THE FOLDERS) ---
    # We group by the chosen timeframe to create the dropdown headers you asked for
    if cal_filter == "By Year" or cal_filter == "All Trades":
        df['group'] = pd.to_datetime(df['date']).dt.strftime('%Y')
    elif cal_filter == "By Month":
        df['group'] = pd.to_datetime(df['date']).dt.strftime('%B %Y')
    elif cal_filter == "By Week":
        df['group'] = "Last 7 Days"
    else:
        df['group'] = "Today's Executions"

    groups = df['group'].unique()
    for group in groups:
        group_df = df[df['group'] == group].sort_values('date', ascending=False)
        with st.expander(f"📁 {group.upper()} ({len(group_df)} TRADES)", expanded=True):
            for _, row in group_df.iterrows():
                res = row['result']
                color = "#00FF00" if res == "WIN" else "#FF0000" if res == "LOSS" else "#808080"
                header = f"{row['model_name']} | {row['market']} | {row['date']} | {round(row['rr'], 2)}R"
                
                with st.container():
                    st.markdown(f"**{header}**")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.write(f"TIME: `{row.get('entry_time', 'N/A')}`")
                        st.write(f"SESS: `{row.get('session', 'N/A')}`")
                        st.write(f"ENTRY: `{row.get('entry_type', 'N/A')}`")
                    with c2:
                        st.write(f"TF: `{row.get('entry_tf', 'N/A')}`")
                        st.write(f"TP: `{row.get('tp_handles', 0)}` handles")
                        st.write(f"SL: `{row.get('sl_handles', 0)}` handles")
                    with c3:
                        st.write(f"RISK: `{row.get('risk_pc', 0)}%`")
                        st.write(f"RESULT: :{color}[**{res}**]")
                        if st.button("🗑️ PURGE", key=f"del_{row['id']}"):
                            supabase.table("trades").delete().eq("id", row['id']).execute()
                            st.rerun()
                    
                    if row.get('screenshot_text'):
                        st.image(f"data:image/png;base64,{row['screenshot_text']}", use_container_width=True)
                    
                    if st.button("✏️ EDIT", key=f"edit_{row['id']}"):
                        st.session_state.editing_id = row['id']
                    
                    if st.session_state.get('editing_id') == row['id']:
                        with st.form(f"f_{row['id']}"):
                            n_notes = st.text_area("Notes", value=row['notes'])
                            if st.form_submit_button("SAVE"):
                                supabase.table("trades").update({"notes": n_notes}).eq("id", row['id']).execute()
                                st.session_state.editing_id = None
                                st.rerun()
                    st.divider()