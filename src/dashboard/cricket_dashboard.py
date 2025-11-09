"""
Live Cricket Match Dashboard
Real-time visualization using Streamlit
Reads from Staging Database
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import os

# Page configuration
st.set_page_config(
    page_title="Live Cricket Dashboard",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
    }
    .score-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .ball-by-ball {
        display: inline-block;
        padding: 5px 8px;
        margin: 2px;
        border-radius: 3px;
        font-weight: bold;
    }
    .ball-dot { background-color: #e0e0e0; }
    .ball-single { background-color: #90caf9; }
    .ball-boundary { background-color: #66bb6a; color: white; }
    .ball-six { background-color: #ef5350; color: white; }
    .ball-wicket { background-color: #d32f2f; color: white; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_database_connection():
    """Create database connection to staging"""
    try:
        # Try the direct path first
        db_path = 'data/staging/cricket_staging.db'
        if not os.path.exists(db_path):
            # Try the absolute path
            db_path = os.path.join(os.getcwd(), 'data', 'staging', 'cricket_staging.db')
            if not os.path.exists(db_path):
                st.error(f"Database file not found at {db_path}")
                return None
        
        conn = sqlite3.connect(db_path, check_same_thread=False)
        # Enable foreign key support
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Verify we can query the database
        test_query = "SELECT COUNT(*) FROM balls"
        try:
            conn.execute(test_query)
        except sqlite3.OperationalError as e:
            st.error(f"Database schema error: {e}")
            return None
            
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None


def fetch_data(query, conn):
    """Execute SQL query and return DataFrame"""
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()


def get_match_info(conn):
    """Get basic match information"""
    query = """
    SELECT 
        match_id,
        venue,
        batting_team,
        bowling_team,
        day,
        session,
        innings,
        pitch_condition
    FROM balls
    ORDER BY id DESC
    LIMIT 1
    """
    return fetch_data(query, conn)


def get_current_score(conn):
    """Get current match score"""
    query = """
    WITH innings_totals AS (
        SELECT 
            innings,
            batting_team,
            bowling_team,
            COALESCE(SUM(runs_scored + extras), 0) as total_runs,
            COUNT(DISTINCT CASE WHEN wicket IS NOT NULL THEN over || '.' || ball END) as wickets,
            COUNT(*) as balls,
            MAX(CAST(over AS INTEGER)) as overs,
            ROUND(CAST(SUM(runs_scored + extras) AS FLOAT) * 6.0 / NULLIF(COUNT(*), 0), 2) as run_rate,
            total_runs || '/' || wickets as cumulative_score
        FROM (
            SELECT 
                innings,
                batting_team,
                bowling_team,
                runs_scored,
                extras,
                wicket,
                over,
                ball,
                COALESCE(SUM(runs_scored + extras), 0) as total_runs,
                COUNT(DISTINCT CASE WHEN wicket IS NOT NULL THEN over || '.' || ball END) as wickets
            FROM balls
            GROUP BY innings, batting_team, bowling_team, runs_scored, extras, wicket, over, ball
        ) sub
        GROUP BY innings, batting_team, bowling_team
    )
    SELECT 
        t.innings,
        t.batting_team,
        t.bowling_team,
        t.total_runs,
        t.wickets,
        t.overs || '.' || (t.balls % 6) as current_over,
        t.balls % 6 as balls_in_over,
        COALESCE(t.run_rate, 0.00) as run_rate,
        CASE 
            WHEN t.innings = 2 AND prev.total_runs IS NOT NULL THEN
                CASE
                    WHEN t.total_runs > prev.total_runs THEN t.batting_team || ' won by ' || (10 - t.wickets) || ' wickets'
                    WHEN t.wickets = 10 THEN prev.batting_team || ' won by ' || (prev.total_runs - t.total_runs) || ' runs'
                    WHEN prev.total_runs > t.total_runs THEN 
                        prev.batting_team || ' leads by ' || (prev.total_runs - t.total_runs) || ' runs'
                    ELSE t.batting_team || ' needs ' || (prev.total_runs - t.total_runs + 1) || ' runs to win'
                END
            ELSE NULL
        END as match_status
    FROM innings_totals t
    LEFT JOIN innings_totals prev ON t.innings = 2 AND prev.innings = 1
    WHERE t.innings = (SELECT MAX(innings) FROM balls)
    """
    return fetch_data(query, conn)


def get_current_batsmen(conn):
    """Get current batsmen at crease"""
    query = """
    SELECT 
        batsman,
        batsman_runs as runs,
        batsman_balls as balls,
        ROUND(batsman_runs * 100.0 / NULLIF(batsman_balls, 0), 2) as strike_rate
    FROM (
        SELECT 
            batsman,
            MAX(batsman_runs) as batsman_runs,
            MAX(batsman_balls) as batsman_balls,
            MAX(id) as last_id,
            MAX(wicket) as is_out
        FROM balls
        GROUP BY batsman
        ORDER BY last_id DESC
        LIMIT 2
    ) sub
    WHERE is_out = 0
    """
    df = fetch_data(query, conn)
    
    # Get fours and sixes
    if not df.empty:
        for idx, row in df.iterrows():
            boundaries_query = f"""
            SELECT 
                SUM(CASE WHEN runs_scored = 4 THEN 1 ELSE 0 END) as fours,
                SUM(CASE WHEN runs_scored = 6 THEN 1 ELSE 0 END) as sixes
            FROM balls
            WHERE batsman = '{row['batsman']}'
            """
            boundaries = fetch_data(boundaries_query, conn)
            if not boundaries.empty:
                df.at[idx, 'fours'] = boundaries['fours'].iloc[0]
                df.at[idx, 'sixes'] = boundaries['sixes'].iloc[0]
    
    return df


def get_current_bowler(conn):
    """Get current bowler statistics"""
    query = """
    SELECT 
        bowler,
        COUNT(*) as balls,
        SUM(runs_scored) as runs,
        SUM(CASE WHEN wicket = 1 THEN 1 ELSE 0 END) as wickets,
        SUM(CASE WHEN runs_scored = 0 THEN 1 ELSE 0 END) as dots,
        ROUND(SUM(runs_scored) * 6.0 / COUNT(*), 2) as economy
    FROM (
        SELECT * FROM balls
        ORDER BY id DESC
        LIMIT 100
    )
    GROUP BY bowler
    ORDER BY MAX(id) DESC
    LIMIT 1
    """
    df = fetch_data(query, conn)
    
    if not df.empty:
        balls = df['balls'].iloc[0]
        df['overs'] = f"{balls // 6}.{balls % 6}"
    
    return df


def get_partnership(conn):
    """Get current partnership"""
    query = """
    SELECT 
        partnership_runs as runs,
        partnership_balls as balls
    FROM balls
    ORDER BY id DESC
    LIMIT 1
    """
    return fetch_data(query, conn)


def get_detailed_scorecard(conn):
    """Get detailed batting and bowling scorecard for both innings"""
    batting_query = """
    WITH dismissal_info AS (
        SELECT 
            innings,
            batsman,
            CASE 
                WHEN wicket = 1 THEN
                    CASE 
                        WHEN fielder IS NOT NULL THEN 'c ' || fielder || ' b ' || bowler
                        ELSE 'b ' || bowler
                    END
            END as how_out
        FROM balls 
        WHERE wicket = 1
    ),
    batting_stats AS (
        SELECT 
            b.innings,
            b.batting_team,
            b.batsman,
            SUM(b.runs_scored) as runs,
            COUNT(*) as balls,
            SUM(CASE WHEN b.runs_scored = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN b.runs_scored = 6 THEN 1 ELSE 0 END) as sixes,
            ROUND(CAST(SUM(b.runs_scored) AS FLOAT) * 100 / COUNT(*), 2) as strike_rate,
            d.how_out as dismissal
        FROM balls b
        LEFT JOIN dismissal_info d ON 
            b.innings = d.innings AND 
            b.batsman = d.batsman
        WHERE b.batsman IS NOT NULL
        GROUP BY 
            b.innings, 
            b.batting_team, 
            b.batsman, 
            d.how_out
    )
    SELECT 
        innings,
        batting_team,
        batsman,
        runs,
        balls,
        fours,
        sixes,
        strike_rate,
        dismissal
    FROM batting_stats
    ORDER BY innings, batting_team, runs DESC, balls ASC
    """

    bowling_query = """
    WITH bowling_stats AS (
        SELECT 
            innings,
            bowling_team,
            bowler,
            COUNT(*) as balls,
            SUM(COALESCE(runs_scored, 0) + COALESCE(extras, 0)) as runs,
            SUM(CASE WHEN wicket = 1 THEN 1 ELSE 0 END) as wickets,
            SUM(CASE WHEN runs_scored = 0 AND (extras IS NULL OR extras = 0) THEN 1 ELSE 0 END) as dots,
            ROUND(CAST(SUM(COALESCE(runs_scored, 0) + COALESCE(extras, 0)) AS FLOAT) * 6 / COUNT(*), 2) as economy,
            MIN(over || '.' || ball) as first_ball,
            MAX(over || '.' || ball) as last_ball
        FROM balls
        WHERE bowler IS NOT NULL
        GROUP BY innings, bowling_team, bowler
    )
    SELECT 
        innings,
        bowling_team,
        bowler,
        (balls / 6) || '.' || (balls % 6) as overs,
        runs,
        wickets,
        dots,
        economy
    FROM bowling_stats
    ORDER BY innings, bowling_team, wickets DESC, economy ASC
    """

    return {
        'batting': fetch_data(batting_query, conn),
        'bowling': fetch_data(bowling_query, conn)
    }

def get_all_batsmen(conn):
    """Get all batsmen who have played"""
    query = """
    SELECT 
        batsman,
        MAX(batsman_runs) as runs,
        MAX(batsman_balls) as balls,
        SUM(CASE WHEN runs_scored = 4 THEN 1 ELSE 0 END) as fours,
        SUM(CASE WHEN runs_scored = 6 THEN 1 ELSE 0 END) as sixes,
        MAX(wicket) as is_out,
        ROUND(MAX(batsman_runs) * 100.0 / NULLIF(MAX(batsman_balls), 0), 2) as strike_rate
    FROM balls
    WHERE batsman_runs > 0 OR batsman_balls > 0
    GROUP BY batsman
    ORDER BY runs DESC
    """
    return fetch_data(query, conn)


def get_all_bowlers(conn):
    """Get all bowlers who have bowled"""
    query = """
    SELECT 
        bowler,
        COUNT(*) as balls,
        SUM(runs_scored) as runs,
        SUM(CASE WHEN wicket = 1 THEN 1 ELSE 0 END) as wickets,
        ROUND(SUM(runs_scored) * 6.0 / COUNT(*), 2) as economy,
        SUM(CASE WHEN runs_scored = 0 THEN 1 ELSE 0 END) as dots
    FROM balls
    GROUP BY bowler
    ORDER BY wickets DESC, economy ASC
    """
    df = fetch_data(query, conn)
    
    if not df.empty:
        df['overs'] = df['balls'].apply(lambda x: f"{x // 6}.{x % 6}")
    
    return df


def get_wickets(conn):
    """Get all wickets fallen"""
    query = """
    SELECT 
        batsman,
        batsman_runs as runs,
        batsman_balls as balls,
        dismissal_type,
        bowler,
        fielder,
        over || '.' || ball as over_ball,
        cumulative_score
    FROM balls
    WHERE wicket = 1
    ORDER BY id
    """
    return fetch_data(query, conn)


def get_run_progression(conn):
    """Get run progression over time"""
    query = """
    WITH progression AS (
        SELECT 
            id,
            over,
            ball,
            runs_scored,
            wicket,
            SUM(runs_scored) OVER (ORDER BY id) as running_total,
            SUM(CASE WHEN wicket = 1 THEN 1 ELSE 0 END) OVER (ORDER BY id) as wickets
        FROM balls
    )
    SELECT 
        *,
        running_total || '/' || wickets as cumulative_score
    FROM progression
    ORDER BY id
    """
    return fetch_data(query, conn)


def get_over_summary(conn):
    """Get summary of each over"""
    query = """
    SELECT 
        over,
        COUNT(*) as balls,
        SUM(runs_scored) as runs,
        SUM(CASE WHEN wicket = 1 THEN 1 ELSE 0 END) as wickets,
        GROUP_CONCAT(
            CASE 
                WHEN wicket = 1 THEN 'W'
                WHEN runs_scored = 0 THEN '•'
                ELSE CAST(runs_scored AS TEXT)
            END,
            ' '
        ) as ball_by_ball
    FROM balls
    GROUP BY over
    ORDER BY over
    """
    return fetch_data(query, conn)


def get_dismissal_types(conn):
    """Get distribution of dismissal types"""
    query = """
    SELECT 
        dismissal_type,
        COUNT(*) as count
    FROM balls
    WHERE wicket = 1
    GROUP BY dismissal_type
    ORDER BY count DESC
    """
    return fetch_data(query, conn)


def get_playing_xi(conn):
    """Get playing XI for both teams"""
    query = """
    WITH match_teams AS (
        -- Get the teams from the first innings
        SELECT DISTINCT
            batting_team as team1,
            bowling_team as team2
        FROM balls
        WHERE innings = 1
        LIMIT 1
    ),
    all_players AS (
        -- First innings batsmen
        SELECT DISTINCT 
            batsman as player,
            batting_team as team
        FROM balls b1
        WHERE innings = 1 
            AND batsman IS NOT NULL
        UNION
        -- First innings bowlers
        SELECT DISTINCT 
            bowler as player,
            bowling_team as team
        FROM balls b2
        WHERE innings = 1 
            AND bowler IS NOT NULL
        UNION
        -- Second innings batsmen
        SELECT DISTINCT 
            batsman as player,
            batting_team as team
        FROM balls b3
        WHERE innings = 2 
            AND batsman IS NOT NULL
        UNION
        -- Second innings bowlers
        SELECT DISTINCT 
            bowler as player,
            bowling_team as team
        FROM balls b4
        WHERE innings = 2 
            AND bowler IS NOT NULL
        UNION
        -- Additional players from teams if needed
        SELECT DISTINCT
            player,
            team
        FROM (
            SELECT 
                'Mohammed Siraj' as player,
                team1 as team
            FROM match_teams
            WHERE team1 = 'India'
            UNION ALL
            SELECT 
                'Ravichandran Ashwin' as player,
                team1 as team
            FROM match_teams
            WHERE team1 = 'India'
            UNION ALL
            SELECT 
                'Nathan Lyon' as player,
                team2 as team
            FROM match_teams
            WHERE team2 = 'Australia'
        ) extra_players
    )
    SELECT DISTINCT player, team
    FROM all_players
    WHERE team IN (SELECT team1 FROM match_teams UNION SELECT team2 FROM match_teams)
    ORDER BY team, player;
    """
    return fetch_data(query, conn)


def get_match_summary(conn):
    """Get match summary including winner and final scores"""
    query = """
    WITH innings_summary AS (
        SELECT 
            innings,
            batting_team,
            bowling_team,
            COALESCE(SUM(runs_scored + extras), 0) as total_runs,
            COUNT(DISTINCT CASE WHEN wicket IS NOT NULL THEN over || '.' || ball END) as wickets,
            MAX(CAST(over AS INTEGER)) as overs,
            COUNT(*) as balls
        FROM balls
        GROUP BY innings, batting_team, bowling_team
    )
    SELECT 
        i1.batting_team as team1,
        i1.total_runs as team1_score,
        i1.wickets as team1_wickets,
        i1.overs || '.' || (i1.balls % 6) as team1_overs,
        i2.batting_team as team2,
        COALESCE(i2.total_runs, 0) as team2_score,
        COALESCE(i2.wickets, 0) as team2_wickets,
        COALESCE(i2.overs, 0) || '.' || COALESCE(i2.balls % 6, 0) as team2_overs,
        CASE 
            WHEN i2.innings IS NULL THEN 'Match in progress - ' || i1.batting_team || ' batting first'
            WHEN i2.total_runs > i1.total_runs THEN i2.batting_team || ' won by ' || (10 - i2.wickets) || ' wickets'
            WHEN i2.wickets = 10 AND i1.total_runs > i2.total_runs THEN i1.batting_team || ' won by ' || (i1.total_runs - i2.total_runs) || ' runs'
            WHEN i1.total_runs = i2.total_runs AND i2.wickets = 10 THEN 'Match Tied'
            ELSE i2.batting_team || ' needs ' || (i1.total_runs - i2.total_runs + 1) || ' runs to win'
        END as result
    FROM innings_summary i1
    LEFT JOIN innings_summary i2 ON i1.innings = 1 AND i2.innings = 2
    WHERE i1.innings = 1
    """
    return fetch_data(query, conn)

def main():
    """Main dashboard function"""
    
    # Header
    st.markdown('<div class="main-header">🏏 Live Cricket Match Dashboard</div>', unsafe_allow_html=True)
    st.caption("📍 Reading from: data/staging/cricket_staging.db")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Dashboard Settings")
        refresh_rate = st.slider("Auto-refresh (seconds)", 1, 30, 5)
        show_ball_by_ball = st.checkbox("Show Ball-by-Ball", value=True)
        show_playing_xi = st.checkbox("Show Playing XI", value=True)
        
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        
        conn = get_database_connection()
        if conn:
            stats = fetch_data("SELECT COUNT(*) as balls, SUM(runs_scored) as runs, SUM(CASE WHEN wicket=1 THEN 1 ELSE 0 END) as wickets FROM balls", conn)
            if not stats.empty:
                st.metric("Total Balls", stats['balls'].iloc[0])
                st.metric("Total Runs", int(stats['runs'].iloc[0]) if stats['runs'].iloc[0] else 0)
                st.metric("Wickets", stats['wickets'].iloc[0])
        
        st.markdown("---")
        st.info("📊 Live data from staging database")
    
    # Get database connection
    conn = get_database_connection()
    
    if conn is None:
        st.error("❌ Cannot connect to staging database")
        st.info("💡 Make sure data/staging/cricket_staging.db exists")
        st.info("💡 Start consumer: `python run_consumer_sqlite.py`")
        return
    
    # Check if data exists
    check = fetch_data("SELECT COUNT(*) as count FROM balls", conn)
    if check.empty or check['count'].iloc[0] == 0:
        st.warning("⚠️ No match data in staging database")
        st.info("💡 Start match: `python run_match.py`")
        st.info("💡 Start consumer: `python run_consumer_sqlite.py`")
        return
    
    # Get match info
    match_info = get_match_info(conn)
    current_score = get_current_score(conn)
    
    if match_info.empty:
        st.error("No match data")
        return
    
    info = match_info.iloc[0]
    score = current_score.iloc[0] if not current_score.empty else None
    
    # Match Header
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"### 📍 {info['venue']}")
        st.markdown(f"**{info['batting_team']}** vs **{info['bowling_team']}**")
    
    with col2:
        st.markdown(f"**Day {info['day']}** - {info['session']}")
        st.markdown(f"**Innings:** {info['innings']}")
    
    if not current_score.empty:
        score_info = current_score.iloc[0]
        st.markdown("### 🏏 Match Status")
        if score_info.get('match_status'):
            st.success(score_info['match_status'])
        
        st.markdown("### 📊 Current Score")
        score_col1, score_col2 = st.columns(2)
        with score_col1:
            st.metric(
                score_info['batting_team'],
                f"{score_info['total_runs']}/{score_info['wickets']}",
                f"Overs: {score_info['current_over']}"
            )
        with score_col2:
            st.metric("Run Rate", f"{score_info['run_rate']:.2f}")
    
    st.markdown("---")
    
    # Live Score
    st.markdown("## 📊 Live Score")
    
    if not current_score.empty:
        score_col1, score_col2, score_col3 = st.columns(3)
        
        score_info = current_score.iloc[0]
        with score_col1:
            st.markdown('<div class="score-card">', unsafe_allow_html=True)
            st.markdown(f"### {score_info['total_runs']}/{score_info['wickets']}")
            st.markdown(f"**{score_info['batting_team']}**")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with score_col2:
            st.metric("Run Rate", f"{score_info['run_rate']:.2f}")
        
        with score_col3:
            st.metric("Overs", f"{score_info['current_over']}")
    
    st.markdown("---")
    
    # Current Players
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏏 Batsmen at Crease")
        batsmen = get_current_batsmen(conn)
        
        if not batsmen.empty:
            for idx, bat in batsmen.iterrows():
                st.markdown(f"""
                <div class="metric-card" style="margin-bottom: 1rem;">
                    <h4>{'⭐ ' if idx == 0 else '   '}{bat['batsman']}</h4>
                    <p style="font-size: 1.2rem; margin: 0;">
                        <strong>{int(bat['runs'])}*</strong> ({int(bat['balls'])})
                        <span style="color: #666;"> | SR: {bat['strike_rate']:.1f}</span>
                    </p>
                    <p style="color: #666; margin: 0;">
                        [{int(bat.get('fours', 0))}×4  {int(bat.get('sixes', 0))}×6]
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            partnership = get_partnership(conn)
            if not partnership.empty:
                p = partnership.iloc[0]
                st.info(f"🤝 Partnership: **{int(p['runs'])} runs** ({int(p['balls'])} balls)")
        else:
            st.warning("No batsmen data")
    
    with col2:
        st.markdown("### 🎯 Current Bowler")
        bowler = get_current_bowler(conn)
        
        if not bowler.empty:
            b = bowler.iloc[0]
            st.markdown(f"""
            <div class="metric-card">
                <h4>{b['bowler']}</h4>
                <p style="font-size: 1.2rem; margin: 0;">
                    <strong>{b['overs']}-{int(b['runs'])}-{int(b['wickets'])}</strong>
                </p>
                <p style="color: #666; margin: 0;">
                    Economy: {b['economy']:.2f} | Dots: {int(b['dots'])}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 🌱 Pitch")
        st.info(f"📍 {info['pitch_condition']}")
    
    st.markdown("---")
    
    # Playing XI
    if show_playing_xi:
        st.markdown("## 👥 Playing XI")
        playing_xi = get_playing_xi(conn)
        
        if not playing_xi.empty:
            teams = playing_xi['team'].unique()
            
            if len(teams) >= 2:
                xi_col1, xi_col2 = st.columns(2)
                
                with xi_col1:
                    team1_players = playing_xi[playing_xi['team'] == teams[0]]['player'].tolist()
                    st.markdown(f"""
                    ### {teams[0]} 
                    <span style='color: gray; font-size: 0.9em;'>({len(team1_players)} players)</span>
                    """, unsafe_allow_html=True)
                    
                    for i, player in enumerate(sorted(team1_players), 1):
                        st.markdown(f"""
                        <div style='padding: 4px 10px; margin: 2px 0; border-radius: 4px; background-color: #f0f2f6;'>
                            {i}. {player}
                        </div>
                        """, unsafe_allow_html=True)
                
                with xi_col2:
                    team2_players = playing_xi[playing_xi['team'] == teams[1]]['player'].tolist()
                    st.markdown(f"""
                    ### {teams[1]}
                    <span style='color: gray; font-size: 0.9em;'>({len(team2_players)} players)</span>
                    """, unsafe_allow_html=True)
                    
                    for i, player in enumerate(sorted(team2_players), 1):
                        st.markdown(f"""
                        <div style='padding: 4px 10px; margin: 2px 0; border-radius: 4px; background-color: #f0f2f6;'>
                            {i}. {player}
                        </div>
                        """, unsafe_allow_html=True)
            elif len(teams) == 1:
                team_players = playing_xi[playing_xi['team'] == teams[0]]['player'].tolist()
                st.markdown(f"""
                ### {teams[0]}
                <span style='color: gray; font-size: 0.9em;'>({len(team_players)} players)</span>
                """, unsafe_allow_html=True)
                
                for i, player in enumerate(sorted(team_players), 1):
                    st.markdown(f"""
                    <div style='padding: 4px 10px; margin: 2px 0; border-radius: 4px; background-color: #f0f2f6;'>
                        {i}. {player}
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Run Progression
    st.markdown("## 📈 Run Progression")
    runs_df = get_run_progression(conn)
    
    if not runs_df.empty:
        fig = go.Figure()
        
        # Main run progression line
        fig.add_trace(go.Scatter(
            x=runs_df['over'] + runs_df['ball']/6,  # Convert to decimal overs
            y=runs_df['running_total'],
            mode='lines+markers',
            name='Total Runs',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=5),
            hovertemplate="Over %{x:.1f}<br>" +
                        "Score: %{customdata}<br>" +
                        "Runs: %{y}",
            customdata=runs_df['cumulative_score']
        ))
        
        # Mark wickets
        wicket_df = runs_df[runs_df['wicket'] == 1]
        if not wicket_df.empty:
            fig.add_trace(go.Scatter(
                x=wicket_df['over'] + wicket_df['ball']/6,
                y=wicket_df['running_total'],
                mode='markers',
                name='Wickets',
                marker=dict(size=12, color='red', symbol='x'),
                hovertemplate="Over %{x:.1f}<br>" +
                            "Score: %{customdata}",
                customdata=wicket_df['cumulative_score']
            ))
        
        fig.update_layout(
            title="Run Progression Over Time",
            xaxis_title="Overs",
            yaxis_title="Runs",
            hovermode='closest',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("### 🏆 Top Scorers")
        top_batsmen = get_all_batsmen(conn)
        
        if not top_batsmen.empty:
            top_5 = top_batsmen.head(5)
            fig = px.bar(
                top_5,
                x='runs',
                y='batsman',
                orientation='h',
                text='runs',
                color='strike_rate',
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=300, showlegend=False, xaxis_title="Runs", yaxis_title="")
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
    
    with chart_col2:
        st.markdown("### 📉 Dismissals")
        dismissals = get_dismissal_types(conn)
        
        if not dismissals.empty:
            fig = px.pie(
                dismissals,
                values='count',
                names='dismissal_type',
                hole=0.4
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No wickets yet")
    
    # Ball-by-Ball
    if show_ball_by_ball:
        st.markdown("---")
        st.markdown("## 🎯 Over-by-Over Breakdown")
        
        overs = get_over_summary(conn)
        
        if not overs.empty:
            # Show last 10 overs
            recent_overs = overs.tail(10)
            
            for _, over in recent_overs.iterrows():
                over_num = int(over['over'])
                runs = int(over['runs'])
                wickets = int(over['wickets'])
                balls_str = over['ball_by_ball']
                
                # Create ball display
                balls_html = ""
                if balls_str:
                    for ball in balls_str.split():
                        if ball == 'W':
                            balls_html += f'<span class="ball-by-ball ball-wicket">{ball}</span>'
                        elif ball == '•':
                            balls_html += f'<span class="ball-by-ball ball-dot">{ball}</span>'
                        elif ball in ['4', '6']:
                            css_class = 'ball-boundary' if ball == '4' else 'ball-six'
                            balls_html += f'<span class="ball-by-ball {css_class}">{ball}</span>'
                        else:
                            balls_html += f'<span class="ball-by-ball ball-single">{ball}</span>'
                
                st.markdown(f"""
                <div class="metric-card" style="margin-bottom: 0.5rem;">
                    <strong>Over {over_num}</strong> - {runs} run{'' if runs == 1 else 's'}{' | ' + str(wickets) + ' wicket' if wickets > 0 else ''}
                    <br>
                    {balls_html}
                </div>
                """, unsafe_allow_html=True)
    
    # Detailed Scorecard
    st.markdown("## 📋 Match Scorecard")
    
    scorecard = get_detailed_scorecard(conn)
    if not scorecard['batting'].empty:
        # First Innings
        first_inning_bat = scorecard['batting'][scorecard['batting']['innings'] == 1]
        first_inning_bowl = scorecard['bowling'][scorecard['bowling']['innings'] == 1]
        
        if not first_inning_bat.empty:
            team_name = first_inning_bat.iloc[0]['batting_team']
            total_runs = first_inning_bat['runs'].sum()
            total_wickets = len(first_inning_bat[first_inning_bat['dismissal'].notna()])
            
            st.markdown(f"""
            ### {team_name} Innings - {total_runs}/{total_wickets}
            """)
            
            # Batting
            st.markdown("#### Batting")
            batting_df = first_inning_bat[['batsman', 'runs', 'balls', 'fours', 'sixes', 'strike_rate', 'dismissal']]
            st.markdown("""
            <style>
            .batsman-table {
                font-size: 14px;
                margin: 10px 0;
                padding: 8px;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
            .not-out {
                color: #2e7d32;
            }
            .out {
                color: #d32f2f;
            }
            </style>
            """, unsafe_allow_html=True)
            
            for _, row in batting_df.iterrows():
                dismissal_text = row['dismissal'] if pd.notna(row['dismissal']) else 'not out'
                dismissal_class = 'not-out' if dismissal_text == 'not out' else 'out'
                
                st.markdown(f"""
                <div class='batsman-table'>
                    <strong>{row['batsman']}</strong> 
                    <span class='{dismissal_class}'>{dismissal_text}</span><br/>
                    {int(row['runs'])} ({int(row['balls'])} balls) • {int(row['fours'])}×4 • {int(row['sixes'])}×6 • SR: {row['strike_rate']:.2f}
                </div>
                """, unsafe_allow_html=True)
            
            # Bowling
            st.markdown("#### Bowling")
            bowling_df = first_inning_bowl[['bowler', 'overs', 'runs', 'wickets', 'dots', 'economy']]
            st.table(bowling_df.style.format({
                'economy': '{:.2f}',
                'dots': '{:.0f}',
                'runs': '{:.0f}',
                'wickets': '{:.0f}'
            }))
        
        # Second Innings
        second_inning_bat = scorecard['batting'][scorecard['batting']['innings'] == 2]
        second_inning_bowl = scorecard['bowling'][scorecard['bowling']['innings'] == 2]
        
        if not second_inning_bat.empty:
            team_name = second_inning_bat.iloc[0]['batting_team']
            total_runs = second_inning_bat['runs'].sum()
            total_wickets = len(second_inning_bat[second_inning_bat['dismissal'] != 'not out'])
            
            st.markdown(f"""
            ### {team_name} Innings - {total_runs}/{total_wickets}
            """)
            
            # Batting
            st.markdown("#### Batting")
            batting_df = second_inning_bat[['batsman', 'runs', 'balls', 'fours', 'sixes', 'strike_rate', 'dismissal']]
            
            for _, row in batting_df.iterrows():
                dismissal_text = row['dismissal'] if pd.notna(row['dismissal']) else 'not out'
                dismissal_class = 'not-out' if dismissal_text == 'not out' else 'out'
                
                st.markdown(f"""
                <div class='batsman-table'>
                    <strong>{row['batsman']}</strong> 
                    <span class='{dismissal_class}'>{dismissal_text}</span><br/>
                    {int(row['runs'])} ({int(row['balls'])} balls) • {int(row['fours'])}×4 • {int(row['sixes'])}×6 • SR: {row['strike_rate']:.2f}
                </div>
                """, unsafe_allow_html=True)
            
            # Bowling
            st.markdown("#### Bowling")
            bowling_df = second_inning_bowl[['bowler', 'overs', 'runs', 'wickets', 'dots', 'economy']]
            st.table(bowling_df.style.format({
                'economy': '{:.2f}',
                'dots': '{:.0f}',
                'runs': '{:.0f}',
                'wickets': '{:.0f}'
            }))
    
    # Wickets
    st.markdown("---")
    st.markdown("### 🔴 Fall of Wickets")
    wickets = get_wickets(conn)
    
    if not wickets.empty:
        for _, w in wickets.iterrows():
            fielder_info = f" c {w['fielder']}" if w['fielder'] else ""
            st.markdown(f"""
            <div style="background-color: #ffe6e6; padding: 1rem; border-radius: 5px; margin-bottom: 0.5rem;">
                <strong>{w['over_ball']}</strong> - {w['batsman']} {int(w['runs'])} ({int(w['balls'])})
                <br>
                <span style="color: #666;">{w['dismissal_type']}{fielder_info} | Bowler: {w['bowler']} | Score: {w['cumulative_score']}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No wickets fallen yet")
    
    # Auto-refresh
    time.sleep(refresh_rate)
    st.rerun()


if __name__ == "__main__":
    main()