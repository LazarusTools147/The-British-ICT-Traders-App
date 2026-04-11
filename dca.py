import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_supabase

def render_dca_tab():
    st.header("📉 PORTFOLIO (Cloud)")
    supabase = get_supabase()
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: cur_s = st.number_input("CUR SHARES", value=0.0)
    with c2: cur_a = st.number_input("CUR AVG", value=0.0)
    with c3: new_s = st.number_input("NEW SHARES", value=0.0)
    with c4: new_p = st.number_input("NEW PRICE", value=0.0)

    total_s = cur_s + new_s
    if total_s > 0:
        new_avg = ((cur_s * cur_a) + (new_s * new_p)) / total_s
        st.metric("NEW AVG PRICE", f"${round(new_avg, 2)}")
        
        with st.form("dca_form"):
            asset = st.text_input("ASSET NAME").upper()
            if st.form_submit_button("SAVE TO CLOUD"):
                data = {"asset_name": asset, "total_shares": total_s, "avg_price": new_avg, "last_updated": datetime.now().strftime("%Y-%m-%d")}
                supabase.table("portfolio").upsert(data).execute()
                st.success("VAULTED")

    resp = supabase.table("portfolio").select("*").execute()
    st.dataframe(pd.DataFrame(resp.data), use_container_width=True)