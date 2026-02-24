#!/usr/bin/env python3
"""Wacht - Live Reload Server

Entry point for running wacht directly without installation.
Usage: python3 wacht.py [OPTIONS]
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from wacht import main

if __name__ == "__main__":
    main()
