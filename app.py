import streamlit as st
import pandas as pd

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

# 2. CLOUD DATABASE CONNECTION
# This uses the TiDB secrets you just pasted
conn = st.connection('tidb', type='sql')

# Initialize Table (Runs once)
with conn.session as s:
    s.execute('CREATE TABLE IF NOT EXISTS ryder_scores (match_id VARCHAR(50), hole INT, winner VARCHAR(20), PRIMARY KEY (match_id, hole));')
    s.commit()

# --- NAVIGATION ---
if 'h_idx' not in st.session_state: st.session_state.h_idx = 1

def change_hole(delta):
    st.session_state.h_idx = max(1, min(18, st.session_state.h_idx + delta))

def save_score(m, h, w):
    with conn.session as s:
        s.execute(
            'INSERT INTO ryder_scores (match_id, hole, winner) VALUES (:m, :h, :w) ON DUPLICATE KEY UPDATE winner = :w',
            params={"m": m, "h": h, "w": w}
        )
        s.commit()
    st.toast("Syncing with cloud...")

# --- UI ---
st.title("🏆 RYDER CUP 2026")
tab_in, tab_track = st.tabs(["⛳ RECORD", "📊 TRACKER"])

with tab_in:
    match_list = ["Match 1", "Match 2", "Match 3", "Match 4", "Match 5"]
    match_choice = st.selectbox("Select Match", match_list)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1: st.button("⬅️", on_click=change_hole, args=(-1,), use_container_width=True)
    with c2: st.markdown(f"<h3 style='text-align: center;'>HOLE {st.session_state.h_idx}</h3>", unsafe_allow_html=True)
    with c3: st.button("➡️", on_click=change_hole, args=(1,), use_container_width=True)

    h = st.session_state.h_idx
    st.info(f"Par {CHISLEHURST_MAP[h]['par']} | SI {CHISLEHURST_MAP[h]['si']}")

    # Get Winner for Highlight
    saved_win = None
    existing = conn.query(f"SELECT winner FROM ryder_scores WHERE match_id = '{match_choice}' AND hole = {h}", ttl=0)
    if not existing.empty:
        saved_win = existing.iloc[0]['winner']

    st.write("Who won this hole?")
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
    st.write("### Live Scores")
    df = conn.query("SELECT * FROM ryder_scores ORDER BY match_id, hole", ttl=0)
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No scores in the cloud yet.")
