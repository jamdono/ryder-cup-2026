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

# 2. DATABASE CONNECTION (Wrapped in try/except to prevent white screen)
@st.cache_resource
def get_engine():
    try:
        s = st.secrets["connections"]["tidb"]
        conn_url = f"mysql+pymysql://{s['username']}:{s['password']}@{s['host']}:{s['port']}/{s['database']}?ssl_ca=/etc/ssl/certs/ca-certificates.crt"
        return create_engine(conn_url, pool_pre_ping=True, pool_recycle=300)
    except Exception:
        return None

engine = get_engine()

# --- DATA HELPERS ---
def get_all_scores():
    if not engine: return pd.DataFrame()
    try:
        with engine.connect() as conn:
            return pd.read_sql("SELECT * FROM ryder_scores", conn)
    except Exception:
        return pd.DataFrame()

def calculate_match_result(df, match_name):
    if df.empty: return "All Square", 0.5, 0.5
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

# --- MAIN LOGIC ---
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
        Last Synced: {datetime.datetime.now().strftime('%H:%M:%S')}
    </p>
</div>
""", unsafe_allow_html=True)

tab_in, tab_track = st.tabs(["⛳ RECORD", "📊 TRACKER"])

with tab_in:
    match_choice = st.selectbox("Select Match", MATCHES)
    current_status, _, _ = calculate_match_result(all_data, match_choice)
    
    st.markdown(f"<div style='text-align: center; color: #1e3d59; font-size: 20px; font-weight: bold; margin: 10px 0;'>This match: {current_status}</div>", unsafe_allow_html=True)
    
    if 'h_idx' not in st.session_state: 
        st.session_state.h_idx = 1
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1: 
        if st.button("⬅️", use_container_width=True, key="p1"):
            st.session_state.h_idx = max(1, st.session_state.h_idx - 1)
            st.rerun()
    with c2: 
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>HOLE {st.session_state.h_idx}</h3>", unsafe_allow_html=True)
    with c3: 
        if st.button("➡️", use_container_width=True, key="n1"):
            st.session_state.h_idx = min(18, st.session_state.h_idx + 1)
            st.rerun()

    h = st.session_state.h_idx
    st.info(f"Par {CHISLEHURST_MAP[h]['par']} | SI {CHISLEHURST_MAP[h]['si']}")

    saved_win = None
    if not all_data.empty:
        row = all_data[(all_data['match_id'] == match_choice) & (all_data['hole'] == h)]
        if not row.empty: saved_win = row.iloc[0]['winner']

    cg, ch, cb = st.columns(3)
    
    def handle_click(winner_name):
        if engine:
            try:
                with engine.connect() as conn:
                    conn.execute(text("INSERT INTO ryder_scores (match_id, hole, winner) VALUES (:m, :h, :w) ON DUPLICATE KEY UPDATE winner = :w"), 
                                 {"m": match_choice, "h": h, "w": winner_name})
                    conn.commit()
                st.rerun()
            except Exception as e:
                st.error("Connection lost. Try again.")

    if cg.button("GABE", type="primary" if saved_win == "Gabe" else "secondary", use_container_width=True):
        handle_click("Gabe")
    if ch.button("HALVE", type="primary" if saved_win == "Halve" else "secondary", use_container_width=True):
        handle_click("Halve")
    if cb.button("BOT.", type="primary" if saved_win == "Bot." else "secondary", use_container_width=True):
        handle_click("Bot.")

with tab_track:
    st.write("### Match Summary")
    for m in MATCHES:
        m_status, _, _ = calculate_match_result(all_data, m)
        color = "#2ecc71" if "Gabe" in m_status else "#e74c3c" if "Bot" in m_status else "#95a5a6"
        st.markdown(f"""
        <div style="padding: 12px; border-left: 5px solid {color}; background: #f8f9fa; margin-bottom: 8px; border-radius: 5px;">
            <span style="font-weight: bold;">{m}</span>: {m_status}
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("🔄 Sync Now", use_container_width=True):
        st.rerun()

# --- SIMPLE REFRESH (No Fragments) ---
# We'll avoid the fragment for now to ensure the white screen disappears.
# To refresh, users can just tap the "Sync Now" button or pull down to refresh.
