import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
import re

# --- 1. SETUP & DATABASE REPAIR ---
st.set_page_config(page_title="ICT_MASTER_TERMINAL_V6.4", layout="wide")

# Persistent connection helper
def get_connection():
    return sqlite3.connect('trading_vault.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS models (name TEXT PRIMARY KEY, logic TEXT, sessions TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS trades 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT, type TEXT, market TEXT, 
                  entry_info TEXT, entry_time TEXT, entry_tf TEXT, session TEXT, target TEXT, result TEXT, 
                  risk_pc REAL, rr REAL, notes TEXT, date TEXT, duration_mins INTEGER, 
                  news_impact TEXT, screenshot BLOB)''')
    
    # Check for missing columns to prevent crashes during updates
    cols = [('duration_mins', 'INTEGER'), ('news_impact', 'TEXT'), ('session', 'TEXT'), ('target', 'TEXT'), ('sessions', 'TEXT'), ('entry_tf', 'TEXT')]
    for col_name, col_type in cols:
        try: c.execute(f'ALTER TABLE trades ADD COLUMN {col_name} {col_type}')
        except: pass
    try: c.execute(f'ALTER TABLE models ADD COLUMN sessions TEXT')
    except: pass
    conn.commit()
    conn.close()

init_db()

# --- 2. AUTHENTICATION (REPAIRED) ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 TERMINAL_ACCESS")
    # Simplified login to prevent "Initialize" button loops
    pwd = st.text_input("ENTER ACCESS KEY", type="password")
    if pwd == "TRADER2026":
        st.session_state.auth = True
        st.rerun()
    elif pwd != "":
        st.error("INVALID KEY")
    st.stop()

# Sidebar Logout
if st.sidebar.button("🔒 LOGOUT"):
    st.session_state.auth = False
    st.rerun()

# --- 3. TABS ---
tabs = st.tabs(["🏗️ ARCHITECT", "🔥 THE_FORGE", "📊 LIVE_DATA", "🧪 TEST_DATA", "📅 HISTORY", "📈 COMPOUNDER"])

# --- TAB 1: ARCHITECT ---
with tabs[0]:
    st.header("MODEL_ARCHITECT")
    m_name = st.text_input("MODEL_NAME").upper()
    m_sess_list = st.multiselect("ALLOWED_SESSIONS", ["ASIA", "LONDON", "NY AM", "NY PM"])
    m_logic = st.text_area("CORE_LOGIC_&_RULES", height=200)
    if st.button("SAVE_MODEL"):
        if m_name:
            conn = get_connection()
            conn.execute("INSERT OR REPLACE INTO models VALUES (?, ?, ?)", (m_name, m_logic, ",".join(m_sess_list)))
            conn.commit(); conn.close()
            st.success("MODEL ARCHIVED")

# --- TAB 2: THE_FORGE ---
with tabs[1]:
    conn = get_connection()
    models_df = pd.read_sql("SELECT * FROM models", conn)
    models = models_df['name'].tolist()
    conn.close() # Always close to prevent "Database Locked" errors
    
    if not models:
        st.warning("CREATE A MODEL FIRST.")
    else:
        st.header("THE_FORGE: LOG_ENTRY")
        with st.form("log_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                env = st.radio("ENV", ["LIVE", "BACKTEST/DEMO"], horizontal=True)
                mod = st.selectbox("MODEL", models)
                mkt = st.text_input("MARKET").upper()
                ent_type = st.text_input("ENTRY DETAILS (e.g. FVG)")
            with c2:
                ent_time = st.text_input("TIME (HH:MM)")
                ent_tf = st.text_input("TF").upper()
                ent_sess = st.text_input("SESSION").upper()
                dur = st.number_input("DURATION (MINS)", min_value=1, value=15)
            with c3:
                news = st.text_input("NEWS").upper()
                targ = st.text_input("TARGET").upper()
                res = st.text_input("RESULT (WIN, LOSS, BE)").upper()
                rsk = st.number_input("RISK %", value=1.0)
                rvr = st.number_input("RR", value=2.0)
                dt = st.date_input("DATE", datetime.now())
            
            nts = st.text_area("NOTES")
            img = st.file_uploader("CHART", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("SAVE_ENTRY"):
                if not mkt or not ent_time or not res:
                    st.error("MISSING DATA: Market, Time, and Result are required.")
                else:
                    img_data = img.read() if img else None
                    conn = get_connection()
                    conn.execute('''INSERT INTO trades (model_name, type, market, entry_info, entry_time, entry_tf, session, 
                                    target, result, risk_pc, rr, notes, date, duration_mins, news_impact, screenshot) 
                                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                                 (mod, env, mkt, ent_type, ent_time, ent_tf, ent_sess, targ, res, rsk, rvr, nts, dt.strftime("%Y-%m-%d"), dur, news, img_data))
                    conn.commit(); conn.close()
                    st.success("DATA SECURED")

# --- 4. ANALYTICS ENGINE (v6.4 Symmetrical Layout + Orange BE) ---
def render_kpi_analytics(df_all, suffix):
    if df_all.empty:
        st.info(f"NO DATA FOR {suffix}.")
        return

    st.markdown("## 📈 GLOBAL PERFORMANCE KPI")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("GLOBAL WIN RATE", f"{round((len(df_all[df_all['result']=='WIN']) / len(df_all)) * 100, 1)}%")
    with k2: st.metric("GLOBAL AVG DURATION", f"{round(df_all['duration_mins'].mean(), 1)}m")
    with k3: st.metric("AVG RISK PER TRADE", f"{round(df_all['risk_pc'].mean(), 2)}%")
    with k4: st.metric("AVG RR RATIO", f"{round(df_all['rr'].mean(), 2)}R")

    st.divider()
    
    kpi1, kpi2 = st.columns([3, 1])
    res_colors = {'WIN':'#00ff00', 'LOSS':'#ff0000', 'BE':'#FFA500'}
    
    with kpi1:
        df_all = df_all.sort_values('entry_time')
        fig_main = px.bar(df_all, x='entry_time', y='rr', color='result', title="Performance Pulse", color_discrete_map=res_colors)
        fig_main.update_layout(bargap=0.3); st.plotly_chart(fig_main, use_container_width=True)
    with kpi2:
        st.plotly_chart(px.pie(df_all, names='result', title="WIN_RATE PIE", hole=0.5, color='result', color_discrete_map=res_colors), use_container_width=True)

    st.divider()

    def draw_segmented_section(res_type, label, emoji, sfx):
        sub_df = df_all[df_all['result'] == res_type].copy()
        if sub_df.empty: return
        
        with st.expander(f"{emoji} {label} DEEP-DIVE ANALYSIS", expanded=(res_type == "WIN")):
            sk1, sk2 = st.columns([3, 1])
            with sk1:
                def get_macro(t):
                    m = re.search(r'(\d{1,2})[:.]?(\d{2})', str(t))
                    if not m: return "OTHER"
                    h, mn = int(m.group(1)), int(m.group(2))
                    if (h==2 and mn>=50) or (h==3 and mn<=10) or (h==3 and mn>=50) or (h==4 and mn<=10) or (h==4 and mn>=50) or (h==5 and mn<=10): return "MACRO"
                    return f"{h:02d}:00"
                sub_df['Cat'] = sub_df['entry_time'].apply(get_macro)
                fig_sub = px.bar(sub_df.sort_values('entry_time'), x='entry_time', color='Cat', title=f"{label} Pulse", color_discrete_map={"MACRO":"#FFD700"})
                st.plotly_chart(fig_sub, use_container_width=True, key=f"bar_{res_type}_{sfx}")
            
            with sk2:
                st.metric(f"AVG {res_type} TIME", f"{round(sub_df['duration_mins'].mean(), 1)}m")
                st.plotly_chart(px.pie(sub_df, names='entry_info', title="Entry Types", hole=0.4), use_container_width=True, key=f"p_ent_{res_type}_{sfx}")

            p1, p2, p3, p4, p5 = st.columns(5)
            pie_args = dict(hole=0.4, width=250, height=250)
            with p1: st.plotly_chart(px.pie(sub_df, names='market', title="Markets", **pie_args), use_container_width=True, key=f"m_{res_type}_{sfx}")
            with p2: st.plotly_chart(px.pie(sub_df, names='session', title="Sessions", **pie_args), use_container_width=True, key=f"s_{res_type}_{sfx}")
            with p3: st.plotly_chart(px.pie(sub_df, names='target', title="Targets", **pie_args), use_container_width=True, key=f"t_{res_type}_{sfx}")
            with p4: st.plotly_chart(px.pie(sub_df, names='news_impact', title="News", **pie_args), use_container_width=True, key=f"n_{res_type}_{sfx}")
            with p5: st.plotly_chart(px.pie(sub_df, names='entry_tf', title="Timeframes", **pie_args), use_container_width=True, key=f"tf_{res_type}_{sfx}")

    draw_segmented_section("WIN", "WINNERS' CIRCLE", "🏆", suffix)
    draw_segmented_section("BE", "BREAK EVEN DEFENSE", "🛡️", suffix)
    draw_segmented_section("LOSS", "LOSS AUTOPSY", "💀", suffix)

# --- LOAD DATA ---
conn = get_connection()
all_trades = pd.read_sql("SELECT * FROM trades", conn)
conn.close()

with tabs[2]: render_kpi_analytics(all_trades[all_trades['type'] == 'LIVE'], "LIVE")
with tabs[3]: render_kpi_analytics(all_trades[all_trades['type'] == 'BACKTEST/DEMO'], "TEST")

# --- TAB 5: HISTORY ---
with tabs[4]:
    st.header("HISTORY")
    for _, row in all_trades[::-1].iterrows():
        with st.expander(f"{row['date']} | {row['entry_time']} | {row['market']} | {row['result']}"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.write(f"TF: {row['entry_tf']} | Sess: {row['session']} | Target: {row['target']} | Dur: {row['duration_mins']}m")
                st.info(f"Notes: {row['notes']}")
                if st.button("🗑️ DELETE", key=f"del_{row['id']}"):
                    conn = get_connection()
                    conn.execute("DELETE FROM trades WHERE id=?", (row['id'],))
                    conn.commit(); conn.close()
                    st.rerun()
            with c2:
                if row['screenshot']: st.image(row['screenshot'])

# --- TAB 6: COMPOUNDER ---
with tabs[5]:
    st.header("COMPOUNDER")
    p, r, y = st.number_input("STARTING BALANCE", 5000), st.number_input("MONTHLY %", 5.0), st.number_input("YEARS", 5)
    bal, data = p, []
    for m in range(1, int(y*12)+1):
        bal *= (1 + (r/100))
        if m%12==0: data.append({"Year": m//12, "Balance": round(bal, 2)})
    st.line_chart(pd.DataFrame(data).set_index("Year"))