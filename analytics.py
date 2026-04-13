import streamlit as st
import pandas as pd
import plotly.express as px

def render_deep_dive_content(sub_df, title_prefix, color_hex, mode_label):
    """
    Recreates the exact high-density layout from your screenshots.
    FIXED: Added mode_label and title_prefix to keys to prevent duplicate IDs.
    """
    if sub_df.empty:
        st.info(f"No {title_prefix} data recorded yet.")
        return

    # --- TOP ROW: BAR CHART & VARIATION PIE ---
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.write(f"**{title_prefix} VOLUME BY TIME**")
        counts = sub_df['entry_time'].value_counts().sort_index()
        st.bar_chart(counts, color=color_hex)
        
    with col_side:
        avg_dur = sub_df['duration_mins'].mean() if 'duration_mins' in sub_df.columns else 0
        st.metric(f"AVG {title_prefix} TIME", f"{round(avg_dur, 1)}m")
        
        st.write("**Variations**")
        fig_var = px.pie(sub_df, names='model_var', hole=0) 
        fig_var.update_layout(showlegend=False, height=220, margin=dict(t=0, b=0, l=0, r=0))
        # Unique key ensures no crash
        st.plotly_chart(fig_var, use_container_width=True, key=f"var_pie_{mode_label}_{title_prefix}")

    # --- BOTTOM ROW: THE 4 DONUT ROW (Markets, Sessions, Timeframes, News) ---
    st.write("") 
    d1, d2, d3, d4 = st.columns(4)
    
    donut_fields = [
        (d1, 'market', 'Markets'),
        (d2, 'session', 'Sessions'),
        (d3, 'entry_tf', 'Timeframes'),
        (d4, 'news_impact', 'News')
    ]
    
    for col, field, title in donut_fields:
        with col:
            st.write(f"**{title}**")
            if field in sub_df.columns and not sub_df[field].dropna().empty:
                fig = px.pie(sub_df, names=field, hole=0.7)
                fig.update_layout(
                    showlegend=False, 
                    height=180, 
                    margin=dict(t=10, b=10, l=10, r=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                fig.update_traces(textposition='inside', textinfo='percent')
                # Unique key per donut per tab
                st.plotly_chart(fig, use_container_width=True, key=f"donut_{field}_{mode_label}_{title_prefix}")

def render_analytics(df, label):
    # --- 1. THE HEADER & GLOBAL KPI ---
    st.markdown(f'<h1 style="color: white;">📊 {label} PERFORMANCE</h1>', unsafe_allow_html=True)
    
    if df.empty:
        st.info("Vault empty. Secure trades in The Forge to generate analytics.")
        return

    m1, m2, m3, m4 = st.columns(4)
    wins = len(df[df['result'] == 'WIN'])
    total = len(df)
    win_rate = (wins / total * 100) if total > 0 else 0
    avg_dur = df['duration_mins'].mean() if 'duration_mins' in df.columns else 0
    avg_risk = df['risk_pc'].mean() if 'risk_pc' in df.columns else 0
    avg_rr = df['rr'].sum() 

    m1.metric("WIN RATE", f"{round(win_rate, 1)}%")
    m2.metric("AVG DUR", f"{round(avg_dur, 1)}m")
    m3.metric("AVG RISK", f"{round(avg_risk, 1)}%")
    m4.metric("TOTAL RR", f"{round(avg_rr, 1)}R")

    st.divider()

    # --- 2. MAIN KPI ROW (RR BAR + RESULT DONUT) ---
    c_left, c_right = st.columns([2, 1])
    with c_left:
        st.write("**EQUITY FLOW BY ENTRY TIME**")
        st.bar_chart(data=df, x='entry_time', y='rr', color='result')
    with c_right:
        st.write("**RESULT RATIO**")
        fig_res = px.pie(
            df, 
            names='result', 
            hole=0.6, 
            color='result',
            color_discrete_map={'WIN': '#00FF00', 'LOSS': '#FF0000', 'BE': '#808080'}
        )
        fig_res.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
        # Unique key for the main ratio donut
        st.plotly_chart(fig_res, use_container_width=True, key=f"main_ratio_{label}")

    # --- 3. THE THREE DEEP DIVES ---
    st.divider()
    
    # Winners Deep-Dive
    with st.expander("🏆 WINNERS DEEP-DIVE"):
        render_deep_dive_content(df[df['result'] == 'WIN'], "WIN", "#00FF00", label)
        
    # Losses Deep-Dive
    with st.expander("💀 LOSSES DEEP-DIVE"):
        render_deep_dive_content(df[df['result'] == 'LOSS'], "LOSS", "#FF0000", label)

    # Hindsight Deep-Dive
    with st.expander("🧠 HINDSIGHT DEEP-DIVE"):
        if 'hindsight' in df.columns:
            h_df = df[df['hindsight'] == True]
            render_deep_dive_content(h_df, "STUDY", "#00A2FF", label)
        else:
            st.warning("Hindsight column missing in database.")