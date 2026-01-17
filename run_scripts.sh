#!/bin/bash

#Android
python -u app-command.py --json "sub-timer.json" --mihomo-dir mihomo --mihomo-config scripts/mihomo-config/config-android.yaml --singbox-dir singbox --singbox-config scripts/singbox-config/config-android.json
python -u app-command.py --json "sub.json" --mihomo-dir mihomo --mihomo-config scripts/mihomo-config/config-android-open.yaml --singbox-dir singbox --singbox-config scripts/singbox-config/config-android-open.json

#linux
python -u app-command.py --json "sub-timer.json" --mihomo-dir mihomo-linux --mihomo-config scripts/mihomo-config/config-linux.yaml --singbox-dir singbox-linux --singbox-config scripts/singbox-config/config-linux.json
python -u app-command.py --json "sub.json" --mihomo-dir mihomo-linux --mihomo-config scripts/mihomo-config/config-linux-open.yaml --singbox-dir singbox-linux --singbox-config scripts/singbox-config/config-linux-open.json

#windows
python -u app-command.py --json "sub-timer.json" --mihomo-dir mihomo-windows --mihomo-config scripts/mihomo-config/config-windows.yaml --singbox-dir singbox-windows --singbox-config scripts/singbox-config/config-windows.json
python -u app-command.py --json "sub.json" --mihomo-dir mihomo-windows --mihomo-config scripts/mihomo-config/config-windows-open.yaml --singbox-dir singbox-windows --singbox-config scripts/singbox-config/config-windows-open.json