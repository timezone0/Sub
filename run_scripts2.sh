#!/bin/bash

python generate-preferred-nodes/config/convert.py -c mihomo/tc.yaml -o generate-preferred-nodes/config/config.csv

python generate-preferred-nodes/app.py --csv generate-preferred-nodes/config/config.csv --txt generate-preferred-nodes/config/config.txt --output generate-preferred-nodes/config/output.txt