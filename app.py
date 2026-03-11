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
PAIRS_MATCHES = [f"Pairs Match {i}" for i in range(1, 6)]
SINGLES_MATCHES = [f"Singles Match {i}" for i in range(1, 11)]

st.set_page_config(page_title="Ryder Cup 2026", layout="centered")

# 2. DATABASE CONNECTION
@st.cache_resource
def get_engine():
    try:
        s = st.secrets["connections"]["tidb"]
        conn_url = f"mysql+pymysql://{s['username']}:{s['password']}@{s['host']}:{s['port']}/{s['database']}?ssl_ca=/etc/ssl/certs/ca-certificates.crt"
        return create_engine(conn_url, pool_pre_ping=True, pool_recycle=300)
    except Exception: return None

engine = get_engine()

# --- DATA HELPERS ---
def get_all_scores():
    if not engine: return pd.DataFrame()
    try:
        with engine.connect() as conn: return pd.read_sql("SELECT * FROM ryder_scores", conn)
    except Exception: return pd.DataFrame()

def calculate_session_result(df, match_id, holes):
    m_data = df[(df['match_id'] == match_id) & (df['hole'].isin(holes))]
    if m_data.empty: return "All Square", 0.5, 0.5
    
    g_wins = len(m_data[m_data['winner'] == 'Gabe'])
    b_wins = len(m_data[m_data['winner'] == 'Bot.'])
    diff = abs(g_wins - b_wins)
    last_played = m_data['hole'].max()
    max_hole = max(holes)
    remaining = max_hole - last_played
    
    if diff > remaining:
        w = "Gabe" if g_wins > b_wins else "Bot."
        res = f"{w} Won {diff}&{remaining}" if remaining > 0 else f"{w} {diff} UP"
        return res, (1.0 if w == "Gabe" else 0.0), (1.0 if w == "Bot." else 0.0)
    
    if last_played == max_hole:
        if diff == 0: return "Halved", 0.5, 0.5
        w = "Gabe" if g_wins > b_wins else "Bot."
        return f"{w} {diff} UP", (1.0 if w == "Gabe" else 0.0), (1.0 if w == "Bot." else 0.0)

    if g_wins > b_wins: return f"Gabe {diff} UP", 1.0, 0.0
    if b_wins > g_wins: return f"Bot. {diff} UP", 0.0, 1.0
    return "All Square", 0.5, 0.5

# --- LOAD DATA & TOTALS ---
all_data = get_all_scores()
proj_g, proj_b = 0.0, 0.0

for m in PAIRS_MATCHES:
    _, g1, b1 = calculate_session_result(all_data, m, range(1, 10))
    _, g2, b2 = calculate_session_result(all_data, m, range(10, 19))
    proj_g += (g1 + g2); proj_b += (b1 + b2)

for m in SINGLES_MATCHES:
    _, gs, bs = calculate_session_result(all_data, m, range(1, 10))
    proj_g += gs; proj_b += bs

# --- UI HEADER ---
st.markdown(f"""
<div style="background-color: #1e3d59; padding: 15px; border-radius: 10px; border: 2px solid #ffc13b; margin-bottom: 10px; text-align: center;">
    <h1 style="color: white; margin: 0; font-size: 24px;">🏆 RYDER CUP 2026</h1>
    <p style="color: #ffc13b; font-size: 20px; font-weight: bold; margin: 5px 0;">
        PROJECTED TOTAL: Gabe {proj_g} — {proj_b} Bot.
    </p>
    <p style="color: #bdc3c7; font-size: 11px; margin: 0;">Synced: {datetime.datetime.now().strftime('%H:%M:%S')}</p>
</div>
""", unsafe_allow_html=True)

# Phase Selector
phase = st.radio("Tournament Phase", ["Morning Pairs", "Afternoon Singles"], horizontal=True)

tab_in, tab_track = st.tabs(["⛳ RECORD", "📊 TRACKER"])

with tab_in:
    match_list = PAIRS_MATCHES if phase == "Morning Pairs" else SINGLES_MATCHES
    match_choice = st.selectbox("Select Match", match_list)
    
    if 'h_idx' not in st.session_state: st.session_state.h_idx = 1
    current_h = st.session_state.h_idx
    
    # Session Logic
    if phase == "Morning Pairs":
        session_range = range(1, 10) if current_h <= 9 else range(10, 19)
        session_label = "FRONT 9" if current_h <= 9 else "BACK 9"
    else:
        # Force singles to Hole 1-9
        if current_h > 9: st.session_state.h_idx = 1; current_h = 1
        session_range = range(1, 10)
        session_label = "SINGLES 9"

    status, _, _ = calculate_session_result(all_data, match_choice, session_range)
    st.markdown(f"<div style='text-align: center;'><span style='background: #ffc13b; padding: 2px 8px; border-radius: 5px; font-weight: bold; font-size: 11px;'>{session_label}</span><div style='color: #1e3d59; font-size: 18px; font-weight: bold;'>{status}</div></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c1: 
        if st.button("⬅️", use_container_width=True, key="p1"):
            st.session_state.h_idx = max(1, current_h - 1); st.rerun()
    with c2: st.markdown(f"<h3 style='text-align: center; margin: 0;'>HOLE {current_h}</h3>", unsafe_allow_html=True)
    with c3:
        max_limit = 18 if phase == "Morning Pairs" else 9
        if st.button("➡️", use_container_width=True, key="n1"):
            st.session_state.h_idx = min(max_limit, current_h + 1); st.rerun()

    st.info(f"Par {CHISLEHURST_MAP[current_h]['par']} | SI {CHISLEHURST_MAP[current_h]['si']}")

    saved_win = None
    row = all_data[(all_data['match_id'] == match_choice) & (all_data['hole'] == current_h)]
    if not row.empty: saved_win = row.iloc[0]['winner']

    cg, ch, cb = st.columns(3)
    def save(w):
        if engine:
            with engine.connect() as conn:
                conn.execute(text("INSERT INTO ryder_scores (match_id, hole, winner) VALUES (:m, :h, :w) ON DUPLICATE KEY UPDATE winner = :w"), 
                             {"m": match_choice, "h": current_h, "w": w})
                conn.commit()
            st.rerun()

    if cg.button("GABE", type="primary" if saved_win == "Gabe" else "secondary", use_container_width=True): save("Gabe")
    if ch.button("HALVE", type="primary" if saved_win == "Halve" else "secondary", use_container_width=True): save("Halve")
    if cb.button("BOT.", type="primary" if saved_win == "Bot." else "secondary", use_container_width=True): save("Bot.")

with tab_track:
    st.write("### Morning Pairs (10 pts)")
    for m in PAIRS_MATCHES:
        f_s, _, _ = calculate_session_result(all_data, m, range(1, 10))
        b_s, _, _ = calculate_session_result(all_data, m, range(10, 19))
        st.markdown(f"<div style='padding: 8px; background: #f8f9fa; border-radius: 5px; margin-bottom: 5px; font-size: 13px;'><b>{m}</b>: F9: {f_s} | B9: {b_s}</div>", unsafe_allow
