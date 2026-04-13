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
    
    if cal_filter == "By Week":
        df = df[df['date_dt'].dt.date >= (today - timedelta(days=7))]
    elif cal_filter == "By Day":
        df = df[df['date_dt'].dt.date == today]

    if sel_model != "ALL MODELS": df = df[df['model_name'] == sel_model]
    if sel_var != "ALL VARIATIONS": df = df[df['model_var'] == sel_var]
    if sel_res != "ALL RESULTS": df = df[df['result'] == sel_res]

    df = df.sort_values('date_dt', ascending=False)
    if df.empty:
        st.warning("No trades match these filters.")
        return

    # --- 4. THE NESTED FOLDER SYSTEM ---
    if cal_filter in ["All Trades", "By Year"]:
        years = df['date_dt'].dt.year.unique()
        for yr in sorted(years, reverse=True):
            yr_df = df[df['date_dt'].dt.year == yr]
            with st.expander(f"📁 YEAR: {yr} ({len(yr_df)} TRADES)", expanded=True):
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
    else:
        render_trade_list(df, supabase)

def render_trade_list(target_df, supabase):
    for _, row in target_df.iterrows():
        res = row['result']
        color = "#00FF00" if res == "WIN" else "#FF0000" if res == "LOSS" else "#808080"
        icon = "🟢" if res == "WIN" else "🔴" if res == "LOSS" else "🟡"
        header = f"{icon} {row['model_name']} | {row['market']} | {row['date_dt'].strftime('%d %b %Y')} | {round(row['rr'], 2)}R"
        
        with st.expander(header):
            if st.session_state.get('editing_id') == row['id']:
                # --- START OF MASTER EDIT FORM ---
                with st.form(f"master_edit_form_{row['id']}"):
                    st.markdown("### 🛠️ EDIT MASTER TRADE DATA")
                    ec1, ec2, ec3 = st.columns(3)
                    with ec1:
                        e_mod = st.text_input("MODEL NAME", value=row['model_name']).upper()
                        e_var = st.text_input("VARIATION", value=row.get('model_var', '')).upper()
                        e_mkt = st.text_input("MARKET", value=row['market']).upper()
                        e_tf = st.text_input("TIMEFRAME", value=row.get('entry_tf', '')).upper()
                    with ec2:
                        e_type = st.text_input("ENTRY TYPE", value=row.get('entry_type', '')).upper()
                        e_sess = st.text_input("SESSION", value=row.get('session', '')).upper()
                        e_time = st.text_input("ENTRY TIME", value=row.get('entry_time', ''))
                        n_list = ["NONE", "LOW", "MEDIUM", "HIGH", "NFP/CPI"]
                        curr_news = row.get('news_impact', 'NONE')
                        e_news = st.selectbox("NEWS IMPACT", n_list, index=n_list.index(curr_news) if curr_news in n_list else 0)
                    with ec3:
                        e_res = st.selectbox("RESULT", ["WIN", "LOSS", "BE"], index=["WIN", "LOSS", "BE"].index(res))
                        e_risk = st.number_input("RISK %", value=float(row.get('risk_pc', 1.0)))
                        e_dur = st.number_input("DURATION (MINS)", value=int(row.get('duration_mins', 15)))
                        e_tp = st.number_input("TP HANDLES", value=float(row.get('tp_handles', 0.0)))
                        e_sl = st.number_input("SL HANDLES", value=float(row.get('sl_handles', 1.0)))
                    
                    e_notes = st.text_area("CONFLUENCE NOTES", value=row['notes'], height=150)
                    
                    # MANDATORY SUBMIT BUTTON - MUST BE INSIDE st.form()
                    if st.form_submit_button("💾 UPDATE ALL RECORDS & SYNC"):
                        new_rr = e_tp / e_sl if e_sl != 0 else 0
                        update_data = {
                            "model_name": e_mod, "model_var": e_var, "market": e_mkt, "entry_tf": e_tf,
                            "entry_type": e_type, "session": e_sess, "entry_time": e_time,
                            "news_impact": e_news, "result": e_res, "risk_pc": e_risk,
                            "duration_mins": e_dur, "notes": e_notes, "tp_handles": e_tp,
                            "sl_handles": e_sl, "rr": new_rr
                        }
                        supabase.table("trades").update(update_data).eq("id", row['id']).execute()
                        st.session_state.editing_id = None
                        st.rerun()

                # Cancel button is OUTSIDE the form block
                if st.button("❌ CANCEL", key=f"cancel_{row['id']}"):
                    st.session_state.editing_id = None
                    st.rerun()
                # --- END OF MASTER EDIT FORM ---
            else:
                # --- DISPLAY MODE ---
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.write(f"TIME: `{row.get('entry_time', 'N/A')}`")
                    st.write(f"SESS: `{row.get('session', 'N/A')}`")
                    st.write(f"ENTRY: `{row.get('entry_type', 'N/A')}`")
                    st.write(f"NEWS: `{row.get('news_impact', 'NONE')}`")
                with c2:
                    st.write(f"TF: `{row.get('entry_tf', 'N/A')}`")
                    st.write(f"VAR: `{row.get('model_var', 'N/A')}`")
                    st.write(f"DUR: `{row.get('duration_mins', 0)}m`")
                with c3:
                    st.write(f"RISK: `{row.get('risk_pc', 0)}%`")
                    st.write(f"RESULT: :{color}[**{res}**]")
                    mode_text = "HINDSIGHT" if row.get('hindsight') else row.get('type', 'LIVE')
                    st.write(f"MODE: `{mode_text}`")
                    
                    if st.button("🗑️ PURGE", key=f"del_{row['id']}"):
                        supabase.table("trades").delete().eq("id", row['id']).execute()
                        st.rerun()
                
                if row.get('screenshot_text'):
                    st.image(f"data:image/png;base64,{row['screenshot_text']}", use_container_width=True)
                
                if st.button("✏️ EDIT FULL DATA", key=f"edit_btn_{row['id']}"):
                    st.session_state.editing_id = row['id']
                    st.rerun()

                st.info(f"**CONFLUENCE NOTES:**\n\n{row.get('notes', 'N/A')}")
                st.divider()