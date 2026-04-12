import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def create_donut(df, column, title):
    """Generates the professional Donut charts from your old build."""
    if column not in df.columns or df[column].dropna().empty:
        return None
    counts = df[column].value_counts().reset_index()
    counts.columns = [column, 'count']
    fig = px.pie(counts, values='count', names=column, hole=0.7, 
                 color_discrete_sequence=px.colors.sequential.RdBu)
    fig.update_layout(
        showlegend=False,
        title={'text': title, 'y': 0.9, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'},
        margin=dict(t=30, b=10, l=10, r=10),
        height=220,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white", size=10)
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def render_deep_dive(df, label, color_scale):
    """The engine that recreates your Winners/Losses/Hindsight layout."""
    if df.empty:
        st.info(f"No {label} data available for this session.")
        return

    # Top Row: Stats & Variations
    c1, c2 = st.columns([2, 1])
    with c1:
        st.write("**Model Performance (Volume)**")
        st.bar_chart(df['model_name'].value_counts(), color=color_scale[0])
    with c2:
        avg_dur = df['duration_mins'].mean() if 'duration_mins' in df.columns else 0
        st.metric(f"AVG {label} TIME", f"{round(avg_dur, 1)}m")
        st.write("**Variations**")
        var_fig = px.pie(df, names='model_var', hole=0.4, color_discrete_sequence=color_scale)
        var_fig.update_layout(showlegend=False, height=200, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(var_fig, use_container_width=True)

    # Bottom Row: The 4 Donuts
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        f1 = create_donut(df, 'market', 'Markets')
        if f1: st.plotly_chart(f1, use_container_width=True)
    with d2:
        f2 = create_donut(df, 'session', 'Sessions')
        if f2: st.plotly_chart(f2, use_container_width=True)
    with d3:
        f3 = create_donut(df, 'entry_tf', 'Timeframes')
        if f3: st.plotly_chart(f3, use_container_width=True)
    with d4:
        f4 = create_donut(df, 'news_impact', 'News')
        if f4: st.plotly_chart(f4, use_container_width=True)

def render_analytics(df, label):
    st.title(f"📈 GLOBAL KPI: {label}")
    
    if df.empty:
        st.info("Vault empty. Secure trades in The Forge to generate analytics.")
        return

    # --- 1. TOP LEVEL METRICS ---
    m1, m2, m3, m4 = st.columns(4)
    wins = len(df[df['result'] == 'WIN'])
    total = len(df)
    win_rate = (wins / total * 100) if total > 0 else 0
    avg_dur = df['duration_mins'].mean() if 'duration_mins' in df.columns else 0
    avg_risk = df['risk_pc'].mean() if 'risk_pc' in df.columns else 0
    avg_rr = df['rr'].mean() if 'rr' in df.columns else 0

    m1.metric("WIN RATE", f"{round(win_rate, 1)}%")
    m2.metric("AVG DUR", f"{round(avg_dur, 1)}m")
    m3.metric("AVG RISK", f"{round(avg_risk, 2)}%")
    m4.metric("AVG RR", f"{round(avg_rr, 2)}R")

    # --- 2. THE EQUITY CURVE & PIE MIX ---
    st.divider()
    g1, g2 = st.columns([2, 1])
    with g1:
        df['date'] = pd.to_datetime(df['date'])
        curve = df.sort_values('date').copy()
        curve['cum_rr'] = curve['rr'].cumsum()
        fig_curve = px.line(curve, x='date', y='cum_rr', title="CUMULATIVE RR GROWTH")
        fig_curve.update_traces(line_color='#00FF00')
        st.plotly_chart(fig_curve, use_container_width=True)
    with g2:
        st.write("**RESULT DISTRIBUTION**")
        res_fig = px.pie(df, names='result', hole=0.5, color_discrete_map={'WIN': '#00FF00', 'LOSS': '#FF0000', 'BE': '#808080'})
        st.plotly_chart(res_fig, use_container_width=True)

    # --- 3. DEEP DIVE TABS ---
    st.divider()
    tabs = st.tabs(["🏆 WINNERS DEEP-DIVE", "💀 LOSSES DEEP-DIVE", "⚖️ BE DEEP-DIVE", "🧠 HINDSIGHT DEEP-DIVE"])

    with tabs[0]:
        render_deep_dive(df[df['result'] == 'WIN'], "WIN", px.colors.sequential.Greens_r)
    
    with tabs[1]:
        render_deep_dive(df[df['result'] == 'LOSS'], "LOSS", px.colors.sequential.Reds_r)
        
    with tabs[2]:
        render_deep_dive(df[df['result'] == 'BE'], "BE", px.colors.sequential.Greys_r)

    with tabs[3]:
        # Hindsight Deep Dive logic
        if 'hindsight' in df.columns:
            h_df = df[df['hindsight'] == True]
            render_deep_dive(h_df, "STUDY", px.colors.sequential.Purples_r)
        else:
            st.warning("Hindsight column missing in database.")