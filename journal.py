import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
from database import get_supabase

def render_journal_tab():
    st.markdown('<h2 style="color: #FF4B4B;">📓 THE JOURNAL</h2>', unsafe_allow_html=True)
    supabase = get_supabase()
    try:
        response = supabase.table("trades").select("*").eq("trader_username", st.session_state.user).execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error: {e}"); return
    if df.empty:
        st.info("Vault empty."); return
    live_c = len(df[(df.get('type') == 'LIVE') & (df.get('hindsight') == False)])
    demo_c = len(df[(df.get('type') == 'BACKTEST/DEMO') & (df.get('hindsight') == False)])
    hind_c = len(df[df.get('hindsight') == True])
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("**MODELS**")
        fig = px.pie(df, names='model_name', hole=0.6)
        fig.update_layout(showlegend=False, height=180, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.write("**ENTRIES**")
        if 'entry_type' in df.columns:
            fig2 = px.pie(df, names='entry_type', hole=0.6)
            fig2.update_layout(showlegend=False, height=180, margin=dict(t=0,b=0,l=0,r=0))
            st.plotly_chart(fig2, use_container_width=True)
    with c3:
        st.metric("LIVE", live_c); st.metric("DEMO", demo_c); st.metric("STUDY", hind_c)
    st.divider()
    cal = st.radio("TF", ["All Trades", "By Year", "By Month", "By Week", "By Day"], horizontal=True, label_visibility="collapsed")
    f1, f2, f3 = st.columns(3)
    with f1: s_mod = st.selectbox("MODEL", ["ALL"] + sorted(df['model_name'].unique().tolist()))
    with f2: s_var = st.selectbox("VAR", ["ALL"] + sorted(df.get('model_var', pd.Series(['ALL'])).dropna().unique().tolist()))
    with f3: s_res = st.selectbox("RES", ["ALL", "WIN", "LOSS", "BE"])
    df['date_dt'] = pd.to_datetime(df['date'])
    tday = datetime.now().date()
    if cal == "By Week": df = df[df['date_dt'].dt.date >= (tday - timedelta(days=7))]
    elif cal == "By Day": df = df[df['date_dt'].dt.date == tday]
    if s_mod != "ALL": df = df[df['model_name'] == s_mod]
    if s_res != "ALL": df = df[df['result'] == s_res]
    df = df.sort_values('date_dt', ascending=False)
    if cal in ["All Trades", "By Year"]:
        for yr in sorted(df['date_dt'].dt.year.unique(), reverse=True):
            yr_df = df[df['date_dt'].dt.year == yr]
            with st.expander(f"📁 YEAR: {yr} ({len(yr_df)})", expanded=True):
                for mo in yr_df['date_dt'].dt.strftime('%B').unique():
                    mo_df = yr_df[yr_df['date_dt'].dt.strftime('%B') == mo]
                    with st.expander(f"📅 {mo.upper()} ({len(mo_df)})"):
                        render_trade_list(mo_df, supabase)
    elif cal == "By Month":
        for mo in df['date_dt'].dt.strftime('%B %Y').unique():
            mo_df = df[df['date_dt'].dt.strftime('%B %Y') == mo]
            with st.expander(f"📅 {mo.upper()} ({len(mo_df)})", expanded=True):
                render_trade_list(mo_df, supabase)
    else: render_trade_list(df, supabase)

def render_trade_list(t_df, supabase):
    for _, row in t_df.iterrows():
        res = row.get('result', 'BE')
        color = "#00FF00" if res == "WIN" else "#FF0000" if res == "LOSS" else "#808080"
        header = f"{row.get('model_name')} | {row.get('market')} | {row['date_dt'].strftime('%d %b')} | {round(row.get('rr', 0), 2)}R"
        with st.expander(header):
            if st.session_state.get('editing_id') == row['id']:
                with st.form(f"ed_{row['id']}"):
                    st.write("### 🛠️ EDIT")
                    ec1, ec2, ec3 = st.columns(3)
                    with ec1:
                        e_date = st.date_input("DATE", value=row['date_dt'].date())
                        e_mod = st.text_input("MODEL", value=str(row.get('model_name', '')))
                        e_var = st.text_input("VAR", value=str(row.get('model_var', '')))
                        e_mkt = st.text_input("MKT", value=str(row.get('market', '')))
                        e_tf = st.text_input("TF", value=str(row.get('entry_tf', '')))
                    with ec2:
                        e_type = st.text_input("ENTRY", value=str(row.get('entry_type', '')))
                        e_sess = st.text_input("SESS", value=str(row.get('session', '')))
                        e_time = st.text_input("TIME", value=str(row.get('entry_time', '')))
                        n_l = ["NONE", "LOW", "MEDIUM", "HIGH", "NFP/CPI"]
                        e_news = st.selectbox("NEWS", n_l, index=n_l.index(row.get('news_impact', 'NONE')) if row.get('news_impact') in n_l else 0)
                    with ec3:
                        e_res = st.selectbox("RES", ["WIN", "LOSS", "BE"], index=["WIN", "LOSS", "BE"].index(res))
                        e_risk = st.number_input("RISK %", value=float(row.get('risk_pc', 1.0)))
                        e_dur = st.number_input("DUR", value=int(row.get('duration_mins', 15)))
                        e_tp = st.number_input("TP", value=float(row.get('tp_handles', 0.0)))
                        e_sl = st.number_input("SL", value=float(row.get('sl_handles', 1.0)))
                    e_notes = st.text_area("NOTES", value=str(row.get('notes', '')))
                    if st.form_submit_button("💾 SAVE"):
                        rr = e_tp / e_sl if e_sl != 0 else 0
                        up = {"date": str(e_date),"model_name": e_mod, "model_var": e_var, "market": e_mkt, "entry_tf": e_tf, "entry_type": e_type, "session": e_sess, "entry_time": e_time, "news_impact": e_news, "result": e_res, "risk_pc": e_risk, "duration_mins": e_dur, "notes": e_notes, "tp_handles": e_tp, "sl_handles": e_sl, "rr": rr}
                        supabase.table("trades").update(up).eq("id", row['id']).execute()
                        st.session_state.editing_id = None; st.rerun()
                if st.button("❌ CANCEL", key=f"cn_{row['id']}"):
                    st.session_state.editing_id = None; st.rerun()
            else:
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.write(f"TIME: `{row.get('entry_time')}`"); st.write(f"SESS: `{row.get('session')}`")
                    st.write(f"ENTRY: `{row.get('entry_type')}`"); st.write(f"NEWS: `{row.get('news_impact')}`")
                with c2:
                    st.write(f"TF: `{row.get('entry_tf')}`"); st.write(f"VAR: `{row.get('model_var')}`")
                    st.write(f"DUR: `{row.get('duration_mins')}m`")
                with c3:
                    st.write(f"RISK: `{row.get('risk_pc')}%` "); st.write(f"RESULT: :{color}[**{res}**]")
                    if st.button("🗑️ PURGE", key=f"p_{row['id']}"):
                        supabase.table("trades").delete().eq("id", row['id']).execute(); st.rerun()
                if row.get('screenshot_text'): st.image(f"data:image/png;base64,{row['screenshot_text']}", use_container_width=True)
                if st.button("✏️ EDIT FULL DATA", key=f"eb_{row['id']}"):
                    st.session_state.editing_id = row['id']; st.rerun()
                st.info(f"**NOTES:** {row.get('notes')}"); st.divider()