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
    if m_data.empty: return "All Square", 0.5, 0.5 
    
    g_wins = len(m_data[m_data['winner'] == 'Gabe'])
    b_wins = len(m_data[m_data['winner'] == 'Bot.'])
    
    if g_wins > b_wins:
        return f"Gabe {g_wins - b_wins} UP", 1.0, 0.0
    elif b_wins > g_wins:
        return f"Bot. {b_wins - g_wins} UP", 0.0, 1.0
    else:
        return "All Square", 0.5, 0.5

# --- UI HEADER ---
all_data = get_all_scores()
proj_g, proj_b = 0.0, 0.0
