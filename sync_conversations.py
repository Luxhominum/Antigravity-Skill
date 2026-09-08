"""
Antigravity Cross-Device Conversation Sync Engine
Author: Luxhominum
Repository: https://github.com/Luxhominum/Antigravity-Skill
"""

import os
import sys
import glob
import zipfile
import shutil
import json
import ssl
import urllib.request
import subprocess
import argparse

CHUNK_SIZE = 25 * 1024 * 1024  # 25 MB max per chunk for GitHub compatibility

def get_paths():
    user_home = os.path.expanduser("~")
    gemini_dir = os.path.join(user_home, ".gemini")
    antigravity_dir = os.path.join(gemini_dir, "antigravity")
    config_dir = os.path.join(gemini_dir, "config")
    
    return {
        "gemini": gemini_dir,
        "antigravity": antigravity_dir,
        "config": config_dir,
        "conversations": os.path.join(antigravity_dir, "conversations"),
        "brain": os.path.join(antigravity_dir, "brain"),
        "summaries": os.path.join(antigravity_dir, "agyhub_summaries_proto.pb"),
        "config_projects": os.path.join(config_dir, "projects"),
        "archives": os.path.join(config_dir, "conversation_archives"),
    }

def backup(auto_git=True):
    paths = get_paths()
    os.makedirs(paths["archives"], exist_ok=True)
    temp_zip = os.path.join(paths["archives"], "temp_bundle.zip")
    
    print("=" * 60)
    print(" [1/3] PACKING ANTIGRAVITY CONVERSATIONS & ARTIFACTS...")
    print("=" * 60)
    
    with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # 1. Summaries protobuf
        if os.path.exists(paths["summaries"]):
            print("  + Adding agyhub_summaries_proto.pb")
            zf.write(paths["summaries"], "agyhub_summaries_proto.pb")
            
        # 2. Projects JSON definitions
        if os.path.exists(paths["config_projects"]):
            for f in os.listdir(paths["config_projects"]):
                if f.endswith(".json"):
                    zf.write(os.path.join(paths["config_projects"], f), os.path.join("projects", f))
            print(f"  + Added project configs from {paths['config_projects']}")
                    
        # 3. Conversation SQLite databases
        if os.path.exists(paths["conversations"]):
            count = 0
            for f in os.listdir(paths["conversations"]):
                if f.endswith(".db"):
                    zf.write(os.path.join(paths["conversations"], f), os.path.join("conversations", f))
                    count += 1
            print(f"  + Added {count} conversation database(s)")
                    
        # 4. Brain transcripts, planning docs, artifacts
        if os.path.exists(paths["brain"]):
            b_count = 0
            for root, _, files in os.walk(paths["brain"]):
                for f in files:
                    if f.endswith(".log") and "tasks" in root:
                        continue  # Skip large ephemeral task logs
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, paths["brain"])
                    zf.write(full_p, os.path.join("brain", rel_p))
                    b_count += 1
            print(f"  + Added {b_count} brain artifact/transcript file(s)")

    total_sz = os.path.getsize(temp_zip)
    print(f"\n[2/3] Total compressed bundle: {total_sz / (1024*1024):.2f} MB")
    print("  Splitting into GitHub-safe 25MB chunks...")
    
    # Remove existing chunk files
    for old_chunk in glob.glob(os.path.join(paths["archives"], "convo_chunk_*.dat")):
        try: os.remove(old_chunk)
        except: pass
        
    part_idx = 0
    with open(temp_zip, "rb") as f_in:
        while True:
            chunk = f_in.read(CHUNK_SIZE)
            if not chunk:
                break
            chunk_file = os.path.join(paths["archives"], f"convo_chunk_{part_idx:03d}.dat")
            with open(chunk_file, "wb") as f_out:
                f_out.write(chunk)
            print(f"    - Chunk {part_idx:03d}: {len(chunk) / (1024*1024):.2f} MB")
            part_idx += 1
            
    try: os.remove(temp_zip)
    except: pass
    
    print(f"\n[3/3] Successfully created {part_idx} archive chunk(s) in {paths['archives']}")
    
    if auto_git:
        print("\n" + "=" * 60)
        print(" COMMITTING AND PUSHING TO GITHUB...")
        print("=" * 60)
        try:
            cwd = paths["config"]
            subprocess.run(["git", "add", "conversation_archives", "sync_conversations.py", "*.bat", "README_SYNC.md"], cwd=cwd, check=True)
            subprocess.run(["git", "commit", "-m", "chore: sync antigravity conversations and artifacts"], cwd=cwd)
            subprocess.run(["git", "push", "origin", "main"], cwd=cwd, check=True)
            print("\n [SUCCESS] Conversations pushed to https://github.com/Luxhominum/Antigravity-Skill!")
        except subprocess.CalledProcessError as e:
            print(f"\n [NOTE] Git push completed or no changes: {e}")

def restore(notify_ls=True):
    paths = get_paths()
    chunks = sorted(glob.glob(os.path.join(paths["archives"], "convo_chunk_*.dat")))
    if not chunks:
        print(f"Error: No conversation chunks found in {paths['archives']}")
        return
        
    print("=" * 60)
    print(" [1/3] REASSEMBLING CONVERSATION BUNDLE...")
    print("=" * 60)
    
    temp_zip = os.path.join(paths["archives"], "temp_restore.zip")
    with open(temp_zip, "wb") as f_out:
        for ch in chunks:
            print(f"  + Reading {os.path.basename(ch)}")
            with open(ch, "rb") as f_in:
                f_out.write(f_in.read())
                
    print("\n [2/3] EXTRACTING TO ANTIGRAVITY DIRECTORIES...")
    os.makedirs(paths["conversations"], exist_ok=True)
    os.makedirs(paths["brain"], exist_ok=True)
    os.makedirs(paths["config_projects"], exist_ok=True)
    
    with zipfile.ZipFile(temp_zip, "r") as zf:
        for member in zf.infolist():
            target_path = None
            if member.filename == "agyhub_summaries_proto.pb":
                target_path = paths["summaries"]
            elif member.filename.startswith("projects/"):
                rel = member.filename[len("projects/"):]
                if rel: target_path = os.path.join(paths["config_projects"], rel)
            elif member.filename.startswith("conversations/"):
                rel = member.filename[len("conversations/"):]
                if rel: target_path = os.path.join(paths["conversations"], rel)
            elif member.filename.startswith("brain/"):
                rel = member.filename[len("brain/"):]
                if rel: target_path = os.path.join(paths["brain"], rel)
                
            if target_path:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with zf.open(member) as src, open(target_path, "wb") as dst:
                    dst.write(src.read())
                    
    try: os.remove(temp_zip)
    except: pass
    print("  Extraction complete!")
    
    if notify_ls:
        print("\n [3/3] NOTIFYING ANTIGRAVITY LANGUAGE SERVER...")
        # Check if language server is running and load trajectories
        try:
            reload_language_server(paths["conversations"])
        except Exception as e:
            print(f"  Note: Language server reload skipped ({e})")
            
    print("\n" + "=" * 60)
    print(" [SUCCESS] All conversations restored on this laptop!")
    print("=" * 60)

def reload_language_server(conv_dir):
    # Try finding language_server process and CSRF token
    try:
        import psutil
    except ImportError:
        psutil = None

    # Connect to localhost language server if running
    ports = [64790, 64789, 64791, 64792]
    # Look for CSRF token from command line or default
    csrf = None
    if sys.platform == "win32":
        try:
            out = subprocess.check_output('powershell -Command "(Get-CimInstance Win32_Process -Filter \\"Name=\'language_server.exe\'\\").CommandLine"', shell=True).decode()
            if "--csrf_token" in out:
                csrf = out.split("--csrf_token")[1].strip().split()[0]
        except Exception:
            pass

    if not csrf:
        print("  Language Server will index all conversations on next launch.")
        return

    ctx = ssl._create_unverified_context()
    dbs = glob.glob(os.path.join(conv_dir, "*.db"))
    loaded = 0
    for db in dbs:
        cid = os.path.basename(db).replace('.db', '')
        for port in ports:
            url = f"https://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetCascadeTrajectory"
            body = json.dumps({"cascadeId": cid}).encode('utf-8')
            req = urllib.request.Request(url, data=body, headers={
                "Content-Type": "application/json",
                "X-Codeium-Csrf-Token": csrf,
                "Connect-Protocol-Version": "1"
            })
            try:
                with urllib.request.urlopen(req, context=ctx, timeout=2) as resp:
                    if resp.status == 200:
                        loaded += 1
                        break
            except Exception:
                pass
    print(f"  Reloaded {loaded} conversation(s) directly into live Antigravity window.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity Cross-Device Conversation Sync")
    parser.add_argument("action", choices=["backup", "restore", "push", "pull"], help="Action to perform")
    parser.add_argument("--no-git", action="store_true", help="Skip git push")
    args = parser.parse_args()
    
    if args.action in ["backup", "push"]:
        backup(auto_git=not args.no_git)
    elif args.action in ["restore", "pull"]:
        restore()
