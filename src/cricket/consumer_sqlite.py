"""
Cricket Consumer - Saves to SQLite
"""

from kafka import KafkaConsumer
import json
import sqlite3
import signal
import sys
import os
from datetime import datetime

# Set up database paths
DB_DIR = os.path.join('data')
STAGING_DIR = os.path.join(DB_DIR, 'staging')
PROD_DIR = os.path.join(DB_DIR, 'production')
ARCHIVE_DIR = os.path.join(DB_DIR, 'archive')

# Create directories if they don't exist
os.makedirs(STAGING_DIR, exist_ok=True)
os.makedirs(PROD_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

STAGING_DB = os.path.join(STAGING_DIR, 'cricket_staging.db')
PROD_DB = os.path.join(PROD_DIR, 'cricket_prod.db')


def init_database(db_path):
    """Initialize SQLite database with cricket tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ball-by-ball data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS balls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT,
        venue TEXT,
        day INTEGER,
        session TEXT,
        innings INTEGER,
        batting_team TEXT,
        bowling_team TEXT,
        over INTEGER,
        ball INTEGER,
        batsman TEXT,
        batsman_runs INTEGER,
        batsman_balls INTEGER,
        non_striker TEXT,
        bowler TEXT,
        runs_scored INTEGER,
        extras INTEGER,
        total_runs INTEGER,
        wicket BOOLEAN,
        dismissal_type TEXT,
        fielder TEXT,
        shot_type TEXT,
        pitch_condition TEXT,
        cumulative_score TEXT,
        run_rate REAL,
        partnership_runs INTEGER,
        partnership_balls INTEGER,
        timestamp TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Session summaries
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS session_summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT,
        day INTEGER,
        session TEXT,
        innings INTEGER,
        batting_team TEXT,
        runs_scored INTEGER,
        wickets_fallen INTEGER,
        overs_bowled REAL,
        run_rate REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Player statistics
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS player_innings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT,
        player_name TEXT,
        team TEXT,
        innings INTEGER,
        runs INTEGER,
        balls INTEGER,
        fours INTEGER,
        sixes INTEGER,
        strike_rate REAL,
        out BOOLEAN,
        dismissal_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    print("✅ Cricket database initialized: data/cricket.db\n")
    return conn


def archive_match(match_id, staging_conn, prod_conn):
    """Archive a completed match to production database"""
    try:
        # Get match data from staging
        staging_cursor = staging_conn.cursor()
        
        # Generate version number based on timestamp
        version = datetime.now().strftime("v%Y%m%d_%H%M")
        
        # Copy data to production
        tables = ['balls', 'session_summaries', 'player_innings']
        
        for table in tables:
            # Copy data for this match
            staging_cursor.execute(f"SELECT * FROM {table} WHERE match_id = ?", (match_id,))
            rows = staging_cursor.fetchall()
            
            if rows:
                # Get column names
                columns = [description[0] for description in staging_cursor.description]
                
                # Prepare insert statement
                placeholders = ','.join(['?' for _ in columns])
                insert_sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
                
                # Insert into production
                prod_cursor = prod_conn.cursor()
                prod_cursor.executemany(insert_sql, rows)
                prod_conn.commit()
        
        print(f"✅ Match {match_id} archived successfully as version {version}")
        
    except Exception as e:
        print(f"❌ Error archiving match {match_id}: {str(e)}")

def main():
    # Initialize databases
    staging_conn = init_database(STAGING_DB)
    prod_conn = init_database(PROD_DB)
    cursor = staging_conn.cursor()
    
    # Clear staging database
    tables = ['balls', 'session_summaries', 'player_innings']
    for table in tables:
        cursor.execute(f"DELETE FROM {table}")
    staging_conn.commit()
    print("✅ Staging database cleared")
    
    # Initialize Kafka consumer
    consumer = KafkaConsumer(
        'cricket_live',
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='cricket-sqlite-consumer'
    )
    
    print("👂 Listening for cricket match data...")
    print("Press Ctrl+C to stop\n")
    
    ball_count = 0
    
    try:
        for message in consumer:
            ball = message.value
            
            # Insert ball data
            cursor.execute('''
            INSERT INTO balls (
                match_id, venue, day, session, innings, batting_team, bowling_team,
                over, ball, batsman, batsman_runs, batsman_balls, non_striker, bowler,
                runs_scored, extras, total_runs, wicket, dismissal_type, fielder,
                shot_type, pitch_condition, cumulative_score, run_rate,
                partnership_runs, partnership_balls, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ball['match_id'], ball['venue'], ball['day'], ball['session'],
                ball['innings'], ball['batting_team'], ball['bowling_team'],
                ball['over'], ball['ball'], ball['batsman'], ball['batsman_runs'],
                ball['batsman_balls'], ball['non_striker'], ball['bowler'],
                ball['runs_scored'], ball['extras'], ball['total_runs'],
                ball['wicket'], ball.get('dismissal_type'), ball.get('fielder'),
                ball['shot_type'], ball['pitch_condition'], ball['cumulative_score'],
                ball['run_rate'], ball['partnership_runs'], ball['partnership_balls'],
                ball['timestamp']
            ))
            
            staging_conn.commit()
            ball_count += 1
            
            # Print progress
            emoji = "🔴" if ball['wicket'] else "💾"
            print(f"{emoji} Ball #{ball_count}: {ball['over']}.{ball['ball']} - "
                  f"{ball['batsman']} vs {ball['bowler']} → {ball['runs_scored']} run(s) | "
                  f"{ball['cumulative_score']}")
            
            # Print stats every 36 balls (6 overs)
            if ball_count % 36 == 0:
                cursor.execute("SELECT COUNT(*), SUM(runs_scored) FROM balls WHERE wicket = 0")
                total_balls, total_runs = cursor.fetchone()
                cursor.execute("SELECT COUNT(*) FROM balls WHERE wicket = 1")
                total_wickets = cursor.fetchone()[0]
                
                print(f"\n📊 Database Stats: {total_balls} balls | "
                      f"{total_runs} runs | {total_wickets} wickets\n")
            
            # Check for innings completion to archive
            if 'innings_complete' in ball and ball['innings_complete']:
                archive_match(ball['match_id'], staging_conn, prod_conn)
    
    except KeyboardInterrupt:
        print(f"\n\n🛑 Stopped consumer. Total balls saved: {ball_count}")
    
    finally:
        staging_conn.close()
        prod_conn.close()
        consumer.close()


if __name__ == "__main__":
    main()