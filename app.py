import streamlit as st
from database import init_db, get_connection
from components import render_architect, render_forge, render_compounder
from analytics import render_analytics
from journal import render_journal_tab
from dca import render_dca_tab
import pandas as pd

# --- 1. INITIALIZE GLOBAL ENGINE ---
# This runs once to ensure the Vault is secure and columns are repaired.
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
    st.write("Institutional Trading Vault v8.0")
    
    pwd = st.text_input("ENTER MASTER ACCESS KEY", type="password")
    if pwd == "TRADER2026":
        st.session_state.auth = True
        st.rerun()
    elif pwd != "":
        st.error("ACCESS DENIED: INVALID KEY")
    st.stop()

# --- 4. DATA SYNCHRONIZATION ---
# We pull the data once here so all tabs have access to the latest state.
conn = get_connection()
all_trades = pd.read_sql("SELECT * FROM trades", conn)
conn.close()

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

# --- TAB 1: ARCHITECT (Model Building) ---
with tabs[0]:
    render_architect()

# --- TAB 2: THE_FORGE (Execution Logging) ---
with tabs[1]:
    render_forge()

# --- TAB 3: LIVE_DATA (Analytics for Live Trades) ---
with tabs[2]:
    render_analytics(all_trades[all_trades['type'] == 'LIVE'], "LIVE")

# --- TAB 4: TEST_DATA (Analytics for Backtesting) ---
with tabs[3]:
    render_analytics(all_trades[all_trades['type'] == 'BACKTEST/DEMO'], "TEST")

# --- TAB 5: JOURNAL (The Record Keeper) ---
with tabs[4]:
    render_journal_tab()

# --- TAB 6: PORTFOLIO/DCA (Long-term Wealth) ---
with tabs[5]:
    render_dca_tab()

# --- TAB 7: COMPOUNDER (Projections) ---
with tabs[6]:
    render_compounder()

# --- 6. SIDEBAR UTILITIES ---
st.sidebar.title("TERMINAL_CONTROLS")
if st.sidebar.button("🔒 SECURE_LOGOUT"):
    st.session_state.auth = False
    st.rerun()

st.sidebar.divider()
st.sidebar.info("v8.0 Modular Build | 2026 Edition")