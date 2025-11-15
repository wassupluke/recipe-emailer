#!/bin/bash

cd /home/wassu/code/recipe-emailer
source .venv/bin/activate
python3 cook.py >> cronjob.log
deactivate
