#!/bin/bash

python generate-preferred-nodes/config/convert.py -c mihomo/tc.yaml -o generate-preferred-nodes/config/config.csv

python generate-preferred-nodes/app.py --csv generate-preferred-nodes/config/config.csv --txt generate-preferred-nodes/config/config.txt --output generate-preferred-nodes/config/output.txt

#Android
python -u app-command.py --json "sub-1.json" --mihomo-dir mihomo --mihomo-config scripts/mihomo-config/config-android.yaml --singbox-dir singbox --singbox-config scripts/singbox-config/config-android.json
python -u app-command.py --json "sub-2.json" --mihomo-dir mihomo --mihomo-config scripts/mihomo-config/config-android-open.yaml --singbox-dir singbox --singbox-config scripts/singbox-config/config-android-open.json

#linux
python -u app-command.py --json "sub-1.json" --mihomo-dir mihomo-linux --mihomo-config scripts/mihomo-config/config-linux.yaml --singbox-dir singbox-linux --singbox-config scripts/singbox-config/config-linux.json
python -u app-command.py --json "sub-2.json" --mihomo-dir mihomo-linux --mihomo-config scripts/mihomo-config/config-linux-open.yaml --singbox-dir singbox-linux --singbox-config scripts/singbox-config/config-linux-open.json

#windows
python -u app-command.py --json "sub-1.json" --mihomo-dir mihomo-windows --mihomo-config scripts/mihomo-config/config-windows.yaml --singbox-dir singbox-windows --singbox-config scripts/singbox-config/config-windows.json
python -u app-command.py --json "sub-2.json" --mihomo-dir mihomo-windows --mihomo-config scripts/mihomo-config/config-windows-open.yaml --singbox-dir singbox-windows --singbox-config scripts/singbox-config/config-windows-open.json

#timer
python -u app-command.py --name "timer" --url "mihomo/8eb.yaml" --mihomo-dir mihomo --mihomo-config scripts/mihomo-config/config-android.yaml --singbox-dir singbox --singbox-config scripts/singbox-config/config-android.json
python -u app-command.py --name "timer" --url "mihomo/8eb.yaml" --mihomo-dir mihomo-linux --mihomo-config scripts/mihomo-config/config-linux.yaml --singbox-dir singbox-linux --singbox-config scripts/singbox-config/config-linux.json
python -u app-command.py --name "timer" --url "mihomo/8eb.yaml" --mihomo-dir mihomo-windows --mihomo-config scripts/mihomo-config/config-windows.yaml --singbox-dir singbox-windows --singbox-config scripts/singbox-config/config-windows.json

#open
python -u app-command.py --name "timer" --url "mihomo/8eb.yaml" --mihomo-dir open --mihomo-config scripts/mihomo-config/config-android-open.yaml --singbox-dir open --singbox-config scripts/singbox-config/config-android-open.json
python -u app-command.py --name "timer-linux" --url "mihomo/8eb.yaml" --mihomo-dir open --mihomo-config scripts/mihomo-config/config-linux-open.yaml --singbox-dir open --singbox-config scripts/singbox-config/config-linux-open.json
python -u app-command.py --name "timer-windows" --url "mihomo/8eb.yaml" --mihomo-dir open --mihomo-config scripts/mihomo-config/config-windows-open.yaml --singbox-dir open --singbox-config scripts/singbox-config/config-windows-open.json