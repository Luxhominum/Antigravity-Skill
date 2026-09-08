@echo off
cd /d "%~dp0"
echo ===================================================
echo   Pulling & Restoring Conversations from GitHub
echo ===================================================
git pull origin main
python sync_conversations.py restore
pause
