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

# --- INITIALIZE STATE ---
if 'master_scores' not in st.session_state:
    # This keeps a record for every match and every hole
    st.session_state.master_scores = {}

if 'h_idx' not in st.session_state:
    st.session_state.h_idx = 1

# --- CALLBACKS (Fixes the skipping) ---
def next_hole():
    if st.session_state.h_idx < 18:
        st.session_state.h_idx += 1

def prev_hole():
    if st.session_state.h_idx > 1:
        st.session_state.h_idx -= 1

def save_score(m_name, h_num, win):
    # Store in a dictionary: { "Match 1": {1: "Gabe", 2: "Halve"} }
    if m_name not in st.session_state.master_scores:
        st.session_state.master_scores[m_name] = {}
    st.session_state.master_scores[m_name][h_num] = win
    st.toast(f"Hole {h_num} Recorded!")

# --- UI ---
st.title("🏆 RYDER CUP 2026")

tab_in, tab_track = st.tabs(["⛳ RECORD", "📊 TRACKER"])

with tab_in:
    match_choice = st.selectbox("Select Match", ["Match 1", "Match 2", "Match 3", "Match 4", "Match 5"])
    
    # STEPPER (Using on_click callbacks to prevent skipping)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        st.button("⬅️", on_click=prev_hole, use_container_width=True)
    with c2:
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>HOLE {st.session_state.h_idx}</h3>", unsafe_allow_html=True)
    with c3:
        st.button("➡️", on_click=next_hole, use_container_width=True)

    h = st.session_state.h_idx
    st.info(f"Par {CHISLEHURST_MAP[h]['par']} | SI {CHISLEHURST_MAP[h]['si']}")

    # --- ILLUMINATION LOGIC ---
    # Check what is currently saved for this match and hole
    current_match_results = st.session_state.master_scores.get(match_choice, {})
    saved_win = current_match_results.get(h, None)

    st.write("Who won this hole?")
    cg, ch, cb = st.columns(3)
    
    with cg:
        st.button("GABE", 
                  type="primary" if saved_win == "Gabe" else "secondary", 
                  use_container_width=True, 
                  on_click=save_score, args=(match_choice, h, "Gabe"))
    with ch:
        st.button("HALVE", 
                  type="primary" if saved_win == "Halve" else "secondary", 
                  use_container_width=True, 
                  on_click=save_score, args=(match_choice, h, "Halve"))
    with cb:
        st.button("BOT.", 
                  type="primary" if saved_win == "Bottomley" else "secondary", 
                  use_container_width=True,
