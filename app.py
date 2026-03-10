import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. DATABASE CONFIG (Hard-coded for reliability)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1fPj-sdgJXymXE-JY6TMZwG231gkcoq2DqM5kLYYie8Y/edit?usp=sharing"

CHISLEHURST_MAP = {
    1: {"par": 5, "si": 11}, 2: {"par": 4, "si": 7},  3: {"par": 3, "si": 3},
    4: {"par": 4, "si": 15}, 5: {"par": 3, "si": 17}, 6: {"par": 4, "si": 1},
    7: {"par": 3, "si": 13}, 8: {"par": 3, "si": 5},  9: {"par": 4, "si": 9},
    10: {"par": 3, "si": 12}, 11: {"par": 4, "si": 4}, 12: {"par": 3, "si": 18},
    13: {"par": 3, "si": 8},  14: {"par": 5, "si": 2}, 15: {"par": 4, "si": 14},
    16: {"par": 4, "si": 10}, 17: {"par": 3, "si": 6}, 18: {"par": 4, "si": 16}
}

st.set_page_config(page_title="Ryder Cup 2026", layout="centered")

# Establish Connection using the URL directly
conn = st.connection("gsheets", type=GSheetsConnection)

if 'h_idx' not in st.session_state: 
    st.session_state.h_idx = 1

def save_result(m_id, h, win):
    try:
        # Read existing data from 'Scores' tab
        try:
            df = conn.read(spreadsheet=SHEET_URL, worksheet="Scores")
        except:
            # If tab is empty/missing, create the structure
            df = pd.DataFrame(columns=["MatchID", "Hole", "Winner"])
        
        # Add new result
        new_row = pd.DataFrame([{"MatchID": m_id, "Hole": h, "Winner": win}])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        
        # Write back to Sheet
        conn.update(spreadsheet=SHEET_URL, worksheet="Scores", data=updated_df)
        st.success(f"Hole {h} synced!")
    except Exception as e:
        st.error("Connection failed. Make sure the Sheet is set to 'Anyone with link can EDIT'.")
        st.exception(e)

# --- UI ---
st.title("🏆 RYDER CUP 2026")

tab_in, tab_track = st.tabs(["⛳ RECORD SCORE", "📊 LIVE TRACKER"])

with tab_in:
    match_choice = st.selectbox("Select Match", ["Match 1", "Match 2", "Match 3", "Match 4", "Match 5"])
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("⬅️"): st.session_state.h_idx = max(1, st.session_state.h_idx - 1)
    with c2:
        st.markdown(f"<h3 style='text-align: center;'>HOLE {st.session_state.h_idx}</h3>", unsafe_allow_html=True)
    with c3:
        if st.button("➡️"): st.session_state.h_idx = min(18, st.session_state.h_idx + 1)

    h = st.session_state.h_idx
    st.info(f"**{'FOURSOMES' if h <= 9 else 'SCRAMBLE'}** | Par {CHISLEHURST_MAP[h]['par']} | SI {CHISLEHURST_MAP[h]['si']}")

    cg, ch, cb = st.columns(3)
    if cg.button("GABE", use_container_width=True): save_result(match_choice, h, "Gabe")
    if ch.button("HALVE", use_container_width=True): save_result(match_choice, h, "Halve")
    if cb.button("BOT.", use_container_width=True): save_result(match_choice, h, "Bottomley")

with tab_track:
    st.write("### Real-Time Scores")
    if st.button("Refresh Board"):
        st.rerun()
    
    try:
        # Read fresh data
        data = conn.read(spreadsheet=SHEET_URL, worksheet="Scores", ttl=0)
        if not data.empty:
            st.dataframe(data, use_container_width=True, hide_index=True)
        else:
            st.info("No scores recorded yet.")
    except:
        st.warning("Check your Google Sheet tab name is exactly 'Scores'.")
