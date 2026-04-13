#!/usr/bin/env python3
"""
Guided Login — Tarayıcı Aç, Giriş Yap, Cookie Kaydet

Kullanım:
    python scrapers/login_session.py           # Twitter + Instagram
    python scrapers/login_session.py --twitter  # Sadece Twitter
    python scrapers/login_session.py --instagram # Sadece Instagram

Nasıl çalışır:
    1. Script tarayıcıyı açar
    2. İlgili siteye gider
    3. Sen giriş yaparsın
    4. Enter'a basarsın
    5. Cookies kaydedilir — bir daha sormaz
"""

import os, sys, json, time, subprocess, argparse, logging, urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("LoginSession")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

X_SESSION  = os.path.join(PROJECT_ROOT, "x_session.json")
IG_SESSION = os.path.join(PROJECT_ROOT, "ig_session.json")

# Tarayıcı öncelik sırası (CDP destekli Chromium tabanlı)
BROWSERS = [
    ("Microsoft Edge",  r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ("Microsoft Edge",  r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    ("Brave",           r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ("Google Chrome",   r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    ("Google Chrome",   r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
]

CDP_PORT    = 9229           # Scraper portlarından (9222, 9223-9226) farklı
USER_DATA   = r"C:\tmp\sam-login-session"   # Ayrı profil — normal tarayıcıyla karışmaz


def find_browser() -> tuple:
    for name, path in BROWSERS:
        if os.path.isfile(path):
            return name, path
    return None, None


def start_browser(exe: str) -> subprocess.Popen:
    """CDP modunda yeni bir tarayıcı penceresi başlat."""
    os.makedirs(USER_DATA, exist_ok=True)
    cmd = [
        exe,
        f"--remote-debugging-port={CDP_PORT}",
        "--remote-allow-origins=*",
        f"--user-data-dir={USER_DATA}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-sync",        # Hesap sync istemez
        "--disable-extensions",  # Temiz başlangıç
    ]
    log.info(f"Tarayici baslatiliyor: {exe}")
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_for_cdp(timeout: int = 20) -> bool:
    """CDP'nin hazır olmasını bekle."""
    url = f"http://127.0.0.1:{CDP_PORT}/json/version"
    for i in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(1)
    return False


def get_cdp_websocket_url() -> str:
    """Aktif sekmenin WebSocket URL'sini al."""
    import urllib.request
    resp = urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json", timeout=5)
    tabs = json.loads(resp.read())
    for tab in tabs:
        if tab.get("type") == "page":
            return tab["webSocketDebuggerUrl"]
    raise RuntimeError("Aktif sekme bulunamadı")


def cdp_send(ws, method: str, params: dict = None, msg_id: int = 1) -> dict:
    """CDP komutu gönder ve yanıt al."""
    import websocket as ws_lib
    msg = json.dumps({"id": msg_id, "method": method, "params": params or {}})
    ws.send(msg)
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == msg_id:
            return data.get("result", {})


def navigate_and_wait(ws_url: str, url: str) -> None:
    """Sayfaya git."""
    import websocket as ws_lib
    ws = ws_lib.create_connection(ws_url, timeout=10)
    try:
        cdp_send(ws, "Page.navigate", {"url": url}, msg_id=1)
    finally:
        ws.close()


def capture_cookies(ws_url: str, domain_filter: str) -> list:
    """CDP üzerinden cookie'leri al."""
    import websocket as ws_lib
    ws = ws_lib.create_connection(ws_url, timeout=10)
    try:
        result = cdp_send(ws, "Network.getAllCookies", {}, msg_id=2)
        all_cookies = result.get("cookies", [])
        # Domain filtrele
        filtered = []
        seen = set()
        for c in all_cookies:
            d = c.get("domain", "").lstrip(".")
            target = domain_filter.lstrip(".")
            if d == target or d.endswith("." + target):
                key = (c["name"], c.get("domain",""))
                if key not in seen:
                    seen.add(key)
                    filtered.append({
                        "name":     c["name"],
                        "value":    c["value"],
                        "domain":   c["domain"],
                        "path":     c.get("path", "/"),
                        "expires":  c.get("expires", 0),
                        "secure":   c.get("secure", False),
                        "httpOnly": c.get("httpOnly", False),
                        "sameSite": c.get("sameSite", "Lax"),
                    })
        return filtered
    finally:
        ws.close()


def do_platform(browser_proc: subprocess.Popen, platform: str) -> bool:
    """Tek platform için login + cookie kaydet."""
    if platform == "twitter":
        url      = "https://x.com/login"
        domain   = "x.com"
        out_file = X_SESSION
        site     = "X/Twitter"
        critical = {"auth_token", "ct0"}
    else:
        url      = "https://www.instagram.com/accounts/login/"
        domain   = "instagram.com"
        out_file = IG_SESSION
        site     = "Instagram"
        critical = {"sessionid", "csrftoken"}

    print(f"\n{'='*55}")
    print(f"  {site} Girisi")
    print(f"{'='*55}")

    try:
        ws_url = get_cdp_websocket_url()
    except Exception as e:
        log.error(f"CDP baglantisi kurulamadi: {e}")
        return False

    # Siteye git
    try:
        navigate_and_wait(ws_url, url)
    except Exception as e:
        log.warning(f"Navigasyon hatasi: {e}")

    print(f"""
  Tarayici penceresi acildi.

  1. {site}'a giris yap (kullanici adi + sifre)
  2. Giris tamamlaninca asagiya don
  3. Enter'a bas
""")
    input("  [ENTER] Giris yapildiktan sonra bu terminale gel ve Enter'a bas...")

    # Cookie yakala
    try:
        ws_url = get_cdp_websocket_url()  # sekme degismis olabilir
        cookies = capture_cookies(ws_url, domain)
    except Exception as e:
        log.error(f"Cookie yakalanamadi: {e}")
        return False

    if not cookies:
        print(f"  [HATA] {site} cookie'si bulunamadi. Gercekten giris yapildi mi?")
        return False

    names   = {c["name"] for c in cookies}
    missing = critical - names
    if missing:
        print(f"  [UYARI] Kritik cookie eksik: {missing}")
        print(f"  Girisin tamamlandigini dogrulayin (ana sayfa goruntulenmeli)")
        # Kullaniciya ek sure ver
        input("  Giriş tamamsa tekrar Enter, yoksa Ctrl+C ile iptal et...")
        ws_url = get_cdp_websocket_url()
        cookies = capture_cookies(ws_url, domain)
        names = {c["name"] for c in cookies}
        missing = critical - names

    # Kaydet
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)

    status = "HAZIR" if not missing else "EKSIK COOKIE"
    print(f"\n  Durum  : {status}")
    print(f"  Cookie : {len(cookies)} adet")
    print(f"  Kritik : {names & critical}")
    print(f"  Kayit  : {out_file}")
    return not missing


def verify_sessions():
    print(f"\n{'='*55}")
    print("  FINAL SESSION DURUMU")
    print(f"{'='*55}")
    for label, path, critical in [
        ("Twitter/X",  X_SESSION,  {"auth_token", "ct0"}),
        ("Instagram",  IG_SESSION, {"sessionid", "csrftoken"}),
    ]:
        if not os.path.isfile(path):
            print(f"  {label}: DOSYA YOK")
            continue
        with open(path, encoding="utf-8") as f:
            cookies = json.load(f)
        names  = {c["name"] for c in cookies}
        ok     = critical.issubset(names)
        status = "HAZIR" if ok else "EKSIK"
        print(f"  {label}: {status} | {len(cookies)} cookie")
        if not ok:
            print(f"    Eksik: {critical - names}")


def main():
    parser = argparse.ArgumentParser(description="Guided browser login + cookie capture")
    parser.add_argument("--twitter",   action="store_true")
    parser.add_argument("--instagram", action="store_true")
    args = parser.parse_args()

    do_twitter   = args.twitter   or (not args.twitter and not args.instagram)
    do_instagram = args.instagram or (not args.twitter and not args.instagram)

    # Tarayıcı bul
    browser_name, browser_exe = find_browser()
    if not browser_exe:
        print("[HATA] Desteklenen tarayici bulunamadi (Edge/Brave/Chrome).")
        sys.exit(1)

    print(f"\nKullanilacak tarayici: {browser_name}")
    print(f"CDP port: {CDP_PORT}")
    print(f"Profil: {USER_DATA}  (normal tarayicinizdan bagimsiz)\n")

    # Tarayıcı başlat
    proc = start_browser(browser_exe)
    print("Tarayici baslatiliyor", end="", flush=True)
    if not wait_for_cdp(timeout=20):
        print("\n[HATA] Tarayici 20s icinde hazir olmadi.")
        proc.terminate()
        sys.exit(1)
    print(" — HAZIR")

    results = {}
    try:
        if do_twitter:
            results["twitter"] = do_platform(proc, "twitter")
        if do_instagram:
            results["instagram"] = do_platform(proc, "instagram")
    finally:
        proc.terminate()
        print("\nTarayici kapatildi.")

    verify_sessions()

    failed = [p for p, ok in results.items() if not ok]
    if not failed:
        print("\n  Session'lar kaydedildi. Artik scraper'lari calistirabilirsinin.")
    else:
        print(f"\n  Eksik: {failed} — tekrar dene.")
        sys.exit(1)


if __name__ == "__main__":
    main()
