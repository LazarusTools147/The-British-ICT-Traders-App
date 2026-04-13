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

    # --- 1. STATS OVERVIEW & SEPARATED COUNTERS ---
    live_count = len(df[(df['type'] == 'LIVE') & (df['hindsight'] == False)])
    demo_count = len(df[(df['type'] == 'BACKTEST/DEMO') & (df['hindsight'] == False)])
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
        st.metric("LIVE EXECUTIONS", live_count)
        st.metric("DEMO EXECUTIONS", demo_count)
        st.metric("HINDSIGHT STUDIES", hind_count)

    st.divider()

    # --- 2. HORIZONTAL SELECTOR ---
    cal_filter = st.radio(
        "TIMEFRAME", 
        ["All Trades", "By Year", "By Month", "By Week", "By Day"], 
        horizontal=True, label_visibility="collapsed"
    )
    
    f1, f2, f3 = st.columns(3)
    with f1:
        sel_model = st.selectbox("MODEL FILTER", ["ALL MODELS"] + sorted(df['model_name'].unique().tolist()))
    with f2:
        sel_var = st.selectbox("VARIATION FILTER", ["ALL VARIATIONS"] + sorted(df['model_var'].dropna().unique().tolist()))
    with f3:
        sel_res = st.selectbox("RESULT FILTER", ["ALL RESULTS", "WIN", "LOSS", "BE"])

    # --- 3. CORE FILTERING ENGINE ---
    df['date_dt'] = pd.to_datetime(df['date'])
    today = datetime.now().date()
    
    # Filter only applied for Week and Day to keep Year/Month/All expansive
    if cal_filter == "By Week":
        df = df[df['date_dt'].dt.date >= (today - timedelta(days=7))]
    elif cal_filter == "By Day":
        df = df[df['date_dt'].dt.date == today]

    if sel_model != "ALL MODELS": df = df[df['model_name'] == sel_model]
    if sel_var != "ALL VARIATIONS": df = df[df['model_var'] == sel_var]
    if sel_res != "ALL RESULTS": df = df[df['result'] == sel_res]

    # --- 4. THE NESTED FOLDER SYSTEM ---
    # Sorting newest trades first globally
    df = df.sort_values('date_dt', ascending=False)

    if df.empty:
        st.warning("No trades match these filters.")
        return

    # Logic for grouping based on the selector
    if cal_filter in ["All Trades", "By Year"]:
        years = df['date_dt'].dt.year.unique()
        for yr in sorted(years, reverse=True):
            yr_df = df[df['date_dt'].dt.year == yr]
            with st.expander(f"📁 YEAR: {yr} ({len(yr_df)} TRADES)", expanded=True):
                # Nested Month grouping inside Year
                months = yr_df['date_dt'].dt.strftime('%B').unique()
                for mo in months:
                    mo_df = yr_df[yr_df['date_dt'].dt.strftime('%B') == mo]
                    with st.expander(f"📅 {mo.upper()} ({len(mo_df)} TRADES)"):
                        render_trade_list(mo_df, supabase)

    elif cal_filter == "By Month":
        months = df['date_dt'].dt.strftime('%B %Y').unique()
        for mo in months:
            mo_df = df[df['date_dt'].dt.strftime('%B %Y') == mo]
            with st.expander(f"📅 {mo.upper()} ({len(mo_df)} TRADES)", expanded=True):
                render_trade_list(mo_df, supabase)

    else: # Week or Day
        render_trade_list(df, supabase)

def render_trade_list(target_df, supabase):
    """Helper function to render the actual trade cards."""
    for _, row in target_df.iterrows():
        res = row['result']
        color = "#00FF00" if res == "WIN" else "#FF0000" if res == "LOSS" else "#808080"
        icon = "🟢" if res == "WIN" else "🔴" if res == "LOSS" else "🟡"
        header = f"{icon} {row['model_name']} | {row['market']} | {row['date_dt'].strftime('%d %b %Y')} | {round(row['rr'], 2)}R"
        
        with st.expander(header):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"TIME: `{row.get('entry_time', 'N/A')}`")
                st.write(f"SESS: `{row.get('session', 'N/A')}`")
                st.write(f"ENTRY: `{row.get('entry_type', 'N/A')}`")
            with c2:
                st.write(f"TF: `{row.get('entry_tf', 'N/A')}`")
                st.write(f"VAR: `{row.get('model_var', 'N/A')}`")
                st.write(f"DUR: `{row.get('duration_mins', 0)}m`")
            with c3:
                st.write(f"RISK: `{row.get('risk_pc', 0)}%`")
                st.write(f"RESULT: :{color}[**{res}**]")
                st.write(f"MODE: `{'HINDSIGHT' if row['hindsight'] else row['type']}`")
                
                if st.button("🗑️ PURGE", key=f"del_{row['id']}"):
                    supabase.table("trades").delete().eq("id", row['id']).execute()
                    st.rerun()
            
            if row.get('screenshot_text'):
                st.image(f"data:image/png;base64,{row['screenshot_text']}", use_container_width=True)
            
            st.info(f"**NOTES:** {row.get('notes', 'N/A')}")
            st.divider()