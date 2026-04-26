import streamlit as st
import pandas as pd
import plotly.express as px

def render_range_bar(sub_df, col_name, title, color, unique_key):
    """Renders a histogram grouped by the market-specific bucket size."""
    if col_name in sub_df.columns and not sub_df[col_name].dropna().empty:
        plot_df = sub_df[sub_df[col_name] > 0].copy()
        
        # Pull the bucket size from session state (set in app.py sidebar)
        b_size = st.session_state.get('bucket_size', 10.0)
        
        fig = px.histogram(
            plot_df, 
            x=col_name, 
            title=title, 
            color_discrete_sequence=[color],
            labels={col_name: 'Handles', 'count': 'Freq'}
        )
        
        fig.update_traces(
            xbins=dict(start=0, end=1000, size=b_size),
            texttemplate='%{y}', 
            textposition='outside'
        )
        
        fig.update_layout(
            showlegend=False,
            height=200, 
            margin=dict(t=30, b=10, l=0, r=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
        )
        # THE ULTIMATE KEY: Ensures no collision across different tabs or sessions
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{unique_key}_{col_name}_{color.replace('#','')}")
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
        st.write(f"**{title_prefix} VOLUME BY TIME (15m BUCKETS)**")
        fig_vol = px.histogram(sub_df, x='entry_time', color_discrete_sequence=[color_hex])
        fig_vol.update_layout(
            height=250, 
            margin=dict(t=10, b=10, l=0, r=0), 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_vol, use_container_width=True, key=f"volume_plot_{mode_label}_{title_prefix}")
        
    with col_side:
        avg_dur = sub_df['duration_mins'].mean() if 'duration_mins' in sub_df.columns else 0
        st.metric(f"AVG {title_prefix} TIME", f"{round(avg_dur, 1)}m")
        if not sub_df['model_name'].empty:
            st.write(f"**Top Model:** `{sub_df['model_name'].mode()[0]}`")

    # --- VOLATILITY AVERAGES ROW ---
    st.divider()
    st.write(f"### 📈 AVG SESSION SIZE IN {title_prefix}S")
    a1, a2, a3, a4, a5 = st.columns(5)
    sessions = [
        ('cbdr_size', 'CBDR', a1), ('asia_size', 'ASIA', a2), 
        ('london_size', 'LON', a3), ('ny_am_size', 'NYAM', a4), ('ny_pm_size', 'NYPM', a5)
    ]
    
    for col_db, label, slot in sessions:
        if col_db in sub_df.columns:
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
                st.plotly_chart(fig, use_container_width=True, key=f"donut_{field}_{mode_label}_{title_prefix}")
            else:
                st.caption("No Data")

    # --- BOTTOM ROW: 5-BAR VOLATILITY ROW ---
    st.write(f"### 📏 SESSION VOLATILITY DISTRIBUTION ({st.session_state.get('bucket_size', 10.0)}H BUCKETS)")
    c1, c2, c3, c4, c5 = st.columns(5)
    # Passing extremely specific keys to ensure uniqueness
    with c1: render_range_bar(sub_df, 'cbdr_size', 'CBDR', "#FFFFFF", f"key_{mode_label}_{title_prefix}_cbdr")
    with c2: render_range_bar(sub_df, 'asia_size', 'ASIA', "#00FFCC", f"key_{mode_label}_{title_prefix}_asia")
    with c3: render_range_bar(sub_df, 'london_size', 'LONDON', "#00A2FF", f"key_{mode_label}_{title_prefix}_lon")
    with c4: render_range_bar(sub_df, 'ny_am_size', 'NY AM', "#FFB700", f"key_{mode_label}_{title_prefix}_am")
    with c5: render_range_bar(sub_df, 'ny_pm_size', 'NY PM', "#FF4B4B", f"key_{mode_label}_{title_prefix}_pm")

def render_analytics(df, label):
    st.markdown(f'<h1 style="color: white;">📊 {label} PERFORMANCE</h1>', unsafe_allow_html=True)
    if df.empty:
        st.info("Vault empty."); return

    # --- 1. THE FIREWALL: SPLIT PERFORMANCE VS HINDSIGHT ---
    is_hind = df['hindsight'] if 'hindsight' in df.columns else False
    perf_df = df[is_hind == False].copy()
    study_df = df[is_hind == True].copy()

    # --- MATH ENGINE ---
    perf_df['adj_rr'] = perf_df.apply(lambda x: -abs(x['rr']) if x['result'] == 'LOSS' else abs(x['rr']) if x['result'] == 'WIN' else 0, axis=1)
    perf_df['net_return'] = perf_df.apply(lambda x: -(x['risk_pc']) if x['result'] == 'LOSS' else (x['rr'] * x['risk_pc']) if x['result'] == 'WIN' else 0, axis=1)
    
    total_rr = perf_df['adj_rr'].sum()
    total_net = perf_df['net_return'].sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    wins = len(perf_df[perf_df['result'] == 'WIN'])
    total = len(perf_df)
    win_rate = (wins / total * 100) if total > 0 else 0
    
    m1.metric("WIN RATE", f"{round(win_rate, 1)}%")
    m2.metric("STUDY COUNT", len(study_df))
    m3.metric("AVG RISK", f"{round(perf_df['risk_pc'].mean(), 1)}%" if total > 0 else "0%")
    m4.metric("TOTAL RR", f"{round(total_rr, 1)}R", delta=f"{round(total_rr, 1)}R")
    m5.metric("NET GROWTH", f"{round(total_net, 2)}%", delta=f"{round(total_net, 2)}%")

    st.divider()
    
    c_left, c_right = st.columns([2, 1])
    with c_left:
        st.write("**RR PERFORMANCE DISTRIBUTION**")
        fig_rr = px.histogram(perf_df, x='adj_rr', color='result', color_discrete_map={'WIN': '#00FF00', 'LOSS': '#FF0000', 'BE': '#808080'})
        fig_rr.update_traces(xbins=dict(size=1))
        fig_rr.update_layout(height=300, margin=dict(t=10, b=10, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_rr, use_container_width=True, key=f"rr_dist_chart_{label}")
        
    with c_right:
        st.write("**RESULT RATIO**")
        fig_res = px.pie(perf_df, names='result', hole=0.6, color='result', color_discrete_map={'WIN': '#00FF00', 'LOSS': '#FF0000', 'BE': '#808080'})
        fig_res.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
        st.plotly_chart(fig_res, use_container_width=True, key=f"main_pie_ratio_{label}")

    st.divider()
    
    # --- DEEP DIVES ---
    with st.expander("🏆 PERFORMANCE WINNERS"): 
        win_execs = perf_df[perf_df['result'] == 'WIN']
        render_deep_dive_content(win_execs, "WIN", "#00FF00", label)
        
    with st.expander("💀 PERFORMANCE LOSSES"): 
        loss_execs = perf_df[perf_df['result'] == 'LOSS']
        render_deep_dive_content(loss_execs, "LOSS", "#FF0000", label)
        
    with st.expander("🧠 HINDSIGHT DEEP-DIVE"):
        if not study_df.empty:
            render_deep_dive_content(study_df, "STUDY", "#00A2FF", label)
        else:
            st.info("No Hindsight studies found.")