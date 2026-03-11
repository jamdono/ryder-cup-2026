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
        return create_engine(conn_url, pool_pre_ping=True)
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None

engine = get_engine()

# --- DATA HELPERS ---
def get_all_scores():
    if not engine: return pd.DataFrame()
    try:
        return pd.read_sql("SELECT * FROM ryder_scores", engine)
    except:
        return pd.DataFrame()

def calculate_match_result(df, match_name):
    m_data = df[df['match_id'] == match_name]
    if m_data.empty: return "All Square", 0, 0 # Status, Gabe Points, Bot Points
    
    g_wins = len(m_data[m_data['winner'] == 'Gabe'])
    b_wins = len(m_data[m_data['winner'] == 'Bot.'])
    
    # Status String
    if g_wins > b_wins:
        status = f"Gabe {g_wins - b_wins} UP"
        pts = (1, 0)
    elif b_wins > g_wins:
        status = f"Bot. {b_wins - g_wins} UP"
        pts = (0, 1)
    else:
        status = "All Square"
        pts = (0.5, 0.5)
    
    return status, pts[0], pts[1]

# --- UI HEADER (Fixed at top) ---
all_data = get_all_scores()
total_g, total_b = 0.0, 0.0

# Pre-calculate totals for header
for m in MATCHES:
    _, pg, pb = calculate_match_result(all_data, m)
    total_g += pg
    total_b += pb

st.markdown(f"""
<div style="background-color: #1e3d59; padding: 15px; border-radius: 10px; border: 2px solid #ffc13b; margin-bottom: 20px;">
    <h1 style="color: white; text-align: center; margin: 0;">🏆 RYDER CUP 2026</h1>
    <p style="color: #ffc13b; text-align: center; font-size: 20px; font-weight: bold; margin: 5px 0;">
        PROJECTED: Team Gabe {total_g} — {total_b} Team Bot.
    </p>
    <p style="color: #bdc3c7; text-align: center; font-size: 12px; margin: 0;">
        Last Synced: {datetime.datetime.now().strftime('%H:%M:%S')}
    </p>
</div>
""", unsafe_allow_html=True)

# --- TABS ---
tab_in, tab_track = st.tabs(["⛳ RECORD", "📊 TRACKER"])

with tab_in:
    match_choice = st.selectbox("Select Match", MATCHES)
    current_status, _, _ = calculate_match_result(all_data, match_choice)
    st.write(f"### {current_status}")
    
    # Hole Navigation
    if 'h_idx' not in st.session_state: st.session_state.h_idx = 1
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1: 
        if st.button("⬅️", use_container_width=True):
            st.session_state.h_idx = max(1, st.session_state.h_idx - 1)
            st.rerun()
    with c2: 
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>HOLE {st.session_state.h_idx}</h3>", unsafe_allow_html=True)
    with c3: 
        if st.button("➡️", use_container_width=True):
            st.session_state.h_idx = min(18, st.session_state.h_idx + 1)
            st.rerun()

    h = st.session_state.h_idx
    st.info(f"Par {CHISLEHURST_MAP[h]['par']} | SI {CHISLEHURST_MAP[h]['si']}")

    # Save logic
    def save_score(m, h, w):
        with engine.connect() as conn:
            conn.execute(text("INSERT INTO ryder_scores (match_id, hole, winner) VALUES (:m, :h, :w) ON DUPLICATE KEY UPDATE winner = :w"), {"m": m, "h": h, "w": w})
            conn.commit()

    # Get Winner to highlight button
    saved_win = None
    row = all_data[(all_data['match_id'] == match_choice) & (all_data['hole'] == h)]
    if not row.empty: saved_win = row.iloc[0]['winner']

    cg, ch, cb = st.columns(3)
    if cg.button("GABE", type="primary" if saved_win == "Gabe" else "secondary", use_container_width=True):
        save_score(match_choice, h, "Gabe")
        st.rerun()
    if ch.button("HALVE", type="primary" if saved_win == "Halve" else "secondary", use_container_width=True):
        save_score(match_choice, h, "Halve")
        st.rerun()
    if cb.button("BOT.", type="primary" if saved_win == "Bot." else "secondary", use_container_width=True):
        save_score(match_choice, h, "Bot.")
        st.rerun()

with tab_track:
    st.write("### Match Summary")
    for m in MATCHES:
        m_status, _, _ = calculate_match_result(all_data, m)
        color = "#2ecc71" if "Gabe" in m_status else "#e74c3c" if "Bot" in m_status else "#95a5a6"
        st.markdown(f"""
        <div style="padding: 10px; border-left: 5px solid {color}; background: #f8f9fa; margin-bottom: 5px; border-radius: 5px;">
            <strong>{m}</strong>: {m_status}
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("🔄 Force Refresh"):
        st.rerun()

# --- AUTO REFRESH (60 Seconds) ---
@st.fragment(run_every=60)
def auto_refresh():
    st.rerun()
