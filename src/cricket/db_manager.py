"""
Database Manager for Cricket Pipeline
Handles staging and production databases
"""

import sqlite3
from datetime import datetime
import os
import shutil


class CricketDBManager:
    def __init__(self):
        self.staging_db_path = 'data/staging/cricket_staging.db'
        self.prod_db_path = 'data/production/cricket_prod.db'
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs('data/staging', exist_ok=True)
        os.makedirs('data/production', exist_ok=True)
        os.makedirs('data/archive', exist_ok=True)

    def _create_tables(self, conn):
        """Create required tables in database"""
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
        
        # Match metadata
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_metadata (
            match_id TEXT PRIMARY KEY,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            version TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()

    def init_staging_db(self):
        """Initialize staging database"""
        conn = sqlite3.connect(self.staging_db_path)
        self._create_tables(conn)
        conn.close()
        print(f"✅ Staging database initialized: {self.staging_db_path}")
        return self.staging_db_path

    def init_prod_db(self):
        """Initialize production database"""
        conn = sqlite3.connect(self.prod_db_path)
        self._create_tables(conn)
        conn.close()
        print(f"✅ Production database initialized: {self.prod_db_path}")
        return self.prod_db_path

    def get_staging_connection(self):
        """Get connection to staging database"""
        return sqlite3.connect(self.staging_db_path)

    def get_prod_connection(self):
        """Get connection to production database"""
        return sqlite3.connect(self.prod_db_path)

    def archive_match(self, match_id):
        """Archive a completed match to production database"""
        staging_conn = self.get_staging_connection()
        prod_conn = self.get_prod_connection()
        
        try:
            # Get match data from staging
            staging_cursor = staging_conn.cursor()
            
            # Generate version number based on timestamp
            version = datetime.now().strftime("v%Y%m%d_%H%M")
            
            # Update match metadata
            staging_cursor.execute("""
                INSERT OR REPLACE INTO match_metadata (
                    match_id, start_time, end_time, version, status
                ) VALUES (
                    ?, 
                    (SELECT MIN(created_at) FROM balls WHERE match_id = ?),
                    (SELECT MAX(created_at) FROM balls WHERE match_id = ?),
                    ?,
                    'COMPLETED'
                )
            """, (match_id, match_id, match_id, version))
            
            # Copy data to production
            tables = ['balls', 'session_summaries', 'player_innings', 'match_metadata']
            
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
            
            # Clear match data from staging
            for table in tables:
                staging_cursor.execute(f"DELETE FROM {table} WHERE match_id = ?", (match_id,))
            
            staging_conn.commit()
            print(f"✅ Match {match_id} archived successfully as version {version}")
            
        finally:
            staging_conn.close()
            prod_conn.close()

    def clear_staging_db(self):
        """Clear all data from staging database"""
        conn = self.get_staging_connection()
        cursor = conn.cursor()
        
        try:
            tables = ['balls', 'session_summaries', 'player_innings', 'match_metadata']
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
            conn.commit()
            print("✅ Staging database cleared")
        finally:
            conn.close()

    def backup_prod_db(self):
        """Create a backup of the production database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        backup_path = f'data/archive/cricket_prod_{timestamp}.db'
        
        if os.path.exists(self.prod_db_path):
            shutil.copy2(self.prod_db_path, backup_path)
            print(f"✅ Production database backed up to: {backup_path}")