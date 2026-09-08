@echo off
cd /d "%~dp0"
echo ===================================================
echo   Backing up Antigravity Conversations to GitHub
echo ===================================================
python sync_conversations.py backup
pause
