#!/bin/bash

python -u app-command.py --json "sub-timer.json"
python -u app-command.py --json "sub.json"

python -u app-command.py --json "sub-timer.json" --mihomo-dir mihomo-linux --mihomo-config scripts/mihomo-config/config-linux.yaml --singbox-dir singbox-linux --singbox-config scripts/singbox-config/config-linux.json
python -u app-command.py --json "sub.json" --mihomo-dir mihomo-linux --mihomo-config scripts/mihomo-config/config-linux.yaml --singbox-dir singbox-linux --singbox-config scripts/singbox-config/config-linux.json