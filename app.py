import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import datetime

# 1. COURSE DATA
CHISLEHURST_MAP = {
    1: {"par": 5, "si": 11}, 2: {"par": 4, "si": 7},  3: {"par": 3, "si": 3},
    4: {"par": 4, "si": 15}, 5: {"par": 3, "si": 17}, 6: {"par": 4, "si": 1},
    7: {"par": 3, "si": 13}, 8: {"par": 3, "si": 5},  9: {"par": 4, "si": 9},
    10: {"par": 3, "si": 12}, 11: {"par": 4, "si": 4}, 12: {"par": 3, "si": 18},
    13: {"par": 3, "si": 8},  14: {"par": 5, "si": 2}, 15: {"par": 4, "si": 14},
    16: {"par": 4, "si": 10}, 17: {"par": 3, "si": 6}, 18: {"par": 4, "si": 16}
}
MATCHES = ["Match 1", "Match 2", "Match 3", "Match 4", "Match 5"]

st.set_page_config(page_title="Ryder Cup 2026", layout="centered")

# 2. DATABASE CONNECTION
@st.cache_resource
def get_engine():
    try:
        s = st.secrets["connections"]["tidb"]
        conn_url = f"mysql+pymysql://{s['username']}:{s['password']}@{s['host']}:{s['port']}/{s['database']}?ssl_ca=/etc/ssl/certs/ca-certificates.crt"
        return create_engine(conn_url, pool_pre_ping=True, pool_recycle=3600)
    except Exception as e:
        return None

engine = get_engine()

# --- DATA HELPERS ---
def get_all_scores():
    if not engine: return pd.DataFrame()
    try:
        with engine.connect() as conn:
            return pd.read_sql("SELECT * FROM ryder_scores", conn)
    except:
        return pd.DataFrame()

def calculate_match_result(df, match_name):
    m_data = df[df['match_id'] == match_name]
    if m_data.empty: return "All Square", 0.5, 0.5 
    
    g_wins = len(m_data[m_data['winner'] == 'Gabe'])
    b_wins = len(m_data[m_data['winner'] == 'Bot.'])
    
    if g_wins > b_wins:
        return f"Gabe {g_wins - b_wins} UP", 1.0, 0.0
    elif b_wins > g_wins:
        return f"Bot. {b_wins - g_wins} UP", 0.0, 1.0
    else:
        return "All Square", 0.5, 0.5

# --- DASHBOARD FRAGMENT (Updates every 60s) ---
@st.fragment(run_every=60)
def show_dashboard():
    all_data = get_all_scores()
    proj_g, proj_b = 0.0, 0.0

    for m in MATCHES:
        _, pg, pb = calculate_match_result(all_data, m)
        proj_g += pg
        proj_b += pb

    # 1. FIXED HEADER
    st.markdown(f"""
    <div style="background-color: #1e3d59; padding: 15px; border-radius: 10px; border: 2px solid #ffc13b; margin-bottom: 20px; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 24px;">🏆 RYDER CUP 2026</h1>
        <p style="color: #ffc13b; font-size: 20px; font-weight: bold; margin: 5px 0;">
            PROJECTED: Team Gabe {proj_g} — {proj_b} Team Bot.
        </p>
        <p style="color: #bdc3c7; font-size: 11px; margin: 0;">
            Auto-Sync Active • {datetime.datetime.now().strftime('%H:%M:%S')}
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_in, tab_track = st.tabs(["⛳ RECORD", "📊 TRACKER"])

    with tab_in:
        match_choice = st.selectbox("Select Match", MATCHES)
        current_status, _, _ = calculate_match_result(all_data, match_choice)
        
        # Centered "This match" status
        st.markdown(f"<div style='text-align: center; color: #1e3d59; font-size: 20px; font-weight: bold; margin: 10px 0;'>This match: {current_status}</div>", unsafe_allow_html=True)
        
        if 'h_idx' not in st.session_state: st.session_state.h_idx = 1
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1: 
            if st.button("⬅️", use_container_width=True, key="p1"):
                st.session_state.h_idx = max(1, st.session_state.h_idx - 1)
                st.rerun()
        with c2: 
            st.markdown(f"<h3 style='text-align: center; margin: 0;'>HOLE {st.session_state.h_idx}</h3>", unsafe_allow_html=True)
