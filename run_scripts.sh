#!/bin/bash

python scripts/xf.py
python -u app-command.py --json "sub-timer.json"
python -u app-command.py --json "sub.json"