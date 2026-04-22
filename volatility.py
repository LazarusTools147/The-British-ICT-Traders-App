import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database import get_supabase

def render_volatility_tab():
    st.markdown('<h2 style="color: #FF4B4B;">📊 VOLATILITY ARCHIVE</h2>', unsafe_allow_html=True)
    supabase = get_supabase()

    # 1. FETCH MARKETS
    try:
        mkt_resp = supabase.table("markets").select("market_name").eq("trader_username", st.session_state.user).execute()
        markets = [r['market_name'] for r in mkt_resp.data]
    except: markets = []

    # 2. STANDALONE TAPE ENTRY (EXPANSION FOCUS)
    st.write("### 📝 LOG SESSION TAPE (DELIVERY WINDOWS)")
    with st.form("vol_standalone_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            v_date = st.date_input("DATE", datetime.now())
            v_mkt = st.selectbox("MARKET", markets)
            v_news = st.selectbox("NEWS DRIVER", ["NONE", "LOW", "MEDIUM", "HIGH", "NFP/CPI"])
        with c2:
            v_lon_h = st.number_input("LONDON HANDLES", value=0.0, step=0.25)
            v_lon_m = st.number_input("TIME TO HIGH/LOW (MINS)", value=1, help="Minutes from Open to Session Peak/Trough")
            v_dir = st.selectbox("EXPANSION DIRECTION", ["EXPANDED HIGHER", "EXPANDED LOWER", "REVERSAL", "CONSOLIDATION"])
        with c3:
            v_ny_h = st.number_input("NY AM HANDLES", value=0.0, step=0.25)
            v_ny_m = st.number_input("NY AM MOVE TIME (MINS)", value=1)
            v_note = st.text_input("NOTES (e.g. London manipulated Asia high then delivered)")

        if st.form_submit_button("📥 ARCHIVE SESSION TAPE"):
            # Velocity = Expansion Distance / Time to reach that distance
            lon_vel = round(v_lon_h / v_lon_m, 2) if v_lon_m > 0 else 0
            ny_vel = round(v_ny_h / v_ny_m, 2) if v_ny_m > 0 else 0
            
            vol_data = {
                "trader_username": st.session_state.user, "date": str(v_date), "market": v_mkt,
                "news_impact": v_news, "london_size": v_lon_h, "ny_am_size": v_ny_h,
                "duration_mins": v_lon_m + v_ny_m, "hindsight": True, "result": "BE", "model_name": "MARKET_TAPE",
                "notes": f"TAPE: {v_dir} | VEL: LON {lon_vel}H/m, NY {ny_vel}H/m | {v_note}"
            }
            try:
                supabase.table("trades").insert(vol_data).execute()
                st.success(f"Tape Secured. London Velocity: {lon_vel}H/m | NY Velocity: {ny_vel}H/m")
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")

    # 3. ANALYSIS
    try:
        res = supabase.table("trades").select("*").eq("trader_username", st.session_state.user).execute()
        df = pd.DataFrame(res.data)
    except: df = pd.DataFrame()

    if df.empty:
        st.info("Log session data to unlock the Delivery Machine."); return

    active_mkt = st.session_state.get('active_market', 'ALL MARKETS')
    if active_mkt != 'ALL MARKETS': df = df[df['market'] == active_mkt]
    
    df['date_dt'] = pd.to_datetime(df['date'])
    df['Day'] = df['date_dt'].dt.day_name()
    df['Week'] = (df['date_dt'].dt.day - 1) // 7 + 1

    # Velocity Extraction
    def get_vel(n, s):
        if not n or "VEL:" not in str(n): return 0.0
        try: return float(str(n).split(f"{s} ")[1].split("H/m")[0])
        except: return 0.0
    df['lon_v'] = df['notes'].apply(lambda x: get_vel(x, "LON"))
    df['ny_v'] = df['notes'].apply(lambda x: get_vel(x, "NY"))

    st.divider()
    st.write(f"### ⚡ {active_mkt} DELIVERY PERFORMANCE")
    
    t1, t2 = st.tabs(["🚀 VELOCITY VS RANGE", "📅 SEASONAL WINDOWS"])

    with t1:
        st.write("**Expansion Speed (H/m) vs Total Range**")
        st.caption("High H/m + High Handles = Institutional Delivery. Low H/m + Low Handles = Consolidation.")
        fig_v = px.scatter(df, x='london_size', y='lon_v', size='lon_v', color='news_impact',
                           hover_data=['date', 'Day'], title="London Delivery Profile")
        fig_v.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_v, use_container_width=True)

    with t2:
        st.write("**Average Session Move Time (Mins) by Day**")
        # Calculating average duration based on your "Move to High/Low" input
        move_time = df.groupby('Day')['duration_mins'].mean().reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        st.bar_chart(move_time)

    st.divider()
    st.write("### 📜 RAW TAPE HISTORY")
    st.dataframe(df[['date', 'Day', 'news_impact', 'london_size', 'ny_am_size', 'notes']].sort_values('date', ascending=False), use_container_width=True)