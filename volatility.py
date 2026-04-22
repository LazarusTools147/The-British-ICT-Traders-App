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

    # 2. STANDALONE TAPE ENTRY
    st.write("### 📝 LOG SESSION TAPE (AMD ANALYSIS)")
    with st.form("vol_standalone_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            v_date = st.date_input("DATE", datetime.now())
            v_mkt = st.selectbox("MARKET", markets)
            v_news = st.selectbox("NEWS DRIVER", ["NONE", "LOW", "MEDIUM", "HIGH", "NFP/CPI"])
        with c2:
            v_lon_h = st.number_input("LONDON HANDLES", value=0.0, step=0.25)
            v_lon_m = st.number_input("LONDON MOVE SPEED (MINS)", value=1, help="Minutes to reach the session high/low")
            v_dir = st.selectbox("DAILY BIAS", ["EXPANDED HIGHER", "EXPANDED LOWER", "REVERSAL", "CONSOLIDATION"])
        with c3:
            v_ny_h = st.number_input("NY AM HANDLES", value=0.0, step=0.25)
            v_ny_m = st.number_input("NY AM MOVE SPEED (MINS)", value=1)
            v_note = st.text_input("NOTES (e.g. SMT at Lows)")

        if st.form_submit_button("📥 ARCHIVE SESSION TAPE"):
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
                st.success(f"Tape Secured. Velocity: {lon_vel}H/m (LON), {ny_vel}H/m (NY)")
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")

    # 3. CORE ANALYSIS ENGINE
    try:
        res = supabase.table("trades").select("*").eq("trader_username", st.session_state.user).execute()
        df = pd.DataFrame(res.data)
    except: df = pd.DataFrame()

    if df.empty:
        st.info("Log session data to unlock the Bias Machine."); return

    # Filter & Temporal Extraction
    active_mkt = st.session_state.get('active_market', 'ALL MARKETS')
    if active_mkt != 'ALL MARKETS': df = df[df['market'] == active_mkt]
    
    df['date_dt'] = pd.to_datetime(df['date'])
    df['Day'] = df['date_dt'].dt.day_name()
    df['Week'] = (df['date_dt'].dt.day - 1) // 7 + 1
    df['Month'] = df['date_dt'].dt.month_name()

    # Velocity Extraction Helper
    def get_vel(n, s):
        if not n or "VEL:" not in str(n): return 0.0
        try: return float(str(n).split(f"{s} ")[1].split("H/m")[0])
        except: return 0.0
    df['lon_v'] = df['notes'].apply(lambda x: get_vel(x, "LON"))
    df['ny_v'] = df['notes'].apply(lambda x: get_vel(x, "NY"))

    # --- VISUAL DASHBOARD ---
    st.divider()
    st.write(f"### 🧬 {active_mkt} SEASONAL DNA")
    t1, t2, t3 = st.tabs(["📅 CALENDAR BIAS", "⚡ VELOCITY SPRINT", "🧭 DIRECTIONAL MATRIX"])

    with t1:
        c_a, c_b = st.columns(2)
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        with c_a:
            st.write("**AVG Range by Day**")
            st.bar_chart(df.groupby('Day')[['london_size', 'ny_am_size']].mean().reindex(day_order))
        with c_b:
            st.write("**AVG Range by Week of Month**")
            st.line_chart(df.groupby('Week')[['london_size', 'ny_am_size']].mean())

    with t2:
        st.write("**Expansion Velocity vs News Impact**")
        st.info("Bubble Size = Total Handles | Height = Speed (H/m)")
        fig_v = px.scatter(df, x='news_impact', y='ny_v', size='ny_am_size', color='Day',
                           labels={'ny_v': 'NY Speed (H/m)', 'news_impact': 'News Driver'})
        fig_v.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_v, use_container_width=True)

    with t3:
        st.write("**News-Based Volatility (Handles)**")
        st.table(df.groupby('news_impact')[['london_size', 'ny_am_size']].describe().T.loc[(slice(None), ['mean', 'max', 'min']), :])

    st.divider()
    st.write("### 📜 THE RAW TAPE")
    st.dataframe(df[['date', 'Day', 'Week', 'news_impact', 'london_size', 'ny_am_size', 'notes']].sort_values('date', ascending=False), use_container_width=True)