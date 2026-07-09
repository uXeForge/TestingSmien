@echo off
set SMENY_USERNAME=zakovakika@gmail.com
set SMENY_PASSWORD=DHLD181818
set TELEGRAM_BOT_TOKEN=8765779374:AAHst-JuNkJdE0mrr2WFZOT9z1JW6Z9KPCw
set TELEGRAM_CHAT_ID=8933335367
set DEBUG=true
set TEST_SEND=true

echo Spúšťam testovací monitor smien (so simuláciou voľnej smeny)...
python monitor.py
pause
