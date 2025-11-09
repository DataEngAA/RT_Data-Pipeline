"""
Cricket Teams and Player Data
"""

INDIA_SQUAD = {
    "batsmen": [
        {
            "name": "Rohit Sharma",
            "role": "Opening Batsman",
            "batting_position": 1,
            "batting_style": "Right-hand",
            "vs_pace_skill": 85,      # Out of 100
            "vs_spin_skill": 80,
            "aggression": 75,          # Higher = more attacking
            "technique": 85,           # Defense capability
            "is_captain": True
        },
        {
            "name": "Yashasvi Jaiswal",
            "role": "Opening Batsman",
            "batting_position": 2,
            "batting_style": "Left-hand",
            "vs_pace_skill": 78,
            "vs_spin_skill": 85,
            "aggression": 70,
            "technique": 80,
            "is_captain": False
        },
        {
            "name": "Shubman Gill",
            "role": "Top Order Batsman",
            "batting_position": 3,
            "batting_style": "Right-hand",
            "vs_pace_skill": 82,
            "vs_spin_skill": 80,
            "aggression": 65,
            "technique": 88,
            "is_captain": False
        },
        {
            "name": "Virat Kohli",
            "role": "Middle Order Batsman",
            "batting_position": 4,
            "batting_style": "Right-hand",
            "vs_pace_skill": 92,
            "vs_spin_skill": 88,
            "aggression": 70,
            "technique": 95,
            "is_captain": False
        },
        {
            "name": "Shreyas Iyer",
            "role": "Middle Order Batsman",
            "batting_position": 5,
            "batting_style": "Right-hand",
            "vs_pace_skill": 80,
            "vs_spin_skill": 75,
            "aggression": 75,
            "technique": 80,
            "is_captain": False
        },
        {
            "name": "Rishabh Pant",
            "role": "Wicket Keeper Batsman",
            "batting_position": 6,
            "batting_style": "Left-hand",
            "vs_pace_skill": 82,
            "vs_spin_skill": 85,
            "aggression": 90,
            "technique": 75,
            "is_captain": False,
            "is_keeper": True
        },
        {
            "name": "Ravindra Jadeja",
            "role": "All-rounder",
            "batting_position": 7,
            "batting_style": "Left-hand",
            "vs_pace_skill": 75,
            "vs_spin_skill": 80,
            "aggression": 70,
            "technique": 78,
            "is_captain": False
        }
    ],
    "bowlers": [
        {
            "name": "Ravichandran Ashwin",
            "role": "Spin Bowler",
            "bowling_style": "Off-spin",
            "bowling_speed": "Spin",
            "skill_vs_left": 90,
            "skill_vs_right": 88,
            "variation": 92
        },
        {
            "name": "Jasprit Bumrah",
            "role": "Fast Bowler",
            "bowling_style": "Right-arm fast",
            "bowling_speed": "Fast",
            "skill_vs_left": 92,
            "skill_vs_right": 90,
            "variation": 88,
            "is_vice_captain": True
        },
        {
            "name": "Mohammed Shami",
            "role": "Fast Bowler",
            "bowling_style": "Right-arm fast",
            "bowling_speed": "Fast",
            "skill_vs_left": 85,
            "skill_vs_right": 87,
            "variation": 80
        },
        {
            "name": "Kuldeep Yadav",
            "role": "Spin Bowler",
            "bowling_style": "Wrist spin (Chinaman)",
            "bowling_speed": "Spin",
            "skill_vs_left": 80,
            "skill_vs_right": 85,
            "variation": 88
        }
    ]
}

AUSTRALIA_SQUAD = {
    "batsmen": [
        {
            "name": "Usman Khawaja",
            "role": "Opening Batsman",
            "batting_position": 1,
            "batting_style": "Left-hand",
            "vs_pace_skill": 82,
            "vs_spin_skill": 88,
            "aggression": 60,
            "technique": 90,
            "is_captain": False
        },
        {
            "name": "David Warner",
            "role": "Opening Batsman",
            "batting_position": 2,
            "batting_style": "Left-hand",
            "vs_pace_skill": 85,
            "vs_spin_skill": 75,
            "aggression": 85,
            "technique": 80,
            "is_captain": False
        },
        {
            "name": "Marnus Labuschagne",
            "role": "Top Order Batsman",
            "batting_position": 3,
            "batting_style": "Right-hand",
            "vs_pace_skill": 88,
            "vs_spin_skill": 82,
            "aggression": 65,
            "technique": 92,
            "is_captain": False
        },
        {
            "name": "Steve Smith",
            "role": "Middle Order Batsman",
            "batting_position": 4,
            "batting_style": "Right-hand",
            "vs_pace_skill": 90,
            "vs_spin_skill": 92,
            "aggression": 70,
            "technique": 95,
            "is_captain": False
        },
        {
            "name": "Travis Head",
            "role": "Middle Order Batsman",
            "batting_position": 5,
            "batting_style": "Left-hand",
            "vs_pace_skill": 80,
            "vs_spin_skill": 78,
            "aggression": 85,
            "technique": 78,
            "is_captain": False
        },
        {
            "name": "Cameron Green",
            "role": "All-rounder",
            "batting_position": 6,
            "batting_style": "Right-hand",
            "vs_pace_skill": 78,
            "vs_spin_skill": 75,
            "aggression": 72,
            "technique": 80,
            "is_captain": False
        },
        {
            "name": "Alex Carey",
            "role": "Wicket Keeper Batsman",
            "batting_position": 7,
            "batting_style": "Left-hand",
            "vs_pace_skill": 75,
            "vs_spin_skill": 80,
            "aggression": 70,
            "technique": 78,
            "is_captain": False,
            "is_keeper": True
        }
    ],
    "bowlers": [
        {
            "name": "Pat Cummins",
            "role": "Fast Bowler",
            "bowling_style": "Right-arm fast",
            "bowling_speed": "Fast",
            "skill_vs_left": 90,
            "skill_vs_right": 88,
            "variation": 85,
            "is_captain": True
        },
        {
            "name": "Mitchell Starc",
            "role": "Fast Bowler",
            "bowling_style": "Left-arm fast",
            "bowling_speed": "Fast",
            "skill_vs_left": 82,
            "skill_vs_right": 90,
            "variation": 88
        },
        {
            "name": "Josh Hazlewood",
            "role": "Fast Bowler",
            "bowling_style": "Right-arm fast",
            "bowling_speed": "Fast",
            "skill_vs_left": 88,
            "skill_vs_right": 88,
            "variation": 80
        },
        {
            "name": "Nathan Lyon",
            "role": "Spin Bowler",
            "bowling_style": "Off-spin",
            "bowling_speed": "Spin",
            "skill_vs_left": 88,
            "skill_vs_right": 90,
            "variation": 85
        }
    ]
}

# Fielders for dismissals
FIELDERS = [
    "First Slip", "Second Slip", "Gully", "Point", "Cover", 
    "Mid-off", "Mid-on", "Square Leg", "Fine Leg", "Third Man",
    "Deep Square", "Long-on", "Long-off"
]