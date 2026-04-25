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
        fig.update_layout(showlegend=False, height=180, margin=dict(t=0,b=0,l=0,r=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.write("**ENTRIES**")
        if 'entry_type' in df.columns:
            fig2 = px.pie(df, names='entry_type', hole=0.6)
            fig2.update_layout(showlegend=False, height=180, margin=dict(t=0,b=0,l=0,r=0), paper_bgcolor='rgba(0,0,0,0)')
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
    else:
        render_trade_list(df, supabase)

def render_trade_list(t_df, supabase):
    # Synchronized News Driver List
    news_list = ["NONE", "LOW", "MEDIUM", "HIGH", "NFP", "CPI", "FOMC", "UNEMPLOYMENT CLAIMS", "BANK HOLIDAY", "OTHER"]
    
    try:
        mkt_resp = supabase.table("markets").select("market_name").eq("trader_username", st.session_state.user).execute()
        markets = [r['market_name'] for r in mkt_resp.data]
    except:
        markets = []

    for _, row in t_df.iterrows():
        res = row.get('result', 'BE')
        side = row.get('direction', 'BUY')
        if side not in ["BUY", "SELL"]: side = "BUY"
        
        side_color = "#00FF00" if side == "BUY" else "#FF0000"
        res_color = "#00FF00" if res == "WIN" else "#FF0000" if res == "LOSS" else "#808080"
        header = f"{row.get('model_name')} | {row.get('market')} | {row['date_dt'].strftime('%d %b')} | {round(row.get('rr', 0), 2)}R"
        
        with st.expander(header):
            if st.session_state.get('editing_id') == row['id']:
                with st.form(f"ed_{row['id']}"):
                    st.write("### 🛠️ EDIT MASTER DATA")
                    ec1, ec2, ec3 = st.columns(3)
                    with ec1:
                        # Safety check for date objects
                        try:
                            current_date_val = row['date_dt'].date()
                        except:
                            current_date_val = datetime.now().date()
                        
                        e_date = st.date_input("DATE", value=current_date_val)
                        e_mod = st.text_input("MODEL", value=str(row.get('model_name', '')))
                        e_var = st.text_input("VAR", value=str(row.get('model_var', '')))
                        mkt_idx = markets.index(row['market']) if row['market'] in markets else 0
                        e_mkt = st.selectbox("MKT", markets, index=mkt_idx)
                        e_price = st.number_input("ENTRY PRICE", value=float(row.get('entry_price', 0.0)), format="%.2f")
                    with ec2:
                        e_type = st.text_input("ENTRY", value=str(row.get('entry_type', '')))
                        e_sess = st.text_input("SESS", value=str(row.get('session', '')))
                        e_time = st.text_input("TIME", value=str(row.get('entry_time', '')))
                        e_sl_p = st.number_input("SL PRICE", value=float(row.get('sl_price', 0.0)), format="%.2f")
                        e_tp_p = st.number_input("TP PRICE", value=float(row.get('tp_price', 0.0)), format="%.2f")
                    with ec3:
                        e_res = st.selectbox("RES", ["WIN", "LOSS", "BE"], index=["WIN", "LOSS", "BE"].index(res))
                        e_side = st.selectbox("SIDE", ["BUY", "SELL"], index=["BUY", "SELL"].index(side))
                        e_risk = st.number_input("RISK %", value=float(row.get('risk_pc', 1.0)))
                        e_tar = st.text_input("TARGET", value=str(row.get('target', '')))
                        
                        # Correct index logic for News Driver
                        n_current = row.get('news_impact', 'NONE')
                        if n_current not in news_list: n_current = "NONE"
                        e_news = st.selectbox("NEWS", news_list, index=news_list.index(n_current))

                    st.write("**VOLATILITY RANGES (HANDLES)**")
                    v1, v2, v3, v4, v5 = st.columns(5)
                    e_cbdr = v1.number_input("CBDR", value=float(row.get('cbdr_size') or 0.0), step=0.25)
                    e_asia = v2.number_input("ASIA", value=float(row.get('asia_size') or 0.0), step=0.25)
                    e_lon = v3.number_input("LON", value=float(row.get('london_size') or 0.0), step=0.25)
                    e_am = v4.number_input("NYAM", value=float(row.get('ny_am_size') or 0.0), step=0.25)
                    e_pm = v5.number_input("NYPM", value=float(row.get('ny_pm_size') or 0.0), step=0.25)
                    
                    e_notes = st.text_area("NOTES", value=str(row.get('notes', '')))
                    
                    if st.form_submit_button("💾 SAVE CHANGES"):
                        sl_h = abs(e_price - e_sl_p); tp_h = abs(e_price - e_tp_p); rr = tp_h / sl_h if sl_h != 0 else 0
                        up = {
                            "date": str(e_date), "model_name": e_mod, "model_var": e_var, "market": e_mkt, "entry_price": e_price, "entry_time": e_time,
                            "entry_type": e_type, "session": e_sess, "sl_price": e_sl_p, "tp_price": e_tp_p, "direction": e_side,
                            "result": e_res, "risk_pc": e_risk, "target": e_tar, "notes": e_notes, "news_impact": e_news,
                            "sl_handles": sl_h, "tp_handles": tp_h, "rr": rr, 
                            "cbdr_size": e_cbdr, "asia_size": e_asia, "london_size": e_lon, "ny_am_size": e_am, "ny_pm_size": e_pm
                        }
                        supabase.table("trades").update(up).eq("id", row['id']).execute()
                        st.session_state.editing_id = None; st.rerun()
                
                if st.button("❌ CANCEL", key=f"cn_{row['id']}"): 
                    st.session_state.editing_id = None; st.rerun()
            else:
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.write(f"**ENV:** `{row.get('type')}`"); st.write(f"**VAR:** `{row.get('model_var')}`")
                    st.write(f"**TIME:** `{row.get('entry_time')}`"); st.write(f"**SESS:** `{row.get('session')}`")
                    st.write(f"**SIDE:** :{side_color}[**{side}**]")
                with c2:
                    st.write(f"**ENTRY:** `{row.get('entry_price')}`"); st.write(f"**SL:** `{row.get('sl_price')}`")
                    st.write(f"**TP:** `{row.get('tp_price')}`"); st.write(f"**DUR:** `{row.get('duration_mins')} mins`")
                    st.write(f"**TF:** `{row.get('entry_tf')}`")
                with c3:
                    st.write(f"**RISK:** `{row.get('risk_pc')}%` "); st.write(f"**RESULT:** :{res_color}[**{res}**]")
                    st.write(f"**NEWS:** `{row.get('news_impact')}`"); st.write(f"**HANDLES:** `{round(row.get('tp_handles', 0), 1)}`")
                    st.write(f"**RR:** `{round(row.get('rr', 0), 2)}R`")
                
                st.divider()
                st.write(f"**TYPE:** `{row.get('entry_type')}` | **TARGET:** `{row.get('target')}`")
                
                st.write("**SESSION RANGES:**")
                v_cols = st.columns(5)
                v_data = [("CBDR", 'cbdr_size'), ("ASIA", 'asia_size'), ("LON", 'london_size'), ("AM", 'ny_am_size'), ("PM", 'ny_pm_size')]
                for i, (label, col) in enumerate(v_data):
                    val = row.get(col)
                    if val and val > 0: v_cols[i].caption(f"**{label}:** {val}")

                if row.get('screenshot_text'): st.image(f"data:image/png;base64,{row['screenshot_text']}", use_container_width=True)
                
                if st.button("✏️ EDIT FULL DATA", key=f"eb_{row['id']}"): 
                    st.session_state.editing_id = row['id']; st.rerun()
                
                st.info(f"**NOTES:** {row.get('notes')}"); st.divider()