"""
Pitch Evolution and Conditions for Chennai Test Match
"""

def get_pitch_condition(day, session, over):
    """
    Returns pitch characteristics based on match progression
    
    Day 1-2 (First two sessions): Pace-friendly
    Day 2 (Later) - Day 3: Batting paradise
    Day 4-5: Spin-friendly
    """
    
    conditions = {
        "description": "",
        "pace_effectiveness": 50,   # 0-100
        "spin_effectiveness": 50,   # 0-100
        "bounce": 50,               # 0-100
        "turn": 50,                 # 0-100
        "wicket_probability": 0.03  # Base probability
    }
    
    # Day 1 - Morning (Fresh pitch, moisture)
    if day == 1 and session == "Morning":
        conditions.update({
            "description": "Fresh pitch, morning moisture, early movement for pacers",
            "pace_effectiveness": 85,
            "spin_effectiveness": 30,
            "bounce": 75,
            "turn": 20,
            "wicket_probability": 0.05
        })
    
    # Day 1 - Post-lunch & Evening
    elif day == 1 and session in ["Afternoon", "Evening"]:
        conditions.update({
            "description": "Pitch settling, still favoring pacers",
            "pace_effectiveness": 75,
            "spin_effectiveness": 40,
            "bounce": 70,
            "turn": 25,
            "wicket_probability": 0.04
        })
    
    # Day 2 - Morning (Still some help for pacers)
    elif day == 2 and session == "Morning":
        conditions.update({
            "description": "Morning moisture, last good period for pacers",
            "pace_effectiveness": 70,
            "spin_effectiveness": 45,
            "bounce": 65,
            "turn": 30,
            "wicket_probability": 0.04
        })
    
    # Day 2 Afternoon - Day 3 (Batting paradise)
    elif (day == 2 and session in ["Afternoon", "Evening"]) or day == 3:
        conditions.update({
            "description": "Flat pitch, excellent for batting",
            "pace_effectiveness": 45,
            "spin_effectiveness": 55,
            "bounce": 55,
            "turn": 40,
            "wicket_probability": 0.02  # Lower wicket chance
        })
    
    # Day 4 (Starting to wear)
    elif day == 4:
        conditions.update({
            "description": "Pitch wearing, cracks appearing, spin starting to grip",
            "pace_effectiveness": 40,
            "spin_effectiveness": 75,
            "bounce": 60,
            "turn": 70,
            "wicket_probability": 0.045
        })
    
    # Day 5 (Maximum wear and tear)
    elif day == 5:
        conditions.update({
            "description": "Worn pitch, wide cracks, sharp turn, variable bounce",
            "pace_effectiveness": 35,
            "spin_effectiveness": 90,
            "bounce": 45,  # Lower, variable
            "turn": 90,
            "wicket_probability": 0.06  # High wicket chance
        })
    
    return conditions


def get_outcome_probabilities(pitch_condition, bowler_type, batsman_skill, batsman_aggression):
    """
    Calculate ball outcome probabilities based on conditions
    
    Returns weights for: [Dot, 1, 2, 3, 4, 6, Wicket]
    """
    
    # Base probabilities
    weights = [35, 30, 15, 8, 7, 2, 3]  # [Dot, 1, 2, 3, 4, 6, W]
    
    # Adjust for bowler type vs pitch
    if bowler_type == "Fast":
        effectiveness = pitch_condition["pace_effectiveness"]
    else:  # Spinner
        effectiveness = pitch_condition["spin_effectiveness"]
    
    # Higher effectiveness = more dot balls and wickets
    effectiveness_factor = effectiveness / 50  # Normalize to 1.0
    
    weights[0] = int(35 * effectiveness_factor)  # Dot balls
    weights[6] = int(3 * effectiveness_factor)   # Wickets
    
    # Adjust for batsman skill (higher skill = more runs, fewer wickets)
    skill_factor = batsman_skill / 80  # Normalize
    
    weights[1] = int(30 * skill_factor)  # Singles
    weights[4] = int(7 * skill_factor)   # Fours
    weights[6] = int(weights[6] / skill_factor)  # Fewer wickets for skilled batsmen
    
    # Adjust for aggression (higher aggression = more boundaries, more risk)
    aggression_factor = batsman_aggression / 70  # Normalize
    
    weights[4] = int(weights[4] * aggression_factor)  # More fours
    weights[5] = int(2 * aggression_factor * aggression_factor)  # More sixes
    weights[6] = int(weights[6] * aggression_factor)  # More risk = more wickets
    
    # Ensure all weights are positive
    weights = [max(1, w) for w in weights]
    
    return weights


def get_dismissal_type(pitch_condition, bowler_type):
    """
    Return dismissal type based on pitch and bowling
    """
    
    if bowler_type == "Fast":
        if pitch_condition["pace_effectiveness"] > 70:
            # Pace-friendly: more edges and LBWs
            dismissals = ["Caught behind", "Caught in slips", "LBW", "Bowled", "Caught"]
            weights = [30, 25, 25, 15, 5]
        else:
            dismissals = ["Caught", "Bowled", "LBW", "Caught behind"]
            weights = [40, 25, 20, 15]
    else:  # Spinner
        if pitch_condition["spin_effectiveness"] > 70:
            # Spin-friendly: more bowled, LBW, stumped
            dismissals = ["Bowled", "LBW", "Caught", "Stumped", "Caught and bowled"]
            weights = [35, 30, 20, 10, 5]
        else:
            dismissals = ["Caught", "Bowled", "LBW", "Stumped"]
            weights = [45, 25, 20, 10]
    
    import random
    return random.choices(dismissals, weights=weights, k=1)[0]


def get_shot_type(runs, wicket):
    """
    Return shot type based on outcome
    """
    import random
    
    if wicket:
        shots = [
            "Defensive prod, edged",
            "Attempted drive, beaten",
            "Playing across the line",
            "Missed straight delivery",
            "Outside edge",
            "Inside edge"
        ]
        return random.choice(shots)
    
    if runs == 0:
        shots = [
            "Forward defense",
            "Back foot defense",
            "Left alone outside off",
            "Defensive push",
            "Blocked back to bowler",
            "Watchful leave"
        ]
    elif runs == 1:
        shots = [
            "Pushed to mid-on",
            "Tucked to leg side",
            "Nudged to point",
            "Worked to square leg",
            "Guided to third man"
        ]
    elif runs == 2:
        shots = [
            "Clipped through mid-wicket",
            "Pushed past cover",
            "Worked behind square",
            "Driven to deep"
        ]
    elif runs == 3:
        shots = [
            "Driven past mid-off",
            "Flicked through mid-wicket",
            "Cut past point"
        ]
    elif runs == 4:
        shots = [
            "Cover drive",
            "Straight drive",
            "Pull shot",
            "Cut shot",
            "On-drive",
            "Square drive",
            "Flick through mid-wicket"
        ]
    elif runs == 6:
        shots = [
            "Lofted over long-on",
            "Pulled over mid-wicket",
            "Slog sweep",
            "Straight six",
            "Hook shot"
        ]
    else:
        shots = ["Miscued shot"]
    
    return random.choice(shots)