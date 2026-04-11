import streamlit as st
import pandas as pd
from database import init_db, get_supabase
from components import render_architect, render_forge, render_compounder
from analytics import render_analytics
from journal import render_journal_tab
from dca import render_dca_tab

init_db()
st.set_page_config(page_title="ICT_MASTER_TERMINAL_V8.0", page_icon="🎯", layout="wide")

if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔐 TERMINAL_ACCESS")
    pwd = st.text_input("ENTER MASTER ACCESS KEY", type="password")
    if pwd == "TRADER2026":
        st.session_state.auth = True
        st.rerun()
    st.stop()

supabase = get_supabase()
response = supabase.table("trades").select("*").execute()
all_trades = pd.DataFrame(response.data)

tabs = st.tabs(["🏗️ ARCHITECT", "🔥 THE_FORGE", "📊 LIVE", "🧪 TEST", "📓 JOURNAL", "📉 DCA", "📈 COMPOUNDER"])

with tabs[0]: render_architect()
with tabs[1]: render_forge()
with tabs[2]: render_analytics(all_trades[all_trades['type'] == 'LIVE'], "LIVE") if not all_trades.empty else st.info("No Live Data")
with tabs[3]: render_analytics(all_trades[all_trades['type'] == 'BACKTEST/DEMO'], "TEST") if not all_trades.empty else st.info("No Test Data")
with tabs[4]: render_journal_tab()
with tabs[5]: render_dca_tab()
with tabs[6]: render_compounder()