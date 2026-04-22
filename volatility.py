import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, time
from database import get_supabase

def render_volatility_tab():
    st.markdown('<h2 style="color: #FF4B4B;">📊 SESSION TAPE ARCHIVE</h2>', unsafe_allow_html=True)
    supabase = get_supabase()

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

    # --- 1. DATA ENTRY FORM ---
    st.write("### 📝 LOG SESSION TAPE")
    with st.form("vol_standalone_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            v_date = st.date_input("DATE", datetime.now())
            v_mkt = st.selectbox("MARKET", markets) if sidebar_mkt == "ALL MARKETS" else sidebar_mkt
            if sidebar_mkt != "ALL MARKETS": st.info(f"Target Market: **{sidebar_mkt}**")
            v_sess = st.selectbox("SESSION", list(session_defaults.keys()))
            v_news = st.selectbox("NEWS DRIVER", ["NONE", "LOW", "MEDIUM", "HIGH", "NFP/CPI"])
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
            handles = float(abs(v_high - v_low))
            dt_low = datetime.combine(v_date, time_low)
            dt_high = datetime.combine(v_date, time_high)
            diff = abs((dt_high - dt_low).total_seconds() / 60)
            duration_int = int(diff) if diff > 0 else 1
            if duration_int > 720: duration_int = 1440 - duration_int
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
            except Exception as e: st.error(f"Database Error: {e}")

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
        df['DayNum'] = df['date_dt'].dt.day
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

        # --- 3. CALENDAR LIST & EDITOR ---
        st.divider()
        st.write("### 📜 TAPE HISTORY")
        
        for yr in sorted(df['Year'].unique(), reverse=True):
            with st.expander(f"📁 YEAR: {yr}", expanded=False):
                yr_df = df[df['Year'] == yr]
                # Sort months correctly using datetime
                months = sorted(yr_df['date_dt'].dt.month.unique(), reverse=True)
                for m_num in months:
                    mo_df = yr_df[yr_df['date_dt'].dt.month == m_num]
                    mo_name = mo_df['Month'].iloc[0].upper()
                    with st.expander(f"📅 MONTH: {mo_name}"):
                        # Group by actual Day
                        days = sorted(mo_df['date_dt'].dt.date.unique(), reverse=True)
                        for d_date in days:
                            d_df = mo_df[mo_df['date_dt'].dt.date == d_date]
                            d_name = d_date.strftime('%A %d').upper()
                            with st.expander(f"📍 DAY: {d_name} ({len(d_df)} Sessions)"):
                                for _, row in d_df.iterrows():
                                    h_color = "#00FF00" if "BULLISH" in row['direction'] else "#FF0000" if "BEARISH" in row['direction'] else "#808080"
                                    label = f"{row['session']} | {row['market']} | {row['handles']}H"
                                    
                                    with st.expander(label):
                                        if st.session_state.get('editing_tape_id') == row['id']:
                                            with st.form(f"edit_tape_{row['id']}"):
                                                ec1, ec2 = st.columns(2)
                                                e_date = ec1.date_input("DATE", value=row['date_dt'].date())
                                                e_mkt = ec1.selectbox("MARKET", markets, index=markets.index(row['market']) if row['market'] in markets else 0)
                                                e_sess = ec1.selectbox("SESSION", list(session_defaults.keys()), index=list(session_defaults.keys()).index(row['session']))
                                                e_news = ec1.selectbox("NEWS", ["NONE", "LOW", "MEDIUM", "HIGH", "NFP", "BANK HOLIDAY", "FOMC", "UNEMPLOYMENT CLAIMS" "OTHER" ], index=["NONE", "LOW", "MEDIUM", "HIGH", "NFP/CPI"].index(row['news_impact']))
                                                
                                                e_high = ec2.number_input("HIGH", value=float(row['high_price']), format="%.2f")
                                                e_low = ec2.number_input("LOW", value=float(row['low_price']), format="%.2f")
                                                e_dir = ec2.selectbox("DIRECTION", ["LOW TO HIGH (BULLISH)", "HIGH TO LOW (BEARISH)", "CONSOLIDATION"], index=["LOW TO HIGH (BULLISH)", "HIGH TO LOW (BEARISH)", "CONSOLIDATION"].index(row['direction']))
                                                
                                                t_low_obj = datetime.strptime(row['time_low'], "%H:%M:%S").time() if row['time_low'] else time(8,0)
                                                t_high_obj = datetime.strptime(row['time_high'], "%H:%M:%S").time() if row['time_high'] else time(10,0)
                                                e_tlow = ec2.time_input("TIME LOW", value=t_low_obj)
                                                e_thigh = ec2.time_input("TIME HIGH", value=t_high_obj)

                                                if st.form_submit_button("💾 UPDATE TAPE"):
                                                    h = float(abs(e_high - e_low))
                                                    d = int(abs((datetime.combine(e_date, e_thigh) - datetime.combine(e_date, e_tlow)).total_seconds() / 60))
                                                    if d == 0: d = 1
                                                    v = round(h/d, 2)
                                                    up = {
                                                        "date": str(e_date), "market": e_mkt, "session": e_sess, 
                                                        "news_impact": e_news, "high_price": e_high, "low_price": e_low,
                                                        "direction": e_dir, "handles": h, "duration_mins": d,
                                                        "time_low": str(e_tlow), "time_high": str(e_thigh), "notes": f"VEL: {v}H/m"
                                                    }
                                                    supabase.table("session_tape").update(up).eq("id", row['id']).execute()
                                                    st.session_state.editing_tape_id = None; st.rerun()
                                            if st.button("❌ CANCEL", key=f"can_{row['id']}"):
                                                st.session_state.editing_tape_id = None; st.rerun()
                                        else:
                                            c1, c2, c3 = st.columns(3)
                                            c1.write(f"**BIAS:** :{h_color}[{row['direction']}]")
                                            c1.write(f"**NEWS:** `{row['news_impact']}`")
                                            c2.write(f"**HIGH:** `{row['high_price']}`")
                                            c2.write(f"**LOW:** `{row['low_price']}`")
                                            c3.write(f"**DURATION:** `{row['duration_mins']} mins`")
                                            c3.write(f"**VELOCITY:** `{row['notes']}`")
                                            
                                            if st.button("✏️ EDIT ENTRY", key=f"ed_btn_{row['id']}"):
                                                st.session_state.editing_tape_id = row['id']; st.rerun()
    else:
        st.info("Archive empty. Log a session to see DNA.")