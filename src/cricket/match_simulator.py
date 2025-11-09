"""
Cricket Test Match Simulator
Generates realistic ball-by-ball data for 5-day Test match
"""

from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime, timedelta
from .players import INDIA_SQUAD, AUSTRALIA_SQUAD, FIELDERS
from .pitch_conditions import (
    get_pitch_condition,
    get_outcome_probabilities,
    get_dismissal_type,
    get_shot_type
)


class TestMatchSimulator:
    def __init__(self, kafka_broker='localhost:9092', speed_multiplier=1.0):
        """
        Initialize Test Match Simulator
        
        speed_multiplier: 1.0 = real-time (3 sec per ball)
                         0.1 = 10x faster (0.3 sec per ball)
                         2.0 = slower (6 sec per ball)
        """
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_broker,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        self.speed_multiplier = speed_multiplier
        self.match_id = "IND_vs_AUS_2024_TEST_Chennai_01"
        self.venue = "M. A. Chidambaram Stadium, Chennai"
        
        # Match state
        self.current_day = 1
        self.current_session = "Morning"  # Morning, Afternoon, Evening
        self.innings = 1
        self.batting_team = "India"
        self.bowling_team = "Australia"
        
        # Scoreboard
        self.total_runs = 0
        self.wickets = 0
        self.overs = 0
        self.balls_in_over = 0
        
        # Current players
        self.striker = None
        self.non_striker = None
        self.bowler = None
        
        # Player stats
        self.batsman_stats = {}  # {name: {runs, balls, fours, sixes}}
        self.bowler_stats = {}   # {name: {overs, runs, wickets, maidens}}
        self.partnership = 0
        self.partnership_balls = 0
        
        # Initialize teams
        self.india_batsmen = INDIA_SQUAD["batsmen"].copy()
        self.india_bowlers = INDIA_SQUAD["bowlers"].copy()
        self.aus_batsmen = AUSTRALIA_SQUAD["batsmen"].copy()
        self.aus_bowlers = AUSTRALIA_SQUAD["bowlers"].copy()
        
        # Batting order
        self.batting_order = []
        self.batting_position = 0
        
        # Match time tracking
        self.match_start_time = datetime.now()
        self.current_ball_time = self.match_start_time
        
    
    def initialize_innings(self):
        """Set up batting and bowling for current innings"""
        if self.batting_team == "India":
            self.batting_order = sorted(self.india_batsmen, key=lambda x: x['batting_position'])
            self.available_bowlers = self.aus_bowlers.copy()
        else:
            self.batting_order = sorted(self.aus_batsmen, key=lambda x: x['batting_position'])
            self.available_bowlers = self.india_bowlers.copy()
        
        # Set opening batsmen
        self.striker = self.batting_order[0]
        self.non_striker = self.batting_order[1]
        self.batting_position = 2  # Next batsman index
        
        # Initialize stats
        for batsman in self.batting_order:
            self.batsman_stats[batsman['name']] = {
                'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0, 'out': False
            }
        
        for bowler in self.available_bowlers:
            self.bowler_stats[bowler['name']] = {
                'overs': 0, 'balls': 0, 'runs': 0, 'wickets': 0, 'maidens': 0, 'dots_in_over': 0
            }
        
        # Select opening bowler
        self.bowler = self.select_bowler()
        
        print(f"\n{'='*60}")
        print(f"🏏 INNINGS {self.innings}: {self.batting_team} Batting")
        print(f"{'='*60}")
        print(f"Openers: {self.striker['name']} & {self.non_striker['name']}")
        print(f"Opening Bowler: {self.bowler['name']}")
        print(f"{'='*60}\n")
    
    
    def select_bowler(self):
        """Select bowler based on pitch conditions and overs bowled"""
        pitch = get_pitch_condition(self.current_day, self.current_session, self.overs)
        
        # Get pace and spin bowlers
        pacers = [b for b in self.available_bowlers if b['bowling_speed'] == 'Fast']
        spinners = [b for b in self.available_bowlers if b['bowling_speed'] == 'Spin']
        
        # Decide based on pitch
        if pitch['pace_effectiveness'] > pitch['spin_effectiveness']:
            # Prefer pacers
            available = pacers if pacers else spinners
        else:
            # Prefer spinners
            available = spinners if spinners else pacers
        
        # Select bowler who has bowled least
        if available:
            available.sort(key=lambda x: self.bowler_stats[x['name']]['overs'])
            return available[0]
        else:
            return self.available_bowlers[0]
    
    
    def get_new_batsman(self):
        """Return next batsman after wicket"""
        if self.batting_position < len(self.batting_order):
            new_batsman = self.batting_order[self.batting_position]
            self.batting_position += 1
            return new_batsman
        return None
    
    
    def swap_strike(self):
        """Swap striker and non-striker"""
        self.striker, self.non_striker = self.non_striker, self.striker
    
    
    def simulate_ball(self):
        """Simulate one ball and return event data"""
        
        # Get pitch condition
        pitch = get_pitch_condition(self.current_day, self.current_session, self.overs)
        
        # Get batsman skill vs this bowling
        batsman = self.striker
        bowler = self.bowler
        
        if bowler['bowling_speed'] == 'Fast':
            batsman_skill = batsman['vs_pace_skill']
        else:
            batsman_skill = batsman['vs_spin_skill']
        
        # Get outcome probabilities
        weights = get_outcome_probabilities(
            pitch,
            bowler['bowling_speed'],
            batsman_skill,
            batsman['aggression']
        )
        
        # Simulate outcome
        outcomes = [0, 1, 2, 3, 4, 6, 'W']
        outcome = random.choices(outcomes, weights=weights, k=1)[0]
        
        # Process outcome
        is_wicket = outcome == 'W'
        runs = 0 if is_wicket else outcome
        
        # Build ball event
        ball_event = {
            'match_id': self.match_id,
            'venue': self.venue,
            'match_type': 'Test',
            
            'day': self.current_day,
            'session': self.current_session,
            'innings': self.innings,
            'batting_team': self.batting_team,
            'bowling_team': self.bowling_team,
            
            'over': self.overs,
            'ball': self.balls_in_over + 1,
            
            'batsman': batsman['name'],
            'batsman_runs': self.batsman_stats[batsman['name']]['runs'],
            'batsman_balls': self.batsman_stats[batsman['name']]['balls'],
            
            'non_striker': self.non_striker['name'],
            'bowler': bowler['name'],
            
            'runs_scored': runs,
            'extras': 0,
            'total_runs': runs,
            
            'wicket': is_wicket,
            'dismissal_type': None,
            'fielder': None,
            
            'shot_type': get_shot_type(runs, is_wicket),
            'pitch_condition': pitch['description'],
            
            'cumulative_score': f"{self.total_runs}/{self.wickets}",
            'run_rate': round(self.total_runs / max(1, self.overs + (self.balls_in_over / 6)), 2),
            
            'partnership_runs': self.partnership,
            'partnership_balls': self.partnership_balls,
            
            'timestamp': self.current_ball_time.isoformat()
        }
        
        # Update stats
        if not is_wicket:
            self.total_runs += runs
            self.batsman_stats[batsman['name']]['runs'] += runs
            self.batsman_stats[batsman['name']]['balls'] += 1
            self.bowler_stats[bowler['name']]['runs'] += runs
            self.partnership += runs
            self.partnership_balls += 1
            
            if runs == 4:
                self.batsman_stats[batsman['name']]['fours'] += 1
            elif runs == 6:
                self.batsman_stats[batsman['name']]['sixes'] += 1
            
            if runs == 0:
                self.bowler_stats[bowler['name']]['dots_in_over'] += 1
            
            # Swap strike for odd runs
            if runs % 2 == 1:
                self.swap_strike()
        
        else:
            # Wicket!
            dismissal = get_dismissal_type(pitch, bowler['bowling_speed'])
            ball_event['dismissal_type'] = dismissal
            
            if dismissal in ["Caught", "Caught behind", "Caught in slips"]:
                ball_event['fielder'] = random.choice(FIELDERS)
            elif dismissal == "Stumped":
                # Get keeper name
                keepers = [b for b in (self.aus_batsmen if self.batting_team == "India" else self.india_batsmen) 
                          if b.get('is_keeper', False)]
                ball_event['fielder'] = keepers[0]['name'] if keepers else "Keeper"
            
            self.wickets += 1
            self.batsman_stats[batsman['name']]['balls'] += 1
            self.batsman_stats[batsman['name']]['out'] = True
            self.bowler_stats[bowler['name']]['wickets'] += 1
            
            # Reset partnership
            self.partnership = 0
            self.partnership_balls = 0
        
        # Update bowler stats
        self.bowler_stats[bowler['name']]['balls'] += 1
        
        # Progress ball count
        self.balls_in_over += 1
        self.current_ball_time += timedelta(seconds=3 * self.speed_multiplier)
        
        # Check for over completion
        if self.balls_in_over == 6:
            self.overs += 1
            self.balls_in_over = 0
            
            # Check for maiden over
            if self.bowler_stats[bowler['name']]['dots_in_over'] == 6:
                self.bowler_stats[bowler['name']]['maidens'] += 1
            
            self.bowler_stats[bowler['name']]['overs'] += 1
            self.bowler_stats[bowler['name']]['dots_in_over'] = 0
            
            # Swap strike at end of over
            self.swap_strike()
            
            # Change bowler
            self.bowler = self.select_bowler()
        
        return ball_event, is_wicket
    
    
    def print_ball_commentary(self, ball_event, is_wicket):
        """Print human-readable commentary"""
        over_ball = f"{ball_event['over']}.{ball_event['ball']}"
        batsman = ball_event['batsman']
        bowler = ball_event['bowler']
        runs = ball_event['runs_scored']
        shot = ball_event['shot_type']
        score = ball_event['cumulative_score']
        
        if is_wicket:
            dismissal = ball_event['dismissal_type']
            batsman_score = f"{ball_event['batsman_runs']} ({ball_event['batsman_balls']})"
            fielder = f" c {ball_event['fielder']}" if ball_event['fielder'] else ""
            
            print(f"🔴 {over_ball:6} WICKET! {batsman} {dismissal}{fielder}!")
            print(f"         {batsman} {batsman_score} | {self.batting_team} {score}")
        elif runs == 6:
            print(f"💥 {over_ball:6} SIX! {batsman} - {shot}")
            print(f"         {self.batting_team} {score}")
        elif runs == 4:
            print(f"🔥 {over_ball:6} FOUR! {batsman} - {shot}")
            print(f"         {self.batting_team} {score}")
        elif runs == 0:
            print(f"⚪ {over_ball:6} Dot ball. {batsman} - {shot}")
        else:
            print(f"⚫ {over_ball:6} {runs} run(s). {batsman} - {shot}")
            if runs % 2 == 1:
                print(f"         Strike rotated. {self.batting_team} {score}")
    
    
    def print_session_summary(self):
        """Print session summary"""
        print(f"\n{'='*60}")
        print(f"📊 END OF {self.current_session.upper()} SESSION - DAY {self.current_day}")
        print(f"{'='*60}")
        print(f"{self.batting_team}: {self.total_runs}/{self.wickets} ({self.overs}.{self.balls_in_over} overs)")
        print(f"Run Rate: {self.total_runs / max(1, self.overs + self.balls_in_over/6):.2f}")
        print(f"\n🏏 At the crease:")
        if not self.batsman_stats[self.striker['name']]['out']:
            stats = self.batsman_stats[self.striker['name']]
            sr = (stats['runs'] / max(1, stats['balls'])) * 100
            print(f"   {self.striker['name']:20} {stats['runs']:3}* ({stats['balls']:3}) SR: {sr:.1f}  [{stats['fours']}×4, {stats['sixes']}×6]")
        if not self.batsman_stats[self.non_striker['name']]['out']:
            stats = self.batsman_stats[self.non_striker['name']]
            sr = (stats['runs'] / max(1, stats['balls'])) * 100
            print(f"   {self.non_striker['name']:20} {stats['runs']:3}* ({stats['balls']:3}) SR: {sr:.1f}  [{stats['fours']}×4, {stats['sixes']}×6]")
        
        print(f"\n⚡ Current bowler:")
        bstats = self.bowler_stats[self.bowler['name']]
        economy = bstats['runs'] / max(1, bstats['overs'] + bstats['balls']/6)
        print(f"   {self.bowler['name']:20} {bstats['overs']}.{bstats['balls']}-{bstats['maidens']}-{bstats['runs']}-{bstats['wickets']}  Econ: {economy:.2f}")
        
        print(f"\n🎯 Pitch: {get_pitch_condition(self.current_day, self.current_session, self.overs)['description']}")
        print(f"{'='*60}\n")
    
    
    def advance_session(self):
        """Move to next session"""
        session_order = ["Morning", "Afternoon", "Evening"]
        current_idx = session_order.index(self.current_session)
        
        if current_idx < 2:
            self.current_session = session_order[current_idx + 1]
            print(f"\n{'='*60}")
            print(f"🌅 SESSION CHANGE: {self.current_session.upper()} SESSION")
            print(f"{'='*60}\n")
            time.sleep(2 * self.speed_multiplier)
        else:
            # End of day
            self.current_day += 1
            self.current_session = "Morning"
            print(f"\n{'='*60}")
            print(f"🌙 STUMPS - END OF DAY {self.current_day - 1}")
            print(f"{'='*60}")
            print(f"{self.batting_team}: {self.total_runs}/{self.wickets}")
            print(f"{'='*60}\n")
            
            if self.current_day <= 5:
                print(f"\n{'='*60}")
                print(f"🌄 DAY {self.current_day} - {self.current_session.upper()} SESSION")
                print(f"{'='*60}\n")
            
            time.sleep(3 * self.speed_multiplier)
    
    
    def is_innings_complete(self):
        """Check if innings should end"""
        # All out
        if self.wickets >= 10:
            return True
        
        # Declared (simplified: declare after 450 runs or Day 3+)
        if self.total_runs > 450 and self.current_day >= 3:
            return True
        
        # Test match specific: Max 2 innings per team typically
        return False
    
    
    def simulate_match(self):
        """Simulate complete Test match"""
        print(f"\n{'='*70}")
        print(f"🏏 TEST MATCH SIMULATION STARTING")
        print(f"{'='*70}")
        print(f"📍 Venue: {self.venue}")
        print(f"🇮🇳 India vs Australia 🇦🇺")
        print(f"⏱️  Speed: {self.speed_multiplier}x {'(Fast-forward)' if self.speed_multiplier < 1 else '(Real-time)' if self.speed_multiplier == 1 else '(Slow-motion)'}")
        print(f"{'='*70}\n")
        
        time.sleep(2 * self.speed_multiplier)
        
        try:
            # Initialize first innings
            self.initialize_innings()
            
            balls_in_session = 0
            session_length = 30  # Overs per session
            
            while self.current_day <= 5:
                
                # Simulate ball
                ball_event, is_wicket = self.simulate_ball()
                
                # Send to Kafka
                self.producer.send('cricket_live', value=ball_event)
                
                # Print commentary
                self.print_ball_commentary(ball_event, is_wicket)
                
                # Handle wicket
                if is_wicket:
                    if self.wickets >= 10:
                        print(f"\n🏁 ALL OUT! {self.batting_team} {self.total_runs}/{self.wickets}")
                        self.print_session_summary()
                        
                        # Check if match should continue (simplified logic)
                        if self.innings < 2:  # Just simulate 2 innings for now
                            self.innings += 1
                            self.batting_team, self.bowling_team = self.bowling_team, self.batting_team
                            self.total_runs = 0
                            self.wickets = 0
                            self.overs = 0
                            self.balls_in_over = 0
                            self.partnership = 0
                            self.partnership_balls = 0
                            
                            time.sleep(3 * self.speed_multiplier)
                            self.initialize_innings()
                            balls_in_session = 0
                        else:
                            print(f"\n🏆 MATCH COMPLETE!")
                            break
                    else:
                        # New batsman
                        new_batsman = self.get_new_batsman()
                        if new_batsman:
                            print(f"         {new_batsman['name']} comes to the crease\n")
                            self.striker = new_batsman
                            time.sleep(1 * self.speed_multiplier)
                
                # Wait between balls
                time.sleep(3 * self.speed_multiplier)
                
                # Track session progress
                if self.balls_in_over == 0:  # Completed an over
                    balls_in_session += 1
                    
                    # Session change after ~30 overs
                    if balls_in_session >= session_length:
                        self.print_session_summary()
                        self.advance_session()
                        balls_in_session = 0
                
                # Check innings completion
                if self.is_innings_complete():
                    if self.total_runs > 450:
                        print(f"\n📢 {self.batting_team} DECLARES at {self.total_runs}/{self.wickets}")
                    
                    self.print_session_summary()
                    
                    # Switch innings
                    if self.innings < 2:
                        self.innings += 1
                        self.batting_team, self.bowling_team = self.bowling_team, self.batting_team
                        self.total_runs = 0
                        self.wickets = 0
                        self.overs = 0
                        self.balls_in_over = 0
                        self.partnership = 0
                        self.partnership_balls = 0
                        
                        time.sleep(3 * self.speed_multiplier)
                        self.initialize_innings()
                        balls_in_session = 0
                    else:
                        print(f"\n🏆 MATCH COMPLETE!")
                        break
        
        except KeyboardInterrupt:
            print(f"\n\n🛑 Match simulation stopped by user")
            print(f"Final Score: {self.batting_team} {self.total_runs}/{self.wickets} ({self.overs}.{self.balls_in_over} overs)")
        
        finally:
            self.producer.close()
            print(f"\n{'='*70}")
            print(f"Thank you for watching! 🏏")
            print(f"{'='*70}\n")


def main():
    """Main entry point"""
    print("🏏 Cricket Test Match Simulator")
    print("=" * 70)
    print("\nSelect simulation speed:")
    print("1. Real-time (3 seconds per ball) - Realistic experience")
    print("2. Fast (0.5 seconds per ball) - Quick testing")
    print("3. Very Fast (0.1 seconds per ball) - Data generation")
    print("4. Custom")
    
    choice = input("\nEnter choice (1-4) [default: 2]: ").strip() or "2"
    
    speed_map = {
        "1": 1.0,
        "2": 0.17,  # ~0.5 seconds
        "3": 0.033, # ~0.1 seconds
    }
    
    if choice == "4":
        multiplier = float(input("Enter speed multiplier (e.g., 0.1 for 10x faster): "))
    else:
        multiplier = speed_map.get(choice, 0.17)
    
    print(f"\n🏏 Starting match simulation at {multiplier}x speed...")
    print("Press Ctrl+C to stop\n")
    time.sleep(2)
    
    simulator = TestMatchSimulator(speed_multiplier=multiplier)
    simulator.simulate_match()


if __name__ == "__main__":
    main()