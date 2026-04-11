import streamlit as st
import plotly.express as px
import pandas as pd

def render_analytics(df, suffix):
    """
    Performance visualization engine.
    suffix: "LIVE" or "TEST" to ensure chart key uniqueness.
    """
    if df.empty:
        st.info(f"📊 NO {suffix} DATA ARCHIVED.")
        return

    # --- 1. GLOBAL KPI ---
    st.markdown(f"## 📈 {suffix} GLOBAL KPI")
    k1, k2, k3, k4 = st.columns(4)
    
    with k1: 
        win_rate = (len(df[df['result']=='WIN'])/len(df))*100
        st.metric("WIN RATE", f"{round(win_rate, 1)}%")
    with k2: 
        st.metric("AVG DUR", f"{round(df['duration_mins'].mean(),1)}m")
    with k3: 
        st.metric("AVG RISK", f"{round(df['risk_pc'].mean(),2)}%")
    with k4: 
        st.metric("AVG RR", f"{round(df['rr'].mean(),2)}R")

    st.divider()

    # --- 2. PERFORMANCE CHARTS ---
    colors = {'WIN':'#00ff00', 'LOSS':'#ff0000', 'BE':'#FF8C00'}
    c_bar, c_pie = st.columns([3, 1])
    
    with c_bar:
        st.plotly_chart(px.bar(df.sort_values('entry_time'), x='entry_time', y='rr', color='result', color_discrete_map=colors).update_layout(bargap=0.3), use_container_width=True, key=f"bar_{suffix}")
    with c_pie:
        st.plotly_chart(px.pie(df, names='result', hole=0.5, color='result', color_discrete_map=colors), use_container_width=True, key=f"pie_{suffix}")

    # --- 3. SEGMENTED DEEP-DIVES ---
    def draw_seg(res_t, label, emoji):
        sdf = df[df['result'] == res_t]
        if sdf.empty: return
        with st.expander(f"{emoji} {label} DEEP-DIVE"):
            sk1, sk2 = st.columns([3, 1])
            with sk1:
                st.plotly_chart(px.bar(sdf.sort_values('entry_time'), x='entry_time', title="Time Distribution"), use_container_width=True, key=f"time_{res_t}_{suffix}")
            with sk2:
                st.plotly_chart(px.pie(sdf, names='model_var', title="Variations"), use_container_width=True, key=f"var_{res_t}_{suffix}")
            
            p1, p2, p3, p4 = st.columns(4)
            p_args = dict(hole=0.4, width=220, height=220)
            with p1: st.plotly_chart(px.pie(sdf, names='market', title="Markets", **p_args), use_container_width=True, key=f"mkt_{res_t}_{suffix}")
            with p2: st.plotly_chart(px.pie(sdf, names='session', title="Sessions", **p_args), use_container_width=True, key=f"sess_{res_t}_{suffix}")
            with p3: st.plotly_chart(px.pie(sdf, names='entry_tf', title="Timeframes", **p_args), use_container_width=True, key=f"tf_{res_t}_{suffix}")
            with p4: st.plotly_chart(px.pie(sdf, names='news_impact', title="News", **p_args), use_container_width=True, key=f"nws_{res_t}_{suffix}")

    draw_seg("WIN", "WINNERS", "🏆")
    draw_seg("BE", "BREAK EVEN", "🛡️")
    draw_seg("LOSS", "LOSSES", "💀")

    # --- 4. HINDSIGHT ANALYSIS (TEST DATA ONLY) ---
    if suffix == "TEST":
        st.divider()
        with st.expander("👁️ HINDSIGHT MODEL ANALYSIS"):
            st.info("Performance analysis based on the ideal model execution (Hindsight).")
            # Filter for Winners specifically to analyze perfect setup traits
            h_df = df[df['result'] == 'WIN']
            if not h_df.empty:
                hc1, hc2 = st.columns(2)
                with hc1:
                    st.plotly_chart(px.histogram(h_df, x="entry_time", title="Ideal Execution Times"), use_container_width=True, key="hindsight_time")
                with hc2:
                    st.plotly_chart(px.pie(h_df, names="model_var", title="Highest Prob Variations"), use_container_width=True, key="hindsight_var")
            else:
                st.write("Record 'WIN' trades in backtesting to generate hindsight data.")