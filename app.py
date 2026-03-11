import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# 1. COURSE DATA (Chislehurst Official SI)
CHISLEHURST = {
    1: {"par": 5, "si": 11}, 2: {"par": 4, "si": 7},  3: {"par": 3, "si": 3},
    4: {"par": 4, "si": 15}, 5: {"par": 3, "si": 17}, 6: {"par": 4, "si": 1},
    7: {"par": 3, "si": 13}, 8: {"par": 3, "si": 5},  9: {"par": 4, "si": 9},
    10: {"par": 3, "si": 12}, 11: {"par": 4, "si": 4}, 12: {"par": 3, "si": 18},
    13: {"par": 3, "si": 8},  14: {"par": 5, "si": 2}, 15: {"par": 4, "si": 14},
    16: {"par": 4, "si": 10}, 17: {"par": 3, "si": 6}, 18: {"par": 4, "si": 16}
}

st.set_page_config(page_title="Ryder Cup 2026", layout="centered")

# 2. DATABASE
@st.cache_resource
def get_engine():
    try:
        s = st.secrets["connections"]["tidb"]
        url = f"mysql+pymysql://{s['username']}:{s['password']}@{s['host']}:{s['port']}/{s['database']}?ssl_ca=/etc/ssl/certs/ca-certificates.crt"
        return create_engine(url, pool_pre_ping=True)
    except: return None

engine = get_engine()

# --- DB HELPERS ---
def run_query(q, params=None):
    if not engine: return
    with engine.connect() as conn:
        conn.execute(text(q), params or {})
        conn.commit()

def get_df(q):
    if not engine: return pd.DataFrame()
    with engine.connect() as conn: return pd.read_sql(q, conn)

# Init Tables
run_query("CREATE TABLE IF NOT EXISTS ryder_scores (match_id VARCHAR(50), hole INT, winner VARCHAR(20), PRIMARY KEY (match_id, hole))")
run_query("CREATE TABLE IF NOT EXISTS players (name VARCHAR(50) PRIMARY KEY, team VARCHAR(10), hcp FLOAT)")
run_query("CREATE TABLE IF NOT EXISTS lineups (match_id VARCHAR(50) PRIMARY KEY, p1_gabe VARCHAR(50), p2_gabe VARCHAR(50), p1_bot VARCHAR(50), p2_bot VARCHAR(50))")

# --- MATCH LOGIC ---
def get_match_status(df, m_id, holes, allowance=1.0):
    m_data = df[(df['match_id'] == m_id) & (df['hole'].isin(holes))]
    if m_data.empty: return "All Square", 0.5, 0.5
    g_wins = len(m_data[m_data['winner'] == 'Gabe'])
    b_wins = len(m_data[m_data['winner'] == 'Bot.'])
    diff = abs(g_wins - b_wins)
    rem = max(holes) - m_data['hole'].max()
    if diff > rem:
        w = "Gabe" if g_wins > b_wins else "Bot."
        return f"{w} {diff}&{rem}" if rem > 0 else f"{w} {diff}UP", (1.0 if w=="Gabe" else 0.0), (1.0 if w=="Bot." else 0.0)
    if rem == 0:
        if diff == 0: return "Halved", 0.5, 0.5
        w = "Gabe" if g_wins > b_wins else "Bot."
        return f"{w} {diff}UP", (1.0 if w=="Gabe" else 0.0), (1.0 if w=="Bot." else 0.0)
    return ("Gabe" if g_wins > b_wins else "Bot." if b_wins > g_wins else "AS") + f" {diff}UP", 0.5, 0.5

# --- LOAD DATA ---
scores = get_df("SELECT * FROM ryder_scores")
roster = get_df("SELECT * FROM players")
lineups = get_df("SELECT * FROM lineups")

# Calculate Totals
tot_g, tot_b = 0.0, 0.0
for i in range(1,6):
    _, g1, b1 = get_match_status(scores, f"Pairs {i}", range(1,10))
    _, g2, b2 = get_match_status(scores, f"Pairs {i}", range(10,19))
    tot_g += (g1+g2); tot_b += (b1+b2)
for i in range(1,11):
    _, gs, bs = get_match_status(scores, f"Singles {i}", range(1,10))
    tot_g += gs; tot_b += bs

# --- UI ---
st.markdown(f"<div style='text-align:center; background:#1e3d59; color:white; padding:10px; border-radius:10px;'><h2>🏆 RYDER CUP 2026</h2><h3>Gabe {tot_g} — {tot_b} Bot.</h3></div>", unsafe_allow_html=True)

phase = st.radio("Tournament Phase", ["Morning Pairs", "Afternoon Singles"], horizontal=True)
tab1, tab2, tab3 = st.tabs(["⛳ RECORD", "📊 TRACKER", "🛠 CAPTAINS"])

with tab1:
    m_ids = [f"Pairs {i}" for i in range(1,6)] if phase == "Morning Pairs" else [f"Singles {i}" for i in range(1,11)]
    m_sel = st.selectbox("Select Match", m_ids)
    
    # Handicap Logic
    m_lineup = lineups[lineups['match_id'] == m_sel]
    if not m_lineup.empty:
        # Get handicaps of players in this match
        names = [m_lineup.iloc[0]['p1_gabe'], m_lineup.iloc[0]['p2_gabe'], m_lineup.iloc[0]['p1_bot'], m_lineup.iloc[0]['p2_bot']]
        match_hcps = roster[roster['name'].isin(names)]
        
        # Calculation: 90% for Pairs, 100% for Singles
        allowance = 0.9 if phase == "Morning Pairs" else 1.0
        # (Simplified for this UI: we'll show who gets a stroke on current hole)
        st.caption(f"Lineup: {', '.join([n for n in names if n])}")

    if 'h' not in st.session_state: st.session_state.h = 1
    ch = st.session_state.h
    if phase == "Afternoon Singles" and ch > 9: st.session_state.h = 1; ch = 1
    
    st.header(f"Hole {ch}")
    st.info(f"Par {CHISLEHURST[ch]['par']} | Stroke Index {CHISLEHURST[ch]['si']}")
    
    c1, c2, c3 = st.columns(3)
    if c1.button("GABE"): 
        run_query("REPLACE INTO ryder_scores VALUES (:m, :h, 'Gabe')", {"m":m_sel, "h":ch}); st.rerun()
    if c2.button("HALVE"): 
        run_query("REPLACE INTO ryder_scores VALUES (:m, :h, 'Halve')", {"m":m_sel, "h":ch}); st.rerun()
    if c3.button("BOT."): 
        run_query("REPLACE INTO ryder_scores VALUES (:m, :h, 'Bot.')", {"m":m_sel, "h":ch}); st.rerun()

with tab2:
    st.subheader("Live Standings")
    st.dataframe(scores)

with tab3:
    st.subheader("Roster Management")
    with st.form("add_player"):
        name = st.text_input("Name")
        team = st.selectbox("Team", ["Gabe", "Bot."])
        hcp = st.number_input("Handicap", 0.0, 54.0)
        if st.form_submit_button("Add Player"):
            run_query("REPLACE INTO players VALUES (:n, :t, :h)", {"n":name, "t":team, "h":hcp})
            st.rerun()
    
    st.subheader("Match Lineups")
    for m in [f"Pairs {i}" for i in range(1,6)] + [f"Singles {i}" for i in range(1,11)]:
        with st.expander(f"Set Lineup: {m}"):
            p1g = st.selectbox(f"{m} Gabe Player 1", [""] + roster[roster['team']=='Gabe']['name'].tolist(), key=f"g1{m}")
            p1b = st.selectbox(f"{m} Bot Player 1", [""] + roster[roster['team']=='Bot.']['name'].tolist(), key=f"b1{m}")
            if st.button(f"Save {m}"):
                run_query("REPLACE INTO lineups (match_id, p1_gabe, p1_bot) VALUES (:m, :g, :b)", {"m":m, "g":p1g, "b":p1b})
