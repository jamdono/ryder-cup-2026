import streamlit as st
import pandas as pd

# 1. DATA: CHISLEHURST GC
CHISLEHURST_MAP = {
    1: {"par": 5, "si": 11}, 2: {"par": 4, "si": 7},  3: {"par": 3, "si": 3},
    4: {"par": 4, "si": 15}, 5: {"par": 3, "si": 17}, 6: {"par": 4, "si": 1},
    7: {"par": 3, "si": 13}, 8: {"par": 3, "si": 5},  9: {"par": 4, "si": 9},
    10: {"par": 3, "si": 12}, 11: {"par": 4, "si": 4}, 12: {"par": 3, "si": 18},
    13: {"par": 3, "si": 8},  14: {"par": 5, "si": 2}, 15: {"par": 4, "si": 14},
    16: {"par": 4, "si": 10}, 17: {"par": 3, "si": 6}, 18: {"par": 4, "si": 16}
}

st.set_page_config(page_title="Ryder Cup 2026", layout="centered")

# Initialize Master Scoreboard in Session State
# Note: In a live deploy, we'd use a real DB, but let's get the UI perfect first
if 'master_scores' not in st.session_state:
    st.session_state.master_scores = pd.DataFrame(columns=["Match", "Hole", "Winner"])

if 'h_idx' not in st.session_state:
    st.session_state.h_idx = 1

# --- FUNCTIONS ---
def save_score(m_name, h_num, win):
    new_data = pd.DataFrame([{"Match": m_name, "Hole": h_num, "Winner": win}])
    # Overwrite if hole already exists for this match
    mask = (st.session_state.master_scores['Match'] == m_name) & (st.session_state.master_scores['Hole'] == h_num)
    if mask.any():
        st.session_state.master_scores = st.session_state.master_scores[~mask]
    
    st.session_state.master_scores = pd.concat([st.session_state.master_scores, new_data], ignore_index=True)
    st.toast(f"Hole {h_num} Recorded!")

# --- UI ---
st.title("🏆 RYDER CUP 2026")

tab_in, tab_track = st.tabs(["⛳ RECORD", "📊 TRACKER"])

with tab_in:
    match_choice = st.selectbox("Select Match", ["Match 1", "Match 2", "Match 3", "Match 4", "Match 5"])
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("⬅️"): st.session_state.h_idx = max(1, st.session_state.h_idx - 1)
    with c2:
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>HOLE {st.session_state.h_idx}</h3>", unsafe_allow_html=True)
    with c3:
        if st.button("➡️"): st.session_state.h_idx = min(18, st.session_state.h_idx + 1)

    h = st.session_state.h_idx
    st.info(f"Par {CHISLEHURST_MAP[h]['par']} | SI {CHISLEHURST_MAP[h]['si']}")

    cg, ch, cb = st.columns(3)
    if cg.button("GABE", use_container_width=True): save_score(match_choice, h, "Gabe")
    if ch.button("HALVE", use_container_width=True): save_score(match_choice, h, "Halve")
    if cb.button("BOT.", use_container_width=True): save_score(match_choice, h, "Bottomley")

with tab_track:
    st.write("### Live Leaderboard")
    if not st.session_state.master_scores.empty:
        # Simple summary
        df = st.session_state.master_scores.sort_values(by=["Match", "Hole"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.write("No scores recorded yet.")
