#!/bin/bash

cd /home/wassu/code/recipe-emailer
source .venv/bin/activate
python3 main.py >> cronjob.log
deactivate
