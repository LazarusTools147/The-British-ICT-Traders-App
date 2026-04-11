import streamlit as st
import plotly.express as px
import pandas as pd

def render_analytics(df, suffix):
    if df.empty:
        st.info(f"📊 NO {suffix} DATA.")
        return

    st.markdown(f"## 📈 {suffix} KPI SUMMARY")
    k1, k2, k3, k4 = st.columns(4)
    with k1: 
        wr = (len(df[df['result']=='WIN'])/len(df))*100 if len(df) > 0 else 0
        st.metric("WIN RATE", f"{round(wr, 1)}%")
    with k2: st.metric("AVG DUR", f"{round(df['duration_mins'].mean(),1)}m")
    with k3: st.metric("AVG RISK", f"{round(df['risk_pc'].mean(),2)}%")
    with k4: st.metric("AVG RR", f"{round(df['rr'].mean(),2)}R")

    st.divider()
    colors = {'WIN':'#00ff00', 'LOSS':'#ff0000', 'BE':'#FF8C00'}
    c_bar, c_pie = st.columns([3, 1])
    
    with c_bar:
        st.plotly_chart(px.bar(df.sort_values('date'), x='date', y='rr', color='result', color_discrete_map=colors), use_container_width=True, key=f"bar_{suffix}")
    with c_pie:
        st.plotly_chart(px.pie(df, names='result', hole=0.5, color='result', color_discrete_map=colors), use_container_width=True, key=f"pie_{suffix}")

    if suffix == "TEST":
        st.divider()
        with st.expander("👁️ HINDSIGHT MODEL ANALYSIS"):
            h_df = df[df['result'] == 'WIN']
            if not h_df.empty:
                hc1, hc2 = st.columns(2)
                with hc1: st.plotly_chart(px.histogram(h_df, x="entry_time", title="Ideal Windows"), use_container_width=True, key="h_time")
                with hc2: st.plotly_chart(px.pie(h_df, names="model_var", title="Best Variations"), use_container_width=True, key="h_var")