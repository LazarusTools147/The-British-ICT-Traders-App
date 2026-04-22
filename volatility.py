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
            # 1. CALCULATE HANDLES
            handles = float(abs(v_high - v_low))
            
            # 2. CALCULATE DURATION (SAFE MATH)
            dt_low = datetime.combine(v_date, time_low)
            dt_high = datetime.combine(v_date, time_high)
            diff = abs((dt_high - dt_low).total_seconds() / 60)
            
            # If times are identical or duration is 0, default to 1 to avoid div by zero/errors
            duration_int = int(diff) if diff > 0 else 1
            if duration_int > 720: duration_int = 1440 - duration_int
            
            # 3. CALCULATE VELOCITY
            velocity = round(handles / duration_int, 2)
            
            vol_data = {
                "trader_username": st.session_state.user, 
                "date": str(v_date), 
                "market": v_mkt,
                "session": v_sess, 
                "news_impact": v_news, 
                "high_price": float(v_high), 
                "low_price": float(v_low),
                "direction": v_dir, 
                "handles": handles, 
                "duration_mins": duration_int,
                "time_low": str(time_low), 
                "time_high": str(time_high),
                "notes": f"VEL: {velocity}H/m"
            }
            
            try:
                supabase.table("session_tape").insert(vol_data).execute()
                st.success(f"Archived {v_mkt}: {handles} Handles in {duration_int} mins")
                st.rerun()
            except Exception as e:
                st.error(f"Database Error: {e}")

    # 4. ANALYTICS
    try:
        query = supabase.table("session_tape").select("*").eq("trader_username", st.session_state.user)
        if sidebar_mkt != "ALL MARKETS": query = query.eq("market", sidebar_mkt)
        res = query.execute()
        df = pd.DataFrame(res.data)
    except: df = pd.DataFrame()

    if not df.empty:
        df['date_dt'] = pd.to_datetime(df['date'])
        df['Day'] = df['date_dt'].dt.day_name()
        df['vel'] = df['notes'].apply(lambda x: float(x.split("VEL: ")[1].split("H/m")[0]) if "VEL:" in str(x) else 0.0)

        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            st.write("**Avg Expansion (Handles)**")
            st.bar_chart(df.groupby('session')['handles'].mean())
        with g2:
            st.write("**Speed (H/m) by Day**")
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            st.line_chart(df.groupby('Day')['vel'].mean().reindex(day_order))
            
        st.write("**Velocity vs Delivery Time**")
        fig = px.scatter(df, x='duration_mins', y='handles', size='vel', color='session',
                         labels={'duration_mins': 'Move Time (Mins)', 'handles': 'Handles'},
                         hover_data=['Day', 'news_impact'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Archive empty. Log a session to see DNA.")