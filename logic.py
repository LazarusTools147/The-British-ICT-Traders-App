import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_connection
from datetime import datetime

def render_forge():
    conn = get_connection(); models = pd.read_sql("SELECT name FROM models", conn)['name'].tolist(); conn.close()
    if not models: st.warning("Create a Model first."); return
    with st.form("forge", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1: env = st.radio("ENV", ["LIVE", "TEST"], horizontal=True); mod = st.selectbox("MODEL", models); mkt = st.text_input("MKT").upper()
        with c2: tm = st.text_input("TIME"); tf = st.text_input("TF").upper(); dur = st.number_input("MINS", 1, 500, 15)
        with c3: res = st.selectbox("RESULT", ["WIN", "LOSS", "BE"]); rsk = st.number_input("RISK%", 1.0); rr = st.number_input("RR", 2.0)
        nts = st.text_area("NOTES"); img = st.file_uploader("CHART")
        if st.form_submit_button("SAVE"):
            img_d = img.read() if img else None; conn = get_connection()
            conn.execute("INSERT INTO trades (model_name,model_var,type,market,entry_time,entry_tf,result,risk_pc,rr,notes,date,duration_mins,screenshot) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         (mod, "", env, mkt, tm, tf, res, rsk, rr, nts, datetime.now().strftime("%Y-%m-%d"), dur, img_d))
            conn.commit(); conn.close(); st.success("SAVED")

def render_dca():
    st.header("📉 DCA CALCULATOR")
    c1, c2 = st.columns(2)
    with c1:
        cur_s = st.number_input("Current Shares", 0.0); cur_a = st.number_input("Current Avg", 0.0)
        new_s = st.number_input("New Shares", 0.0); new_p = st.number_input("New Price", 0.0)
        if (cur_s + new_s) > 0:
            new_avg = ((cur_s * cur_a) + (new_s * new_p)) / (cur_s + new_s)
            st.metric("New Average", f"${round(new_avg, 2)}")
    with c2:
        asset = st.text_input("Asset Name").upper()
        if st.button("Save Position"):
            conn = get_connection(); conn.execute("INSERT OR REPLACE INTO portfolio VALUES (?,?,?)", (asset, cur_s+new_s, new_avg)); conn.commit(); conn.close(); st.success("Vaulted")

def render_analytics(df, suffix):
    if df.empty: st.info("No Data."); return
    st.metric("WIN RATE", f"{round((len(df[df['result']=='WIN'])/len(df))*100,1)}%")
    colors = {'WIN':'#00ff00', 'LOSS':'#ff0000', 'BE':'#FF8C00'}
    st.plotly_chart(px.bar(df, x='entry_time', y='rr', color='result', color_discrete_map=colors), use_container_width=True, key=f"bar_{suffix}")