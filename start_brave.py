import subprocess

brave = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

subprocess.Popen([brave, "--remote-debugging-port=9222", "--remote-allow-origins=*", "--user-data-dir=C:\\tmp\\chrome-tw"])
print("Twitter Brave baslatildi (port 9222)")

subprocess.Popen([brave, "--remote-debugging-port=9226", "--remote-allow-origins=*", "--user-data-dir=C:\\tmp\\chrome-ig"])
print("Instagram Brave baslatildi (port 9226)")
