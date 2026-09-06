import os
import paramiko

HOST = "fi12.bot-hosting.cloud"
PORT = 2022
USER = "fe7daebb-5d31-4a25-ade7-9cd591139e8f.rtepbovn"
PASS = "poh6yQM4oMjSLzcpzgxOq1gg"

def deploy():
    print(f"Connecting to {HOST}:{PORT}...", flush=True)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    print("Connected!", flush=True)
    
    sftp = client.open_sftp()
    print("Remote directory before update:", sftp.listdir('.'), flush=True)

    items_to_upload = [
        "main.py",
        "security_bot.py",
        "run_24_7.py",
        "requirements.txt",
        "TERMS_OF_SERVICE.md",
        "PRIVACY_POLICY.md"
    ]
    
    for item in items_to_upload:
        if os.path.exists(item):
            print(f"Uploading {item}...", flush=True)
            sftp.put(item, item)
            print(f"Uploaded {item} successfully.", flush=True)

    # Upload cogs folder
    if os.path.exists("cogs"):
        try:
            sftp.mkdir("cogs")
        except Exception:
            pass
        for f in os.listdir("cogs"):
            if f.endswith(".py"):
                local_path = os.path.join("cogs", f)
                remote_path = f"cogs/{f}"
                print(f"Uploading {local_path} -> {remote_path}...", flush=True)
                sftp.put(local_path, remote_path)
                print(f"Uploaded {remote_path} successfully.", flush=True)

    # Upload utils folder if exists
    if os.path.exists("utils"):
        try:
            sftp.mkdir("utils")
        except Exception:
            pass
        for f in os.listdir("utils"):
            if f.endswith(".py"):
                local_path = os.path.join("utils", f)
                remote_path = f"utils/{f}"
                print(f"Uploading {local_path} -> {remote_path}...", flush=True)
                sftp.put(local_path, remote_path)
                print(f"Uploaded {remote_path} successfully.", flush=True)

    print("\nVerifying uploaded files on server...", flush=True)
    cogs_files = sftp.listdir('cogs')
    print("Remote cogs:", cogs_files, flush=True)

    sftp.close()
    client.close()
    print("\n🚀 ALL BOT UPDATES DEPLOYED TO 24/7 SERVER SUCCESSFULLY!", flush=True)

if __name__ == "__main__":
    deploy()
