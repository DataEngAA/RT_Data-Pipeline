"""
Main entry point to start cricket match simulation
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent / "src"))

from cricket.match_simulator import main

if __name__ == "__main__":
    main()