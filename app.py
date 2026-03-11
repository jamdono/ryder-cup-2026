import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# 1. COURSE DATA
CHISLEHURST_MAP = {
    1: {"par": 5, "si": 11}, 2: {"par": 4, "si": 7},  3: {"par": 3, "si": 3},
    4: {"par": 4, "si": 15}, 5: {"par": 3, "si": 17}, 6: {"par": 4, "si": 1},
    7: {"par": 3, "si": 13}, 8: {"par": 3, "si": 5},  9: {"par": 4, "si": 9},
    10: {"par": 3, "si": 12}, 11: {"par": 4, "si": 4}, 12: {"par": 3, "si": 18},
    13: {"par": 3, "si": 8},  14: {"par": 5, "si": 2}, 15: {"par": 4, "si": 14},
    16: {"par": 4, "si": 10}, 17: {"par": 3, "si": 6}, 18: {"par": 4, "si": 16}
}

st.set_page_config(page_title="Ryder Cup 2026", layout="centered")

# 2. MANUAL DATABASE CONNECTION
@st.cache_resource
def get_engine():
    try:
        s = st.secrets["connections"]["tidb"]
        # Building the URL manually to avoid Streamlit's internal bugs
        # Supports both 'user' or 'username' keys in your secrets
        user = s.get("username") or s.get("user")
        conn_url = f"mysql+pymysql://{user}:{s['password']}@{s['host']}:{s['port']}/{s['database']}?ssl_ca=/etc/ssl/certs/ca-certificates.crt"
        return create_engine(conn_url, pool_pre_ping=True)
    except Exception as e:
        st.error(f"Secret Configuration Error: {e}")
        return None

engine = get_engine()

# Initialize Table
if engine:
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS ryder_scores (match_id VARCHAR(50), hole INT, winner VARCHAR(20), PRIMARY KEY (match_id, hole))"))
        conn.commit()

# --- HELPERS ---
if 'h_idx' not in st.session_state: st.session_state.h_idx = 1

def change_hole(delta):
    st.session_state.h_idx = max(1, min(18, st.session_state.h_idx + delta))

def save_score(m, h, w):
    if not engine: return
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO ryder_scores (match_id, hole, winner) VALUES (:m, :h, :w) ON DUPLICATE KEY UPDATE winner = :w"),
            {"m": m, "h": h, "w": w}
        )
        conn.commit()
    st.toast(f"Synced {w} for Hole {h}!")

# --- UI ---
st.title("🏆 RYDER CUP 2026")
tab_in, tab_track = st.tabs(["⛳ RECORD", "📊 TRACKER"])

with tab_in:
    match_choice = st.selectbox("Select Match", ["Match 1", "Match 2", "Match 3", "Match 4", "Match 5"])
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1: st.button("⬅️", on_click=change_hole, args=(-1,), use_container_width=True)
    with c2: st.markdown(f"<h3 style='text-align: center; margin: 0;'>HOLE {st.session_state.h_idx}</h3>", unsafe_allow_html=True)
    with c3: st.button("➡️", on_click=change_hole, args=(1,), use_container_width=True)

    h = st.session_state.h_idx
    st.info(f"Par {CHISLEHURST_MAP[h]['par']} | SI {CHISLEHURST_MAP[h]['si']}")

    # Get Winner for Highlight
    saved_win = None
    if engine:
        try:
            with engine.connect() as conn:
                res = conn.execute(text("SELECT winner FROM ryder_scores WHERE match_id = :m AND hole = :h"), {"m": match_choice, "h": h}).fetchone()
                if res: saved_win = res[0]
        except: pass

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
    st.write("### Live Leaderboard")
    if engine:
        try:
            df = pd.read_sql("SELECT * FROM ryder_scores ORDER BY match_id, hole", engine)
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No scores in the cloud yet.")
        except:
            st.warning("Connecting to cloud...")
