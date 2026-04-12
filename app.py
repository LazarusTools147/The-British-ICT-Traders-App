import streamlit as st
import pandas as pd
from database import init_db, get_supabase
from components import render_architect, render_forge, render_compounder
from analytics import render_analytics
from journal import render_journal_tab
from dca import render_dca_tab

# --- 1. INITIALIZE CLOUD CONNECTION ---
# This connects your local VS Code environment to the Supabase Cloud
init_db()
supabase = get_supabase()

# --- 2. GLOBAL PAGE CONFIG ---
st.set_page_config(
    page_title="ICT_MASTER_TERMINAL_V8.0",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 3. THE NEW CLOUD AUTHENTICATION ---
# This block handles the multi-user gatekeeping. 
# If a new user is added to the DB, they get a fresh slate automatically.
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = None

if not st.session_state.auth:
    st.title("🔐 TERMINAL_ACCESS_REQUIRED")
    st.write("Institutional Trading Vault v8.0 | Multi-User Cloud Infrastructure")
    
    # Using a form so hitting 'Enter' on the keyboard submits the login
    with st.form("login_form"):
        u_input = st.text_input("USERNAME").upper().strip()
        p_input = st.text_input("PASSWORD", type="password")
        submit = st.form_submit_button("ENTER VAULT")
        
        if submit:
            # Query the users table for a matching username AND password
            user_query = supabase.table("users").select("*").eq("username", u_input).eq("password", p_input).execute()
            
            if len(user_query.data) > 0:
                st.session_state.auth = True
                st.session_state.user = u_input
                st.success(f"ACCESS GRANTED: WELCOME {u_input}")
                st.rerun()
            else:
                st.error("ACCESS DENIED: INVALID CREDENTIALS. CHECK SUPABASE USERS TABLE.")
    st.stop()

# --- 4. DATA SYNCHRONIZATION (FILTERED BY PRIVATE USERNAME) ---
# This is the "Privacy Wall" that separates your data from Fin's data.
try:
    # We only pull trades where the trader_username matches the logged-in user
    response = supabase.table("trades").select("*").eq("trader_username", st.session_state.user).execute()
    all_trades = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"SYSTEM_ERROR: Unable to sync private vault data. {e}")
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
    # Architect is now filtered to show only YOUR saved models
    render_architect()

with tabs[1]: 
    # Forge is now filtered to only allow execution on YOUR models
    render_forge()

with tabs[2]:
    st.subheader("📊 LIVE PERFORMANCE")
    if not all_trades.empty:
        # Filter for LIVE trades only within the user's private dataset
        live_trades = all_trades[all_trades['type'] == 'LIVE']
        if not live_trades.empty:
            render_analytics(live_trades, "LIVE")
        else:
            st.info(f"No LIVE trades found in the vault for {st.session_state.user}. Log your first live execution in The Forge.")
    else:
        st.info("Cloud Vault is currently empty. Start logging to generate analytics.")

with tabs[3]:
    st.subheader("🧪 BACKTEST PERFORMANCE")
    if not all_trades.empty:
        # Filter for BACKTEST trades only within the user's private dataset
        test_trades = all_trades[all_trades['type'] == 'BACKTEST/DEMO']
        if not test_trades.empty:
            render_analytics(test_trades, "TEST")
        else:
            st.info(f"No TEST trades found in the vault for {st.session_state.user}. Time to hit the charts and backtest.")
    else:
        st.info("Cloud Vault is currently empty. Your backtesting data will appear here.")

with tabs[4]: 
    # Journal now includes the Winners Deep Dive and Full Stats
    render_journal_tab()

with tabs[5]: 
    # Portfolio is now private and user-specific
    render_dca_tab()

with tabs[6]: 
    # The Lifestyle Compounder remains a global utility
    render_compounder()

# --- 6. SIDEBAR UTILITIES ---
st.sidebar.title("TERMINAL_CONTROLS")
st.sidebar.write(f"Logged in as: **{st.session_state.user}**")

if st.sidebar.button("🔒 SECURE_LOGOUT"):
    # Clear session and force return to login gate
    st.session_state.auth = False
    st.session_state.user = None
    st.rerun()

st.sidebar.divider()
st.sidebar.info("v8.0 Multi-User Cloud Build | 2026 Institutional Edition")
st.sidebar.write("System Status: **🟢 ONLINE**")