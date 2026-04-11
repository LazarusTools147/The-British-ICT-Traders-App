import streamlit as st
import pandas as pd
from database import init_db, get_supabase
from components import render_architect, render_forge, render_compounder
from analytics import render_analytics
from journal import render_journal_tab
from dca import render_dca_tab

# --- 1. INITIALIZE CLOUD CONNECTION ---
init_db()

# --- 2. GLOBAL PAGE CONFIG ---
st.set_page_config(
    page_title="ICT_MASTER_TERMINAL_V8.0",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 3. AUTHENTICATION GATEKEEPER ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 TERMINAL_ACCESS_REQUIRED")
    st.write("Institutional Trading Vault v8.0 | Cloud Edition")
    
    pwd = st.text_input("ENTER MASTER ACCESS KEY", type="password")
    if pwd == "TRADER2026":
        st.session_state.auth = True
        st.rerun()
    elif pwd != "":
        st.error("ACCESS DENIED: INVALID KEY")
    st.stop()

# --- 4. DATA SYNCHRONIZATION (SUPABASE) ---
supabase = get_supabase()
try:
    response = supabase.table("trades").select("*").execute()
    all_trades = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Error fetching data: {e}")
    all_trades = pd.DataFrame()

# --- 5. NAVIGATION (THE TABS) ---
tabs = st.tabs([
    "🏗️ ARCHITECT", 
    "🔥 THE_FORGE", 
    "📊 LIVE_DATA", 
    "🧪 TEST_DATA", 
    "📓 JOURNAL", 
    "📉 PORTFOLIO/DCA", 
    "📈 COMPOUNDER"
])

with tabs[0]: 
    render_architect()

with tabs[1]: 
    render_forge()

with tabs[2]:
    st.subheader("📊 LIVE PERFORMANCE")
    if not all_trades.empty:
        # Filter for LIVE trades specifically
        live_trades = all_trades[all_trades['type'] == 'LIVE']
        if not live_trades.empty:
            render_analytics(live_trades, "LIVE")
        else:
            st.info("No LIVE trades found. Start logging in The Forge.")
    else:
        st.info("Cloud Vault is empty. Log your first trade.")

with tabs[3]:
    st.subheader("🧪 BACKTEST PERFORMANCE")
    if not all_trades.empty:
        # Filter for BACKTEST trades specifically
        test_trades = all_trades[all_trades['type'] == 'BACKTEST/DEMO']
        if not test_trades.empty:
            render_analytics(test_trades, "TEST")
        else:
            st.info("No TEST trades found. Time to hit the charts.")
    else:
        st.info("Cloud Vault is empty. Log your first backtest.")

with tabs[4]: 
    render_journal_tab()

with tabs[5]: 
    render_dca_tab()

with tabs[6]: 
    render_compounder()

# --- 6. SIDEBAR UTILITIES ---
st.sidebar.title("TERMINAL_CONTROLS")
if st.sidebar.button("🔒 SECURE_LOGOUT"):
    st.session_state.auth = False
    st.rerun()

st.sidebar.divider()
st.sidebar.info("v8.0 Cloud Build | 2026 Edition")