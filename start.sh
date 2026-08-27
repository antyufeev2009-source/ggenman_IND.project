#!/bin/bash
python /app/OSN_HR/main.py &
python /app/bot_admin/main.py &
wait -n
