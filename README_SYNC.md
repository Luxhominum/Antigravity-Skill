# Antigravity Cross-Device Sync Guide

Sync your Antigravity skills, rules, configurations, and full conversation history across multiple laptops.

## How It Works

1. **Configurations & Skills**: Synced directly via this Git repository (`~/.gemini/config`).
2. **Conversations & Artifacts**: Packaged into compressed 25MB chunks in `conversation_archives/` (GitHub-safe, avoiding GitHub's 100MB limit).

---

## 1. On Your Current Laptop (To Save & Push):
Run the backup script whenever you want to upload your latest conversations:
* **Option A**: Double-click `backup_conversations.bat`
* **Option B**: Run via terminal:
  ```bash
  cd ~/.gemini/config
  python sync_conversations.py backup
  ```

---

## 2. On Any Other Laptop (To Retrieve All Conversations):

### First Time Setup:
1. Clone this repository to `~/.gemini/config`:
   ```bash
   git clone https://github.com/Luxhominum/Antigravity-Skill.git ~/.gemini/config
   ```
2. Run the restore script:
   * **Option A**: Double-click `restore_conversations.bat`
   * **Option B**: Run via terminal:
     ```bash
     cd ~/.gemini/config
     git pull origin main
     python sync_conversations.py restore
     ```

3. Open or refresh Antigravity Desktop—all conversations, projects, artifacts, and sidebar trees will be instantly loaded and ready!
