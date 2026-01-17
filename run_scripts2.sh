#!/bin/bash

python generate-preferred-nodes/config/convert.py -c mihomo/tc.yaml -o generate-preferred-nodes/config/config.csv

python generate-preferred-nodes/app.py generate-preferred-nodes/config/config.csv generate-preferred-nodes/config/config.txt generate-preferred-nodes/config/output.txt