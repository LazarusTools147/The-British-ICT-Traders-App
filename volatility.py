import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, time
from database import get_supabase

def render_volatility_tab():
    st.markdown('<h2 style="color: #FF4B4B;">📊 SESSION TAPE ARCHIVE</h2>', unsafe_allow_html=True)
    supabase = get_supabase()

    active_mkt = st.session_state.get('active_market', 'ALL MARKETS')
    if active_mkt == 'ALL MARKETS':
        st.warning("⚠️ Please select a specific Market in the sidebar to log tape data.")
        return

    # 1. DEFINE SESSION BOUNDARIES (NY TIME)
    session_defaults = {
        "CBDR (4pm-8pm)": time(16, 0),
        "ASIA (8pm-12am)": time(20, 0),
        "LONDON (12am-6am)": time(0, 0),
        "NY AM (7am-12pm)": time(7, 0),
        "NY PM (12pm-4pm)": time(12, 0)
    }

    # 2. DATA ENTRY FORM
    st.write(f"### 📝 LOG {active_mkt} SESSION TAPE")
    with st.form("vol_standalone_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            v_date = st.date_input("DATE", datetime.now())
            v_sess = st.selectbox("SESSION", list(session_defaults.keys()))
            v_news = st.selectbox("NEWS DRIVER", ["NONE", "LOW", "MEDIUM", "HIGH", "NFP/CPI"])
        with c2:
            v_high = st.number_input("SESSION HIGH PRICE", value=0.0, format="%.2f")
            v_low = st.number_input("SESSION LOW PRICE", value=0.0, format="%.2f")
            v_dir = st.selectbox("DELIVERY DIRECTION", ["LOW TO HIGH (BULLISH)", "HIGH TO LOW (BEARISH)", "CONSOLIDATION"])

        st.divider()
        st.write("**TIME OF PEAK/TROUGH (NY TIME)**")
        t1, t2 = st.columns(2)
        
        # Defaulting start time to the session open you provided
        time_low = t1.time_input("TIME OF LOW", value=session_defaults[v_sess])
        time_high = t2.time_input("TIME OF HIGH", value=session_defaults[v_sess])

        if st.form_submit_button("📥 ARCHIVE SESSION TAPE"):
            # MATH ENGINE
            handles = abs(v_high - v_low)
            
            # Smart Time Delta (Handles Midnight Crossovers)
            dt_low = datetime.combine(v_date, time_low)
            dt_high = datetime.combine(v_date, time_high)
            
            diff = dt_high - dt_low
            duration = abs(diff.total_seconds() / 60)
            
            # If duration > 720 mins (12 hours), it's likely a midnight crossover error, 
            # we subtract from 24 hours to get the real duration
            if duration > 720: 
                duration = 1440 - duration
            
            velocity = round(handles / duration, 2) if duration > 0 else 0
            
            vol_data = {
                "trader_username": st.session_state.user,
                "date": str(v_date),
                "market": active_mkt,
                "news_impact": v_news,
                "session": v_sess,
                "tp_handles": handles,
                "duration_mins": duration,
                "notes": f"TAPE: {v_dir} | VEL: {velocity}H/m | LOW: {time_low} | HIGH: {time_high}",
                "hindsight": True,
                "model_name": "SESSION_TAPE"
            }
            
            try:
                supabase.table("trades").insert(vol_data).execute()
                st.success(f"Archived {v_sess}: {handles} Handles in {int(duration)} mins")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    # 3. ANALYTICS
    try:
        res = supabase.table("trades").select("*").eq("trader_username", st.session_state.user).eq("model_name", "SESSION_TAPE").eq("market", active_mkt).execute()
        df = pd.DataFrame(res.data)
    except: df = pd.DataFrame()

    if df.empty:
        st.info(f"No standalone tape data for {active_mkt} yet."); return

    df['date_dt'] = pd.to_datetime(df['date'])
    df['Day'] = df['date_dt'].dt.day_name()
    df['vel'] = df['notes'].apply(lambda x: float(x.split("VEL: ")[1].split("H/m")[0]) if "VEL:" in str(x) else 0.0)

    st.divider()
    st.write(f"### 🧬 {active_mkt} VOLATILITY DNA")
    
    g1, g2 = st.columns(2)
    with g1:
        st.write("**Avg Expansion (Handles) by Session**")
        st.bar_chart(df.groupby('session')['tp_handles'].mean())
    with g2:
        st.write("**Expansion Speed (H/m) by Day**")
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        st.line_chart(df.groupby('Day')['vel'].mean().reindex(day_order))

    st.write("**Velocity vs Delivery Time (The Sweet Spot)**")
    fig = px.scatter(df, x='duration_mins', y='tp_handles', size='vel', color='session',
                     labels={'duration_mins': 'Time to Complete Move (Mins)', 'tp_handles': 'Total Handles'},
                     hover_data=['Day', 'news_impact'])
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)