"""
MindBridge Platform - Root Runner Script
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(BASE_DIR, "MINDBRIDGE")
if os.path.exists(PROJECT_DIR):
    sys.path.insert(0, PROJECT_DIR)
    os.chdir(PROJECT_DIR)
    import run
    run.main()
else:
    import run
    run.main()
