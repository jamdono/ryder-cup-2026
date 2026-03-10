import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CHISLEHURST DATA ---
CHISLEHURST_MAP = {
    1: {"par": 5, "si": 11}, 2: {"par": 4, "si": 7},  3: {"par": 3, "si": 3},
    4: {"par": 4, "si": 15}, 5: {"par": 3, "si": 17}, 6: {"par": 4, "si": 1},
    7: {"par": 3, "si": 13}, 8: {"par": 3, "si": 5},  9: {"par": 4, "si": 9},
    10: {"par": 3, "si": 12}, 11: {"par": 4, "si": 4}, 12: {"par": 3, "si": 18},
    13: {"par": 3, "si": 8},  14: {"par": 5, "si": 2}, 15: {"par": 4, "si": 14},
    16: {"par": 4, "si": 10}, 17: {"par": 3, "si": 6}, 18: {"par": 4, "si": 16}
}

st.set_page_config(page_title="Ryder Cup 2026", layout="centered")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- STATE MANAGEMENT ---
if 'hole_tracker' not in st.session_state:
    st.session_state.hole_tracker = 1

# --- CALLBACKS ---
def next_hole():
    if st.session_state.hole_tracker < 18:
        st.session_state.hole_tracker += 1

def prev_hole():
    if st.session_state.hole_tracker > 1:
        st.session_state.hole_tracker -= 1

def save_to_sheets(m_id, h_idx, winner):
    # This creates a new row for your 'Scores' tab
    new_data = pd.DataFrame([{"MatchID": m_id, "Hole": h_idx, "Winner": winner}])
    # We append this to the existing 'Scores' worksheet
    existing_scores = conn.read(worksheet="Scores")
    updated_scores = pd.concat([existing_scores, new_data], ignore_index=True)
    conn.update(worksheet="Scores", data=updated_scores)
    st.toast(f"Hole {h_idx} synced to leaderboard!")

# --- UI HEADER ---
st.title("🏆 RYDER CUP 2026")

tab_in, tab_track = st.tabs(["⛳ RECORD SCORE", "📊 LIVE TRACKER"])

with tab_in:
    # Pull match names from your 'Setup' tab if it exists, otherwise use placeholders
    try:
        setup_df = conn.read(worksheet="Setup")
        match_list = setup_df['MatchID'].unique().tolist()
    except:
        match_list = ["Match 1", "Match 2", "Match 3", "Match 4", "Match 5"]

    match_choice = st.selectbox("Select Your Match", match_list)
    
    # STEPPER
    c_p, c_l, c_n = st.columns([1, 2, 1])
    with c_p:
        st.button("⬅️", on_click=prev_hole, use_container_width=True)
    with c_l:
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>HOLE {st.session_state.hole_tracker}</h3>", unsafe_allow_html=True)
    with c_n:
        st.button("➡️", on_click=next_hole, use_container_width=True)

    h_idx = st.session_state.hole_tracker
    session_name = "FOURSOMES" if h_idx <= 9 else "SCRAMBLE"
    st.info(f"**{session_name}** | Par {CHISLEHURST_MAP[h_idx]['par']} | SI {CHISLEHURST_MAP[h_idx]['si']}")

    # SCORING BUTTONS
    st.write("Who won this hole?")
    cg, ch, cb = st.columns(3)
    if cg.button("GABE", use_container_width=True):
        save_to_sheets(match_choice, h_idx, "G")
    if ch.button("HALVE", use_container_width=True):
        save_to_sheets(match_choice, h_idx, "H")
    if cb.button("BOT.", use_container_width=True):
        save_to_sheets(match_choice, h_idx, "B")

with tab_track:
    st.write("### Live Standings")
    try:
        scores_df = conn.read(worksheet="Scores", ttl=0)
        st.dataframe(scores_df, use_container_width=True)
    except:
        st.write("No scores recorded yet. Get out on the first tee!")
