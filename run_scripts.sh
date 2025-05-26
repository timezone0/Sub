#!/bin/bash

python scripts/xf.py
python -u gen_configs.py --json "sub-timer.json"
python -u gen_configs.py --json "sub.json"