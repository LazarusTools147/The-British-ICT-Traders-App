import streamlit as st
import pandas as pd
import plotly.express as px

def render_range_bar(sub_df, col_name, title, color):
    """Renders a high-density histogram grouped into 10-handle buckets."""
    if col_name in sub_df.columns and not sub_df[col_name].dropna().empty:
        # Create a copy to avoid modifying the original dataframe
        plot_df = sub_df[sub_df[col_name] > 0].copy()
        
        # This forces the histogram to bin in 10-handle increments
        fig = px.histogram(
            plot_df, 
            x=col_name, 
            title=title, 
            color_discrete_sequence=[color],
            nbins=20, # Initial suggestion for granularity
            labels={col_name: 'Handles', 'count': 'Freq'}
        )
        
        fig.update_traces(
            xbins=dict(start=0, end=1000, size=10), # Force 10-handle buckets
            texttemplate='%{y}', 
            textposition='outside'
        )
        
        fig.update_layout(
            showlegend=False,
            height=200, 
            margin=dict(t=30, b=10, l=0, r=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, dtick=20), # Labels every 20 handles for clarity
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
        )
        st.plotly_chart(fig, use_container_width=True, key=f"bar_{col_name}_{title}_{color}")
    else:
        st.caption(f"No {title} data")

def render_deep_dive_content(sub_df, title_prefix, color_hex, mode_label):
    """Rebuilds the deep dive with Donut charts, Volatility Averages, and the 5-Bar Row."""
    if sub_df.empty:
        st.info(f"No {title_prefix} data recorded yet.")
        return

    # --- TOP ROW: VOLUME & TOP MODEL ---
    col_main, col_side = st.columns([2, 1])
    with col_main:
        st.write(f"**{title_prefix} VOLUME BY TIME**")
        counts = sub_df['entry_time'].value_counts().sort_index()
        st.bar_chart(counts, color=color_hex)
    with col_side:
        avg_dur = sub_df['duration_mins'].mean() if 'duration_mins' in sub_df.columns else 0
        st.metric(f"AVG {title_prefix} TIME", f"{round(avg_dur, 1)}m")
        if not sub_df['model_name'].empty:
            st.write(f"**Top Model:** `{sub_df['model_name'].mode()[0]}`")

    # --- NEW: VOLATILITY AVERAGES ROW ---
    st.divider()
    st.write(f"### 📈 AVG SESSION SIZE IN {title_prefix}S")
    a1, a2, a3, a4, a5 = st.columns(5)
    sessions = [('cbdr_size', 'CBDR', a1), ('asia_size', 'ASIA', a2), 
                ('london_size', 'LON', a3), ('ny_am_size', 'NYAM', a4), ('ny_pm_size', 'NYPM', a5)]
    
    for col_db, label, slot in sessions:
        if col_db in sub_df.columns:
            # Only average values greater than zero
            avg_val = sub_df[sub_df[col_db] > 0][col_db].mean()
            slot.metric(f"AVG {label}", f"{round(avg_val, 1)}H" if pd.notnull(avg_val) else "0H")

    # --- MIDDLE ROW: THE 6-DONUT GRID ---
    st.divider()
    d1, d2, d3, d4, d5, d6 = st.columns(6)
    donut_fields = [
        (d1, 'model_var', 'Variations'), (d2, 'market', 'Markets'),
        (d3, 'session', 'Sessions'), (d4, 'entry_tf', 'Timeframes'),
        (d5, 'news_impact', 'News'), (d6, 'entry_type', 'Entry Type')
    ]
    for col, field, title in donut_fields:
        with col:
            st.write(f"**{title}**")
            if field in sub_df.columns and not sub_df[field].dropna().empty:
                fig = px.pie(sub_df, names=field, hole=0.7, color_discrete_sequence=px.colors.qualitative.Bold)
                fig.update_layout(showlegend=False, height=160, margin=dict(t=10, b=10, l=5, r=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=9)
                st.plotly_chart(fig, use_container_width=True, key=f"dn_{field}_{mode_label}_{title_prefix}")
            else:
                st.caption("No Data")

    # --- BOTTOM ROW: 5-BAR VOLATILITY ROW ---
    st.write("### 📏 SESSION VOLATILITY DISTRIBUTION (10H BUCKETS)")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: render_range_bar(sub_df, 'cbdr_size', 'CBDR', "#FFFFFF")
    with c2: render_range_bar(sub_df, 'asia_size', 'ASIA', "#00FFCC")
    with c3: render_range_bar(sub_df, 'london_size', 'LONDON', "#00A2FF")
    with c4: render_range_bar(sub_df, 'ny_am_size', 'NY AM', "#FFB700")
    with c5: render_range_bar(sub_df, 'ny_pm_size', 'NY PM', "#FF4B4B")

def render_analytics(df, label):
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
    c_left, c_right = st.columns([2, 1])
    with c_left:
        st.write("**EQUITY FLOW BY ENTRY TIME**")
        st.bar_chart(data=df, x='entry_time', y='rr', color='result')
    with c_right:
        st.write("**RESULT RATIO**")
        fig_res = px.pie(df, names='result', hole=0.6, color='result', color_discrete_map={'WIN': '#00FF00', 'LOSS': '#FF0000', 'BE': '#808080'})
        fig_res.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
        st.plotly_chart(fig_res, use_container_width=True, key=f"main_ratio_{label}")

    st.divider()
    with st.expander("🏆 WINNERS"): 
        win_execs = df[(df['result'] == 'WIN') & (df['hindsight'].astype(str).str.lower() == 'false')]
        render_deep_dive_content(win_execs, "WIN", "#00FF00", label)
    with st.expander("💀 LOSSES"): 
        loss_execs = df[(df['result'] == 'LOSS') & (df['hindsight'].astype(str).str.lower() == 'false')]
        render_deep_dive_content(loss_execs, "LOSS", "#FF0000", label)
    with st.expander("🧠 HINDSIGHT DEEP-DIVE"):
        if 'hindsight' in df.columns:
            h_df = df[df['hindsight'] == True]
            render_deep_dive_content(h_df, "STUDY", "#00A2FF", label)