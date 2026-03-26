import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
import io

# --- 1. SETUP & DATABASE INITIALIZATION ---
st.set_page_config(page_title="TRADING_TERMINAL_V3", layout="wide")

def init_db():
    conn = sqlite3.connect('trading_vault.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS models (name TEXT PRIMARY KEY, logic TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS trades 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT, type TEXT, market TEXT, 
                  entry_info TEXT, entry_time TEXT, result TEXT, risk_pc REAL, rr REAL, notes TEXT, 
                  date TEXT, screenshot BLOB)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. AUTHENTICATION SYSTEM ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 TERMINAL_ACCESS")
    pwd = st.text_input("KEY", type="password")
    if st.button("INITIALIZE"):
        if pwd == "TRADER2026":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("ACCESS_DENIED")
    st.stop()

# SIDEBAR: NAVIGATION & LOGOUT
st.sidebar.title("🏁 NAVIGATION")
if st.sidebar.button("🔒 LOGOUT"):
    st.session_state.auth = False
    st.rerun()

# --- 3. MAIN TABS STRUCTURE ---
tabs = st.tabs(["🏗️ ARCHITECT", "🔥 THE_FORGE", "📊 LIVE_DATA", "🧪 TEST_DATA", "📅 HISTORY", "📈 COMPOUNDER"])

# --- TAB 1: ARCHITECT (Model Creation) ---
with tabs[0]:
    st.header("SYSTEM_DESIGN")
    m_name = st.text_input("MODEL_NAME").upper()
    m_logic = st.text_area("MODEL_LOGIC_&_RULES", height=300, placeholder="Define your entry criteria, HTF narrative, and exit rules...")
    if st.button("SAVE_MODEL"):
        if m_name:
            conn = sqlite3.connect('trading_vault.db')
            conn.execute("INSERT OR REPLACE INTO models VALUES (?, ?)", (m_name, m_logic))
            conn.commit()
            conn.close()
            st.success(f"MODEL {m_name} ARCHIVED")

# --- TAB 2: THE_FORGE (Trade Entry) ---
with tabs[1]:
    conn = sqlite3.connect('trading_vault.db')
    models_df = pd.read_sql("SELECT name FROM models", conn)
    models = models_df['name'].tolist()
    conn.close()

    if not models:
        st.warning("PLEASE CREATE A MODEL IN THE 'ARCHITECT' TAB FIRST.")
    else:
        st.header("ENTRY_STATION")
        with st.form("log_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                env = st.radio("ENVIRONMENT", ["LIVE", "BACKTEST/DEMO"], horizontal=True)
                mod = st.selectbox("MODEL", models)
                mkt = st.text_input("MARKET (e.g., NQ, OIL, ES)").upper()
                ent_type = st.text_input("ENTRY_TYPE (e.g., FVG + OB)")
                ent_time = st.time_input("ENTRY_TIME", datetime.now().time())
            with c2:
                res = st.selectbox("RESULT", ["WIN", "LOSS", "BE"])
                rsk = st.number_input("RISK_%", step=0.1, value=1.0)
                rvr = st.number_input("RR_RESULT", step=0.1, value=2.0)
                dt = st.date_input("DATE", datetime.now())
            
            nts = st.text_area("NOTES_&_JOURNAL")
            img = st.file_uploader("UPLOAD_CHART", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("SAVE_ENTRY"):
                img_data = img.read() if img else None
                conn = sqlite3.connect('trading_vault.db')
                conn.execute('''INSERT INTO trades (model_name, type, market, entry_info, entry_time, result, 
                                risk_pc, rr, notes, date, screenshot) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                             (mod, env, mkt, ent_type, ent_time.strftime("%H:%M"), res, rsk, rvr, nts, dt.strftime("%Y-%m-%d"), img_data))
                conn.commit()
                conn.close()
                st.success("DATA_SECURED")

# --- TAB 3 & 4: ANALYTICS ---
def render_analytics(df_subset, title):
    st.header(title)
    if df_subset.empty:
        st.info("NO DATA LOGGED FOR THIS ENVIRONMENT.")
        return
    
    # Frequency Chart
    df_subset['hour'] = df_subset['entry_time'].apply(lambda x: int(x.split(':')[0]))
    st.plotly_chart(px.histogram(df_subset, x='hour', nbins=24, title="Trade Frequency by Hour", color_discrete_sequence=['black']), use_container_width=True)

    # Triple Pie Charts
    c1, c2, c3 = st.columns(3)
    with c1: st.plotly_chart(px.pie(df_subset, names='entry_info', title="ENTRY_TYPE_%", hole=0.4), use_container_width=True)
    with c2: st.plotly_chart(px.pie(df_subset, names='market', title="MARKET_%", hole=0.4), use_container_width=True)
    with c3: st.plotly_chart(px.pie(df_subset, names='result', title="WIN_RATE_%", hole=0.4, 
                                   color='result', color_discrete_map={'WIN':'#00ff00', 'LOSS':'#ff0000', 'BE':'#888888'}), use_container_width=True)

conn = sqlite3.connect('trading_vault.db')
all_trades = pd.read_sql("SELECT * FROM trades", conn)
conn.close()

with tabs[2]: render_analytics(all_trades[all_trades['type'] == 'LIVE'], "LIVE_PERFORMANCE")
with tabs[3]: render_analytics(all_trades[all_trades['type'] == 'BACKTEST/DEMO'], "TEST_PERFORMANCE")

# --- TAB 5: HISTORY (WITH EDIT & DELETE) ---
with tabs[4]:
    st.header("TRADE_HISTORY")
    search_q = st.text_input("SEARCH_BY_MARKET (e.g. NQ)").upper()
    hist_df = all_trades.copy()
    if search_q: hist_df = hist_df[hist_df['market'].str.contains(search_q)]
    
    for _, row in hist_df.iterrows():
        with st.expander(f"{row['date']} | {row['entry_time']} | {row['market']} | {row['result']}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                edit_key = f"edit_mode_{row['id']}"
                if edit_key not in st.session_state: st.session_state[edit_key] = False
                
                if not st.session_state[edit_key]:
                    st.write(f"**Model:** {row['model_name']} | **Entry:** {row['entry_info']}")
                    st.write(f"**RR:** {row['rr']}R | **Risk:** {row['risk_pc']}%")
                    st.write(f"**Notes:** {row['notes']}")
                    
                    c_btn1, c_btn2 = st.columns(2)
                    if c_btn1.button("✏️ EDIT", key=f"btn_edit_{row['id']}"):
                        st.session_state[edit_key] = True
                        st.rerun()
                    if c_btn2.button("🗑️ DELETE", key=f"btn_del_{row['id']}"):
                        conn = sqlite3.connect('trading_vault.db')
                        conn.execute("DELETE FROM trades WHERE id = ?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
                else:
                    # EDIT MODE
                    new_ent = st.text_input("Edit Entry Info", value=row['entry_info'], key=f"edit_ent_{row['id']}")
                    new_rr = st.number_input("Edit RR", value=float(row['rr']), key=f"edit_rr_{row['id']}")
                    new_res = st.selectbox("Edit Result", ["WIN", "LOSS", "BE"], index=["WIN", "LOSS", "BE"].index(row['result']), key=f"edit_res_{row['id']}")
                    new_nts = st.text_area("Edit Notes", value=row['notes'], key=f"edit_nts_{row['id']}")
                    
                    c_save1, c_save2 = st.columns(2)
                    if c_save1.button("SAVE CHANGES", key=f"save_{row['id']}"):
                        conn = sqlite3.connect('trading_vault.db')
                        conn.execute("UPDATE trades SET entry_info=?, rr=?, result=?, notes=? WHERE id=?", (new_ent, new_rr, new_res, new_nts, row['id']))
                        conn.commit()
                        conn.close()
                        st.session_state[edit_key] = False
                        st.rerun()
                    if c_save2.button("CANCEL", key=f"cancel_{row['id']}"):
                        st.session_state[edit_key] = False
                        st.rerun()
            with col2:
                if row['screenshot']: st.image(row['screenshot'])

# --- TAB 6: COMPOUNDER ---
with tabs[5]:
    st.header("COMPOUND_PROJECTOR")
    c_col1, c_col2 = st.columns([1, 2])
    with c_col1:
        p_val = st.number_input("INITIAL_BALANCE", value=5000)
        r_val = st.number_input("ESTIMATED_MONTHLY_%", value=5.0)
        y_val = st.number_input("DURATION_IN_YEARS", value=5)
    
    months = int(y_val * 12)
    current_bal = p_val
    proj_data = []
    for m in range(1, months + 1):
        current_bal *= (1 + (r_val / 100))
        if m % 12 == 0: proj_data.append({"Year": m//12, "Balance": round(current_bal, 2)})
    
    with c_col2:
        st.line_chart(pd.DataFrame(proj_data).set_index("Year"))
        st.table(pd.DataFrame(proj_data))