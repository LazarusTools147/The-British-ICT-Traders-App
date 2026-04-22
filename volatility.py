import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, time
from database import get_supabase

def render_volatility_tab():
    st.markdown('<h2 style="color: #FF4B4B;">📊 SESSION TAPE ARCHIVE</h2>', unsafe_allow_html=True)
    supabase = get_supabase()

    # --- 0. INITIALIZE STICKY SETTINGS ---
    if 'last_v_date' not in st.session_state: st.session_state.last_v_date = datetime.now()
    if 'last_v_mkt' not in st.session_state: st.session_state.last_v_mkt = "NQ"
    if 'last_v_sess' not in st.session_state: st.session_state.last_v_sess = "LONDON (12am-6am)"
    if 'last_v_news' not in st.session_state: st.session_state.last_v_news = "NONE"

    try:
        mkt_resp = supabase.table("markets").select("market_name").eq("trader_username", st.session_state.user).execute()
        markets = [r['market_name'] for r in mkt_resp.data]
    except: markets = []

    sidebar_mkt = st.session_state.get('active_market', 'ALL MARKETS')

    session_defaults = {
        "CBDR (4pm-8pm)": time(16, 0),
        "ASIA (8pm-12am)": time(20, 0),
        "LONDON (12am-6am)": time(0, 0),
        "NY AM (7am-12pm)": time(7, 0),
        "NY PM (12pm-4pm)": time(12, 0)
    }

    # --- 1. DATA ENTRY FORM (STICKY) ---
    st.write("### 📝 LOG SESSION TAPE")
    with st.form("vol_standalone_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            v_date = st.date_input("DATE", value=st.session_state.last_v_date)
            if sidebar_mkt == "ALL MARKETS":
                m_idx = markets.index(st.session_state.last_v_mkt) if st.session_state.last_v_mkt in markets else 0
                v_mkt = st.selectbox("MARKET", markets, index=m_idx)
            else:
                st.info(f"Target Market: **{sidebar_mkt}**")
                v_mkt = sidebar_mkt
            
            s_idx = list(session_defaults.keys()).index(st.session_state.last_v_sess) if st.session_state.last_v_sess in session_defaults else 0
            v_sess = st.selectbox("SESSION", list(session_defaults.keys()), index=s_idx)
            
            n_list = ["NONE", "LOW", "MEDIUM", "HIGH", "NFP", "CPI", "FOMC", "UNEMPLOYMENT CLAIMS", "BANK HOLIDAY", "OTHER"]
            n_idx = n_list.index(st.session_state.last_v_news) if st.session_state.last_v_news in n_list else 0
            v_news = st.selectbox("NEWS DRIVER", n_list, index=n_idx)
        
        with c2:
            v_high = st.number_input("SESSION HIGH PRICE", value=0.0, format="%.2f")
            v_low = st.number_input("SESSION LOW PRICE", value=0.0, format="%.2f")
            v_dir = st.selectbox("DELIVERY DIRECTION", ["LOW TO HIGH (BULLISH)", "HIGH TO LOW (BEARISH)", "CONSOLIDATION"])

        st.divider()
        st.write("**TIME OF PEAK/TROUGH (NY TIME)**")
        t1, t2 = st.columns(2)
        time_low = t1.time_input("TIME OF LOW", value=session_defaults[v_sess])
        time_high = t2.time_input("TIME OF HIGH", value=session_defaults[v_sess])

        if st.form_submit_button("📥 ARCHIVE SESSION TAPE"):
            st.session_state.last_v_date = v_date
            st.session_state.last_v_mkt = v_mkt
            st.session_state.last_v_sess = v_sess
            st.session_state.last_v_news = v_news

            handles = float(abs(v_high - v_low))
            dt1 = datetime.combine(v_date, time_low)
            dt2 = datetime.combine(v_date, time_high)
            delta = abs((dt2 - dt1).total_seconds() / 60)
            if delta > 720: delta = 1440 - delta
            duration_int = int(delta) if delta > 0 else 1
            velocity = round(handles / duration_int, 2)
            
            vol_data = {
                "trader_username": st.session_state.user, "date": str(v_date), "market": v_mkt,
                "session": v_sess, "news_impact": v_news, "high_price": float(v_high), 
                "low_price": float(v_low), "direction": v_dir, "handles": handles, 
                "duration_mins": duration_int, "time_low": str(time_low), 
                "time_high": str(time_high), "notes": f"VEL: {velocity}H/m"
            }
            try:
                supabase.table("session_tape").insert(vol_data).execute()
                st.success(f"Archived {v_mkt}: {handles} Handles"); st.rerun()
            except Exception as e: st.error(f"Error: {e}")

    # --- 2. ANALYTICS ---
    try:
        query = supabase.table("session_tape").select("*").eq("trader_username", st.session_state.user)
        if sidebar_mkt != "ALL MARKETS": query = query.eq("market", sidebar_mkt)
        res = query.execute()
        df = pd.DataFrame(res.data)
    except: df = pd.DataFrame()

    if not df.empty:
        df['date_dt'] = pd.to_datetime(df['date'])
        df['DayName'] = df['date_dt'].dt.day_name()
        df['Year'] = df['date_dt'].dt.year
        df['Month'] = df['date_dt'].dt.strftime('%B')
        df['vel'] = df['notes'].apply(lambda x: float(x.split("VEL: ")[1].split("H/m")[0]) if "VEL:" in str(x) else 0.0)

        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            st.write("**Avg Expansion (Handles)**")
            st.bar_chart(df.groupby('session')['handles'].mean())
        with g2:
            st.write("**Speed (H/m) by Day**")
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            st.line_chart(df.groupby('DayName')['vel'].mean().reindex(day_order))
            
        st.write("**Velocity vs Delivery Time**")
        fig = px.scatter(df, x='duration_mins', y='handles', size='vel', color='session',
                         labels={'duration_mins': 'Move Time (Mins)', 'handles': 'Handles'},
                         hover_data=['DayName', 'news_impact'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

        # --- 3. CALENDAR LIST & FULL EDITOR ---
        st.divider()
        st.write("### 📜 TAPE HISTORY")
        for yr in sorted(df['Year'].unique(), reverse=True):
            with st.expander(f"📁 YEAR: {yr}"):
                yr_df = df[df['Year'] == yr]
                months = sorted(yr_df['date_dt'].dt.month.unique(), reverse=True)
                for m_num in months:
                    mo_df = yr_df[yr_df['date_dt'].dt.month == m_num]
                    mo_name = mo_df['Month'].iloc[0].upper()
                    with st.expander(f"📅 MONTH: {mo_name}"):
                        days = sorted(mo_df['date_dt'].dt.date.unique(), reverse=True)
                        for d_date in days:
                            d_df = mo_df[mo_df['date_dt'].dt.date == d_date]
                            d_name = d_date.strftime('%A %d').upper()
                            with st.expander(f"📍 DAY: {d_name}"):
                                for _, row in d_df.iterrows():
                                    h_color = "#00FF00" if "BULLISH" in row['direction'] else "#FF0000" if "BEARISH" in row['direction'] else "#808080"
                                    with st.expander(f"{row['session']} | {row['market']} | {row['handles']}H"):
                                        if st.session_state.get('editing_tape_id') == row['id']:
                                            with st.form(f"edit_tape_{row['id']}"):
                                                ec1, ec2 = st.columns(2)
                                                e_date = ec1.date_input("DATE", value=row['date_dt'].date())
                                                e_mkt = ec1.selectbox("MARKET", markets, index=markets.index(row['market']) if row['market'] in markets else 0)
                                                e_sess = ec1.selectbox("SESSION", list(session_defaults.keys()), index=list(session_defaults.keys()).index(row['session']))
                                                e_news = ec1.selectbox("NEWS", n_list, index=n_list.index(row['news_impact']) if row['news_impact'] in n_list else 0)
                                                
                                                e_high = ec2.number_input("HIGH", value=float(row['high_price']), format="%.2f")
                                                e_low = ec2.number_input("LOW", value=float(row['low_price']), format="%.2f")
                                                e_dir = ec2.selectbox("DIRECTION", ["LOW TO HIGH (BULLISH)", "HIGH TO LOW (BEARISH)", "CONSOLIDATION"], index=["LOW TO HIGH (BULLISH)", "HIGH TO LOW (BEARISH)", "CONSOLIDATION"].index(row['direction']))
                                                
                                                try: t_low_obj = datetime.strptime(row['time_low'], "%H:%M:%S").time()
                                                except: t_low_obj = time(8,0)
                                                try: t_high_obj = datetime.strptime(row['time_high'], "%H:%M:%S").time()
                                                except: t_high_obj = time(10,0)
                                                
                                                e_tlow = ec2.time_input("TIME LOW", value=t_low_obj)
                                                e_thigh = ec2.time_input("TIME HIGH", value=t_high_obj)

                                                if st.form_submit_button("💾 UPDATE TAPE"):
                                                    h = float(abs(e_high - e_low))
                                                    dt_e1 = datetime.combine(e_date, e_tlow)
                                                    dt_e2 = datetime.combine(e_date, e_thigh)
                                                    d_delta = abs((dt_e2 - dt_e1).total_seconds() / 60)
                                                    if d_delta > 720: d_delta = 1440 - d_delta
                                                    d_final = int(d_delta) if d_delta > 0 else 1
                                                    v = round(h/d_final, 2)
                                                    up = {
                                                        "date": str(e_date), "market": e_mkt, "session": e_sess, "news_impact": e_news,
                                                        "high_price": e_high, "low_price": e_low, "direction": e_dir,
                                                        "handles": h, "duration_mins": d_final, "time_low": str(e_tlow),
                                                        "time_high": str(e_thigh), "notes": f"VEL: {v}H/m"
                                                    }
                                                    supabase.table("session_tape").update(up).eq("id", row['id']).execute()
                                                    st.session_state.editing_tape_id = None; st.rerun()
                                            if st.button("❌ CANCEL", key=f"can_{row['id']}"):
                                                st.session_state.editing_tape_id = None; st.rerun()
                                        else:
                                            st.write(f"**BIAS:** :{h_color}[{row['direction']}] | **NEWS:** `{row['news_impact']}`")
                                            st.write(f"**DELIVERY:** {row['duration_mins']} mins | **VELOCITY:** {row['notes']}")
                                            if st.button("✏️ EDIT", key=f"ed_{row['id']}"):
                                                st.session_state.editing_tape_id = row['id']; st.rerun()
    else:
        st.info("Archive empty.")