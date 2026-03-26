import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
import re

# --- 1. SETUP & DATABASE ---
st.set_page_config(page_title="TRADING_TERMINAL_V4.2", layout="wide")

def init_db():
    conn = sqlite3.connect('trading_vault.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS models (name TEXT PRIMARY KEY, logic TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS trades 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT, type TEXT, market TEXT, 
                  entry_info TEXT, entry_time TEXT, target TEXT, result TEXT, risk_pc REAL, rr REAL, 
                  notes TEXT, date TEXT, screenshot BLOB)''')
    for col in [('entry_time', 'TEXT'), ('target', 'TEXT')]:
        try:
            c.execute(f'ALTER TABLE trades ADD COLUMN {col[0]} {col[1]}')
        except:
            pass
    conn.commit()
    conn.close()

init_db()

# --- 2. LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 TERMINAL_ACCESS")
    pwd = st.text_input("KEY", type="password")
    if st.button("INITIALIZE"):
        if pwd == "TRADER2026":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- 3. TABS ---
tabs = st.tabs(["🏗️ ARCHITECT", "🔥 THE_FORGE", "📊 LIVE_DATA", "🧪 TEST_DATA", "📅 HISTORY", "📈 COMPOUNDER"])

# --- TAB 1: ARCHITECT ---
with tabs[0]:
    st.header("SYSTEM_DESIGN")
    m_name = st.text_input("MODEL_NAME").upper()
    m_logic = st.text_area("MODEL_LOGIC_&_RULES", height=300)
    if st.button("SAVE_MODEL"):
        if m_name:
            conn = sqlite3.connect('trading_vault.db')
            conn.execute("INSERT OR REPLACE INTO models VALUES (?, ?)", (m_name, m_logic))
            conn.commit()
            st.success("MODEL_ARCHIVED")

# --- TAB 2: THE_FORGE ---
with tabs[1]:
    conn = sqlite3.connect('trading_vault.db')
    models_df = pd.read_sql("SELECT name FROM models", conn)
    models = models_df['name'].tolist()
    if not models:
        st.warning("CREATE A MODEL FIRST.")
    else:
        st.header("ENTRY_STATION")
        with st.form("log_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                env = st.radio("ENVIRONMENT", ["LIVE", "BACKTEST/DEMO"], horizontal=True)
                mod = st.selectbox("MODEL", models)
                mkt = st.text_input("MARKET (NQ, OIL, ES)").upper()
                ent_type = st.text_input("ENTRY_DETAILS (e.g. FVG + OB)")
                ent_time = st.text_input("ENTRY_TIME (e.g. 09:30 or 14:15)")
            with c2:
                targ = st.text_input("TARGET (e.g. BSL, SSL, 2R)")
                res = st.selectbox("RESULT", ["WIN", "LOSS", "BE"])
                rsk = st.number_input("RISK_%", step=0.1, value=1.0)
                rvr = st.number_input("RR_RESULT", step=0.1, value=2.0)
                dt = st.date_input("DATE", datetime.now())
            
            nts = st.text_area("NOTES_&_JOURNAL")
            img = st.file_uploader("UPLOAD_CHART", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("SAVE_ENTRY"):
                if not mkt or not ent_type or not ent_time:
                    st.error("MISSING DATA: Fill in Market, Entry Details, and Time.")
                else:
                    img_data = img.read() if img else None
                    conn.execute('''INSERT INTO trades (model_name, type, market, entry_info, entry_time, target, 
                                    result, risk_pc, rr, notes, date, screenshot) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                                 (mod, env, mkt, ent_type, ent_time.upper(), targ.upper(), res, rsk, rvr, nts, dt.strftime("%Y-%m-%d"), img_data))
                    conn.commit()
                    st.success("DATA_SECURED")

# --- TAB 3 & 4: ANALYTICS ---
def render_analytics(df_subset, suffix):
    if df_subset.empty:
        st.info(f"NO DATA LOGGED FOR {suffix}.")
        return

    # NEW 10-MINUTE ROUNDING LOGIC
    def round_to_10(t_str):
        match = re.search(r'(\d{1,2})[:.]?(\d{2})', str(t_str))
        if match:
            h, m = int(match.group(1)), int(match.group(2))
            m = round(m / 10) * 10
            if m == 60:
                h = (h + 1) % 24
                m = 0
            return f"{h:02d}:{m:02d}"
        return "OTHER"

    df_subset['Rounded_Time'] = df_subset['entry_time'].apply(round_to_10)
    df_subset = df_subset.sort_values(by='Rounded_Time')

    st.subheader("⏱️ MACRO_ROUNDED_DISTRIBUTION (10m)")
    fig_bar = px.bar(df_subset, x='Rounded_Time', title=f"Frequency (10m Intervals) - {suffix}", 
                     color_discrete_sequence=['#000000'])
    st.plotly_chart(fig_bar, use_container_width=True, key=f"bar_{suffix}")

    st.divider()

    c1, c2 = st.columns(2)
    c3, c4, c5 = st.columns(3)
    with c1: st.plotly_chart(px.pie(df_subset, names='entry_info', title="ENTRY_TYPE %", hole=0.4), use_container_width=True, key=f"pie1_{suffix}")
    with c2: st.plotly_chart(px.pie(df_subset, names='market', title="MARKET %", hole=0.4), use_container_width=True, key=f"pie2_{suffix}")
    with c3: st.plotly_chart(px.pie(df_subset, names='result', title="WIN_RATE %", hole=0.4, color='result', color_discrete_map={'WIN':'#00ff00', 'LOSS':'#ff0000', 'BE':'#888888'}), use_container_width=True, key=f"pie3_{suffix}")
    with c4: st.plotly_chart(px.pie(df_subset, names='entry_time', title="SESSIONS %", hole=0.4), use_container_width=True, key=f"pie4_{suffix}")
    with c5: st.plotly_chart(px.pie(df_subset, names='target', title="TARGETS %", hole=0.4), use_container_width=True, key=f"pie5_{suffix}")

conn = sqlite3.connect('trading_vault.db')
all_trades = pd.read_sql("SELECT * FROM trades", conn)

with tabs[2]: render_analytics(all_trades[all_trades['type'] == 'LIVE'], "LIVE")
with tabs[3]: render_analytics(all_trades[all_trades['type'] == 'BACKTEST/DEMO'], "TEST")

# --- TAB 5: HISTORY ---
with tabs[4]:
    st.header("TRADE_HISTORY")
    search_q = st.text_input("SEARCH_BY_MARKET").upper()
    hist_df = all_trades.copy()
    if search_q: hist_df = hist_df[hist_df['market'].str.contains(search_q)]
    
    for _, row in hist_df.iterrows():
        with st.expander(f"{row['date']} | {row['entry_time']} | {row['market']} | {row['result']}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                edit_key = f"edit_mode_{row['id']}"
                if edit_key not in st.session_state: st.session_state[edit_key] = False
                
                if not st.session_state[edit_key]:
                    st.write(f"**Entry:** {row['entry_info']} | **Target:** {row['target']} | **Time:** {row['entry_time']}")
                    st.write(f"**RR:** {row['rr']}R | **Notes:** {row['notes']}")
                    ca, cb = st.columns(2)
                    if ca.button("✏️ EDIT", key=f"e_{row['id']}"): 
                        st.session_state[edit_key] = True
                        st.rerun()
                    if cb.button("🗑️ DELETE", key=f"d_{row['id']}"):
                        conn.execute("DELETE FROM trades WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()
                else:
                    n_ent = st.text_input("Details", row['entry_info'], key=f"ne_{row['id']}")
                    n_targ = st.text_input("Target", row['target'], key=f"ntar_{row['id']}")
                    n_time = st.text_input("Time", row['entry_time'], key=f"nt_{row['id']}")
                    if st.button("SAVE CHANGES", key=f"s_{row['id']}"):
                        conn.execute("UPDATE trades SET entry_info=?, target=?, entry_time=? WHERE id=?", (n_ent, n_targ.upper(), n_time.upper(), row['id']))
                        conn.commit()
                        st.session_state[edit_key] = False
                        st.rerun()
            with col2:
                if row['screenshot']: st.image(row['screenshot'])

# --- TAB 6: COMPOUNDER ---
with tabs[5]:
    st.header("COMPOUND_PROJECTOR")
    c_col1, c_col2 = st.columns([1, 2])
    with c_col1:
        p_val = st.number_input("INITIAL", value=5000)
        r_val = st.number_input("MONTHLY_%", value=5.0)
        y_val = st.number_input("YEARS", value=5)
    months, bal = int(y_val * 12), p_val
    data = []
    for m in range(1, months + 1):
        bal *= (1 + (r_val / 100))
        if m % 12 == 0: data.append({"Year": m//12, "Balance": round(bal, 2)})
    with c_col2:
        st.line_chart(pd.DataFrame(data).set_index("Year"))
        st.table(pd.DataFrame(data))

conn.close()