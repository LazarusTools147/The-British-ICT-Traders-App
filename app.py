import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
import re

# --- 1. SETUP & DATABASE ---
st.set_page_config(page_title="ICT_TERMINAL_V5.6", layout="wide")

def init_db():
    conn = sqlite3.connect('trading_vault.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS models (name TEXT PRIMARY KEY, logic TEXT, sessions TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS trades 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT, type TEXT, market TEXT, 
                  entry_info TEXT, entry_time TEXT, session TEXT, target TEXT, result TEXT, 
                  risk_pc REAL, rr REAL, notes TEXT, date TEXT, duration_mins INTEGER, 
                  news_impact TEXT, screenshot BLOB)''')
    for col, typ in [('duration_mins','INTEGER'),('news_impact','TEXT'),('session','TEXT'),('target','TEXT'),('sessions','TEXT')]:
        try: c.execute(f'ALTER TABLE trades ADD COLUMN {col} {typ}')
        except: pass
    conn.commit()
    conn.close()

init_db()

# --- 2. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔐 TERMINAL_ACCESS")
    if st.text_input("KEY", type="password") == "TRADER2026":
        if st.button("INITIALIZE"): st.session_state.auth = True; st.rerun()
    st.stop()

# --- 3. THE FORGE & ARCHITECT ---
tabs = st.tabs(["🏗️ ARCHITECT", "🔥 THE_FORGE", "📊 LIVE_DATA", "🧪 TEST_DATA", "📅 HISTORY", "📈 COMPOUNDER"])

with tabs[0]:
    st.header("MODEL_ARCHITECT")
    m_name = st.text_input("NAME").upper()
    m_sess = st.multiselect("SESSIONS", ["ASIA", "LONDON", "NY AM", "NY PM"])
    m_logic = st.text_area("RULES", height=150)
    if st.button("SAVE"):
        conn = sqlite3.connect('trading_vault.db')
        conn.execute("INSERT OR REPLACE INTO models VALUES (?,?,?)", (m_name, m_logic, ",".join(m_sess)))
        conn.commit(); conn.close(); st.success("SAVED")

with tabs[1]:
    conn = sqlite3.connect('trading_vault.db')
    models = pd.read_sql("SELECT name FROM models", conn)['name'].tolist()
    if not models: st.warning("Create a model first.")
    else:
        with st.form("forge", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1: env=st.radio("ENV",["LIVE","TEST"]); mod=st.selectbox("MODEL",models); mkt=st.text_input("MKT").upper(); ent=st.text_input("DETAILS")
            with c2: tm=st.text_input("TIME (HH:MM)"); sess=st.text_input("SESS").upper(); dur=st.number_input("MINS",1,120,15); nws=st.selectbox("NEWS",["NONE","LOW","MED","RED"])
            with c3: trg=st.text_input("TARGET").upper(); res=st.selectbox("RESULT",["WIN","LOSS","BE"]); rsk=st.number_input("RSK%",0.1,5.0,1.0); rr=st.number_input("RR",0.1,20.0,2.0); dt=st.date_input("DATE")
            nts=st.text_area("NOTES"); img=st.file_uploader("IMG", type=['png','jpg'])
            if st.form_submit_button("SAVE ENTRY"):
                img_data = img.read() if img else None
                conn.execute("INSERT INTO trades (model_name,type,market,entry_info,entry_time,session,target,result,risk_pc,rr,notes,date,duration_mins,news_impact,screenshot) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(mod,env,mkt,ent,tm,sess,trg,res,rsk,rr,nts,dt.strftime("%Y-%m-%d"),dur,nws,img_data))
                conn.commit(); st.success("SECURED")

# --- 4. ANALYTICS ENGINE (OPTIMIZED) ---
def run_viz(df, label):
    if df.empty: return st.write(f"No {label} data.")
    def get_cat(t):
        m = re.search(r'(\d{1,2})[:.]?(\d{2})', str(t))
        if not m: return "OTHER"
        h, mn = int(m.group(1)), int(m.group(2))
        if (h==2 and mn>=50) or (h==3 and mn<=10) or (h==3 and mn>=50) or (h==4 and mn<=10) or (h==4 and mn>=50) or (h==5 and mn<=10): return "GOLD_MACRO"
        return f"{h:02d}:00"
    df['Cat'] = df['entry_time'].apply(get_cat)
    c1, c2 = st.columns([2,1])
    with c1: st.plotly_chart(px.bar(df.sort_values('entry_time'), x='entry_time', color='Cat', title=f"{label} Pulse", color_discrete_map={"GOLD_MACRO":"#FFD700"}).update_layout(bargap=0.4), use_container_width=True)
    with c2: st.metric(f"AVG {label} MINS", f"{round(df['duration_mins'].mean(),1)}m"); st.plotly_chart(px.pie(df, names='entry_info', hole=0.4, title="Setups"))
    p1, p2, p3, p4 = st.columns(4)
    for p, col, tit in zip([p1,p2,p3,p4], ['market','session','target','news_impact'], ['Markets','Sessions','Targets','News']):
        with p: st.plotly_chart(px.pie(df, names=col, hole=0.4, title=tit), use_container_width=True)

conn = sqlite3.connect('trading_vault.db')
all_t = pd.read_sql("SELECT * FROM trades", conn)
for i, name in enumerate(["LIVE", "TEST"]):
    with tabs[i+2]:
        df_sub = all_t[all_t['type'] == ("LIVE" if name=="LIVE" else "BACKTEST/DEMO")]
        for res in ["WIN", "BE", "LOSS"]:
            st.markdown(f"### {res} ANALYSIS")
            run_viz(df_sub[df_sub['result'] == res], res); st.divider()

# --- 5. HISTORY & COMPOUNDER ---
with tabs[4]:
    st.header("HISTORY")
    for _, r in all_t[::-1].iterrows():
        with st.expander(f"{r['date']} | {r['entry_time']} | {r['market']} | {r['result']}"):
            st.write(f"Sess: {r['session']} | Trg: {r['target']} | Dur: {r['duration_mins']}m | News: {r['news_impact']}")
            if r['screenshot']: st.image(r['screenshot'])
            if st.button(f"DELETE {r['id']}"): conn.execute("DELETE FROM trades WHERE id=?",(r['id'],)); conn.commit(); st.rerun()

with tabs[5]:
    st.header("PROJECTOR")
    p, r, y = st.number_input("START",5000), st.number_input("%/MO",5.0), st.number_input("YRS",5)
    bal, data = p, []
    for m in range(1, int(y*12)+1):
        bal *= (1+(r/100))
        if m%12==0: data.append({"Year":m//12, "Bal":round(bal,2)})
    st.line_chart(pd.DataFrame(data).set_index("Year"))
    st.table(pd.DataFrame(data))
conn.close()