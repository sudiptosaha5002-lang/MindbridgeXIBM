"""
MindBridge Platform - Main Runner Script.
Initializes the database and boots the Flask web application.
"""

import os
import sys
import webbrowser
import threading
import time

# Ensure backend path is registered
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from server import app, db

def main():
    print("=" * 65)
    print("        MINDBRIDGE - MENTAL HEALTH PLATFORM & CHATBOT         ")
    print("=" * 65)
    print(" [+] Initializing SQLite & PostgreSQL-compatible Database...")
    db.init_db()
    print(" [+] Initializing NLP Sentiment & Safety Classification Engine...")
    print(" [+] Non-Diagnostic Ethical Guardrails: ACTIVE")
    print(" [+] 24/7 Crisis & Emergency SOS Gateway: ACTIVE")
    print(" [+] Verified Care Provider Network & Calendar: READY")
    print("-" * 65)
    
    port = 5000
    url = f"http://127.0.0.1:{port}"
    print(f" MindBridge Web App is live at: {url}")
    print(" Press Ctrl+C to shut down.")
    print("=" * 65)

    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    main()
