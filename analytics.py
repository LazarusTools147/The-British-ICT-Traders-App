import streamlit as st
import pandas as pd
import plotly.express as px

def render_deep_dive_content(sub_df, title_prefix, color_hex, mode_label):
    """
    Rebuilds the deep dive with a high-density 5+ donut layout.
    Features: Model Variation, Market, Session, TF, News, and Entry Type.
    """
    if sub_df.empty:
        st.info(f"No {title_prefix} data recorded yet.")
        return

    # --- TOP ROW: BAR CHART & STATS ---
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.write(f"**{title_prefix} VOLUME BY TIME**")
        counts = sub_df['entry_time'].value_counts().sort_index()
        st.bar_chart(counts, color=color_hex)
        
    with col_side:
        avg_dur = sub_df['duration_mins'].mean() if 'duration_mins' in sub_df.columns else 0
        st.metric(f"AVG {title_prefix} TIME", f"{round(avg_dur, 1)}m")
        # Added a small summary metric for the top model in this specific deep dive
        if not sub_df['model_name'].empty:
            st.write(f"**Top Model:** `{sub_df['model_name'].mode()[0]}`")

    # --- BOTTOM ROW: THE 6-DONUT GRID ---
    # We use 6 columns to ensure Model Variation and Entry Type fit perfectly
    st.write("") 
    d1, d2, d3, d4, d5, d6 = st.columns(6)
    
    donut_fields = [
        (d1, 'model_var', 'Variations'),
        (d2, 'market', 'Markets'),
        (d3, 'session', 'Sessions'),
        (d4, 'entry_tf', 'Timeframes'),
        (d5, 'news_impact', 'News'),
        (d6, 'entry_type', 'Entry Type')
    ]
    
    for col, field, title in donut_fields:
        with col:
            st.write(f"**{title}**")
            if field in sub_df.columns and not sub_df[field].dropna().empty:
                # Optimized donut: hole=0.7, Bold colors, and Auto-Labels
                fig = px.pie(sub_df, names=field, hole=0.7, color_discrete_sequence=px.colors.qualitative.Bold)
                fig.update_layout(
                    showlegend=False, 
                    height=160, 
                    margin=dict(t=10, b=10, l=5, r=5),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                # This ensures you can see the labels and % without hovering
                fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=9)
                st.plotly_chart(fig, use_container_width=True, key=f"donut_{field}_{mode_label}_{title_prefix}")
            else:
                st.caption("No Data")

def render_analytics(df, label):
    with st.container():
        st.markdown(f'<h1 style="color: white;">📊 {label} PERFORMANCE</h1>', unsafe_allow_html=True)
        
        if df.empty:
            st.info("Vault empty. Secure trades in The Forge to generate analytics.")
            return

        m1, m2, m3, m4 = st.columns(4)
        wins = len(df[df['result'] == 'WIN'])
        total = len(df)
        win_rate = (wins / total * 100) if total > 0 else 0
        
        m1.metric("WIN RATE", f"{round(win_rate, 1)}%")
        m2.metric("AVG DUR", f"{round(df['duration_mins'].mean(), 1)}m")
        m3.metric("AVG RISK", f"{round(df['risk_pc'].mean(), 1)}%")
        m4.metric("TOTAL RR", f"{round(df['rr'].sum(), 1)}R")

        st.divider()

        # --- 2. MAIN KPI ROW ---
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
            st.plotly_chart(fig_res, use_container_width=True, key=f"main_ratio_{label}")

        # --- 3. THE THREE DEEP DIVES ---
        st.divider()
        
        with st.expander("🏆 WINNERS"): 
        # This checks if it's False, 0, or the string 'false'
        win_execs = df[(df['result'] == 'WIN') & (df['hindsight'].astype(str).str.lower() == 'false')]
        render_deep_dive_content(win_execs, "WIN", "#00FF00", label)
        
    with st.expander("💀 LOSSES"): 
        # This does the same for losses
        loss_execs = df[(df['result'] == 'LOSS') & (df['hindsight'].astype(str).str.lower() == 'false')]
        render_deep_dive_content(loss_execs, "LOSS", "#FF0000", label)

        with st.expander("🧠 HINDSIGHT DEEP-DIVE"):
            if 'hindsight' in df.columns:
                h_df = df[df['hindsight'] == True]
                render_deep_dive_content(h_df, "STUDY", "#00A2FF", label)
            else:
                st.warning("Hindsight column missing in database.")