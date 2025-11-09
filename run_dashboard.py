#!/usr/bin/env python3
"""
Start Streamlit Dashboard
"""

import subprocess
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    print("🏏 Starting Cricket Dashboard...")
    print("Dashboard will open in your browser automatically")
    print("Press Ctrl+C to stop\n")
    
    try:
        subprocess.run([
            "streamlit", "run",
            "src/dashboard/cricket_dashboard.py",
            "--server.headless=true"
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure Streamlit is installed:")
        print("pip install streamlit plotly altair")


if __name__ == "__main__":
    main()