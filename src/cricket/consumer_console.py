"""
Simple console consumer - just prints to screen
"""

from kafka import KafkaConsumer
import json


def main():
    consumer = KafkaConsumer(
        'cricket_live',
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='cricket-console-consumer'
    )
    
    print("🏏 Live Cricket Match - Console View")
    print("=" * 70)
    print("Listening to Kafka topic: cricket_live")
    print("Press Ctrl+C to stop\n")
    
    ball_count = 0
    
    try:
        for message in consumer:
            ball = message.value
            ball_count += 1
            
            over_ball = f"{ball['over']}.{ball['ball']}"
            batsman = ball['batsman']
            bowler = ball['bowler']
            runs = ball['runs_scored']
            score = ball['cumulative_score']
            
            if ball['wicket']:
                dismissal = ball['dismissal_type']
                print(f"\n🔴 {over_ball:6} WICKET! {batsman} - {dismissal}")
                print(f"         {ball['batting_team']} {score}")
                print(f"         {ball['batsman_runs']} ({ball['batsman_balls']})\n")
            elif runs == 6:
                print(f"💥 {over_ball:6} SIX! {batsman} | {score}")
            elif runs == 4:
                print(f"🔥 {over_ball:6} FOUR! {batsman} | {score}")
            else:
                print(f"⚪ {over_ball:6} {runs} run(s) | {score}")
            
            # Session summary every 30 balls
            if ball_count % 30 == 0:
                print(f"\n{'─'*70}")
                print(f"📊 After {ball_count} balls:")
                print(f"   {ball['batting_team']}: {score}")
                print(f"   Run Rate: {ball['run_rate']}")
                print(f"   Pitch: {ball['pitch_condition']}")
                print(f"{'─'*70}\n")
    
    except KeyboardInterrupt:
        print(f"\n\n🛑 Stopped. Balls watched: {ball_count}")
    
    finally:
        consumer.close()


if __name__ == "__main__":
    main()