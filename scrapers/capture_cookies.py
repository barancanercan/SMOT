#!/usr/bin/env python3
"""
Cookie Yakalama — Tarayıcıdan Direkt veya Extension ile

İki mod:

1. OTOMATİK (Tarayıcı KAPALI iken):
   Brave/Chrome/Edge/Firefox cookie veritabanını okur.
   >> python scrapers/capture_cookies.py

2. MANUEL (Extension ile — Tarayıcı açıkken):
   Brave'de "Cookie-Editor" extension'ı kur (https://cookie-editor.com)
   x.com'a git → extension → Export → Export All (JSON)  → twitter_cookies.json kaydet
   instagram.com'a git → extension → Export → Export All (JSON) → ig_cookies.json kaydet
   >> python scrapers/capture_cookies.py --import-twitter twitter_cookies.json --import-instagram ig_cookies.json
"""

import json, os, sys, shutil, sqlite3, base64, struct, argparse, logging, tempfile
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("CookieCapture")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X_SESSION    = os.path.join(PROJECT_ROOT, "x_session.json")
IG_SESSION   = os.path.join(PROJECT_ROOT, "ig_session.json")

TWITTER_DOMAINS   = {".x.com", "x.com", ".twitter.com", "twitter.com"}
INSTAGRAM_DOMAINS = {".instagram.com", "instagram.com"}

CHROMIUM_PROFILES = [
    ("Brave",  Path(os.environ.get("LOCALAPPDATA","")) / "BraveSoftware/Brave-Browser/User Data"),
    ("Chrome", Path(os.environ.get("LOCALAPPDATA","")) / "Google/Chrome/User Data"),
    ("Edge",   Path(os.environ.get("LOCALAPPDATA","")) / "Microsoft/Edge/User Data"),
]


# ──────────────────────────────────────────────────────────
# DPAPI + AES-GCM çözücü
# ──────────────────────────────────────────────────────────

def _dpapi_decrypt(ciphertext: bytes) -> bytes:
    import ctypes, ctypes.wintypes
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", ctypes.wintypes.DWORD),
                    ("pbData", ctypes.POINTER(ctypes.c_char))]
    p = ctypes.create_string_buffer(ciphertext, len(ciphertext))
    blobin, blobout = DATA_BLOB(ctypes.sizeof(p), p), DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(blobin), None, None, None, None, 0, ctypes.byref(blobout)
    ):
        raise RuntimeError("DPAPI çözme başarısız")
    result = ctypes.string_at(blobout.pbData, blobout.cbData)
    ctypes.windll.kernel32.LocalFree(blobout.pbData)
    return result


def _get_encryption_key(user_data_dir: Path) -> bytes:
    local_state = user_data_dir / "Local State"
    with open(local_state, encoding="utf-8") as f:
        state = json.load(f)
    enc_key = base64.b64decode(state["os_crypt"]["encrypted_key"])
    return _dpapi_decrypt(enc_key[5:])  # ilk 5 = b"DPAPI"


def _aes_gcm_decrypt(aes_key: bytes, ciphertext: bytes) -> str:
    from Cryptodome.Cipher import AES
    if ciphertext[:3] in (b"v10", b"v11", b"v20"):
        nonce = ciphertext[3:15]
        data  = ciphertext[15:-16]
        cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt(data).decode("utf-8", errors="replace")
    return _dpapi_decrypt(ciphertext).decode("utf-8", errors="replace")


def _chromium_epoch_to_unix(ts: int) -> int:
    if ts <= 0:
        return 0
    return (ts // 1_000_000) - 11_644_473_600


# ──────────────────────────────────────────────────────────
# Kilitli dosya kopyalama (tarayıcı kapalıyken çalışır)
# ──────────────────────────────────────────────────────────

def _safe_copy(src: str, dst: str) -> bool:
    """
    Dosyayı kopyalamaya çalış. Tarayıcı açıksa dosya kilitlidir → False döner.
    """
    try:
        shutil.copy2(src, dst)
        return True
    except (PermissionError, OSError):
        return False


# ──────────────────────────────────────────────────────────
# Chromium (Brave/Chrome/Edge) cookie okuyucu
# ──────────────────────────────────────────────────────────

def read_chromium_cookies(user_data_dir: Path) -> list:
    try:
        aes_key = _get_encryption_key(user_data_dir)
    except Exception as e:
        log.debug(f"  Anahtar alınamadı: {e}")
        return []

    cookie_files = (list(user_data_dir.glob("*/Network/Cookies")) +
                    list(user_data_dir.glob("*/Cookies")))

    all_cookies = []
    for cookie_db in cookie_files:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name

        if not _safe_copy(str(cookie_db), tmp_path):
            log.debug(f"  Kilitli (tarayıcı açık): {cookie_db.name}")
            os.unlink(tmp_path)
            continue

        # WAL kopyala (varsa)
        for ext in ("-wal", "-shm"):
            src_ext = Path(str(cookie_db) + ext)
            if src_ext.exists():
                _safe_copy(str(src_ext), tmp_path + ext)

        try:
            conn = sqlite3.connect(f"file:{tmp_path}?mode=ro", uri=True)
            rows = conn.execute(
                "SELECT host_key, name, encrypted_value, path, expires_utc, is_secure "
                "FROM cookies"
            ).fetchall()
            conn.close()
        except Exception as e:
            log.debug(f"  SQLite hatası: {e}")
            continue
        finally:
            for f in [tmp_path, tmp_path+"-wal", tmp_path+"-shm"]:
                try: os.unlink(f)
                except: pass

        for row in rows:
            try:
                value = _aes_gcm_decrypt(aes_key, bytes(row[2]))
            except Exception:
                value = ""
            if not value:
                continue
            all_cookies.append({
                "name":     row[1],
                "value":    value,
                "domain":   row[0],
                "path":     row[3],
                "expires":  _chromium_epoch_to_unix(row[4]),
                "secure":   bool(row[5]),
                "httpOnly": False,
                "sameSite": "Lax",
            })

    return all_cookies


# ──────────────────────────────────────────────────────────
# Firefox cookie okuyucu
# ──────────────────────────────────────────────────────────

def read_firefox_cookies() -> list:
    ff_dir = Path(os.environ.get("APPDATA","")) / "Mozilla/Firefox/Profiles"
    if not ff_dir.exists():
        return []
    all_cookies = []
    for profile in ff_dir.iterdir():
        cookie_db = profile / "cookies.sqlite"
        if not cookie_db.exists():
            continue
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name
        if not _safe_copy(str(cookie_db), tmp_path):
            os.unlink(tmp_path)
            continue
        try:
            conn = sqlite3.connect(f"file:{tmp_path}?mode=ro", uri=True)
            rows = conn.execute(
                "SELECT host, name, value, path, expiry, isSecure, isHttpOnly FROM moz_cookies"
            ).fetchall()
            conn.close()
            for row in rows:
                all_cookies.append({
                    "name": row[1], "value": row[2], "domain": row[0],
                    "path": row[3], "expires": row[4],
                    "secure": bool(row[5]), "httpOnly": bool(row[6]), "sameSite": "Lax",
                })
        except Exception as e:
            log.debug(f"Firefox SQLite: {e}")
        finally:
            try: os.unlink(tmp_path)
            except: pass
    return all_cookies


# ──────────────────────────────────────────────────────────
# Domain filtreleme
# ──────────────────────────────────────────────────────────

def filter_cookies(cookies: list, domains: set) -> list:
    result, seen = [], set()
    for c in cookies:
        d = c.get("domain", "").lstrip(".")
        if not any(d == t.lstrip(".") or d.endswith("." + t.lstrip(".")) for t in domains):
            continue
        key = (c["name"], c.get("domain",""))
        if key in seen:
            continue
        seen.add(key)
        result.append(c)
    return result


# ──────────────────────────────────────────────────────────
# Extension JSON import
# ──────────────────────────────────────────────────────────

def import_from_file(json_path: str, platform: str) -> bool:
    """
    Cookie-Editor extension'ından export edilmiş JSON'u içe aktar.
    Cookie-Editor formatı: [{name, value, domain, path, expires, secure, httpOnly, sameSite}, ...]
    """
    domains  = TWITTER_DOMAINS if platform == "twitter" else INSTAGRAM_DOMAINS
    out_file = X_SESSION if platform == "twitter" else IG_SESSION
    site     = "X/Twitter" if platform == "twitter" else "Instagram"
    critical = {"auth_token", "ct0"} if platform == "twitter" else {"sessionid", "csrftoken"}

    if not os.path.isfile(json_path):
        print(f"  [HATA] Dosya bulunamadı: {json_path}")
        return False

    with open(json_path, encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        print(f"  [HATA] Beklenen format: JSON array")
        return False

    # Cookie-Editor formatını standart formata dönüştür
    cookies = []
    for c in raw:
        cookies.append({
            "name":     c.get("name", ""),
            "value":    c.get("value", ""),
            "domain":   c.get("domain", ""),
            "path":     c.get("path", "/"),
            "expires":  c.get("expirationDate") or c.get("expires") or 0,
            "secure":   c.get("secure", False),
            "httpOnly": c.get("httpOnly", False),
            "sameSite": c.get("sameSite", "Lax"),
        })

    # Filtrele (opsiyonel — kullanıcı doğru sayfadan export ettiyse genelde hepsi ilgili)
    filtered = filter_cookies(cookies, domains)
    if not filtered:
        # Domain eşleşmesi yoksa tümünü kullan (bazı extension'lar domain'i farklı yazar)
        filtered = [c for c in cookies if c.get("name") in critical or c.get("value")]

    if not filtered:
        print(f"  [HATA] {json_path} içinde {site} cookie'si bulunamadı.")
        return False

    names   = {c["name"] for c in filtered}
    missing = critical - names
    if missing:
        print(f"  [UYARI] Kritik cookie eksik: {missing}")
        print(f"  {site}'a giriş yapılmış mı?")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    print(f"\n  Import : {json_path}")
    print(f"  Cookie : {len(filtered)} adet")
    print(f"  Kritik : {names & critical}")
    print(f"  Kayit  : {out_file}")
    return not missing


# ──────────────────────────────────────────────────────────
# Otomatik yakalama
# ──────────────────────────────────────────────────────────

def capture_auto(platform: str) -> bool:
    domains  = TWITTER_DOMAINS if platform == "twitter" else INSTAGRAM_DOMAINS
    out_file = X_SESSION if platform == "twitter" else IG_SESSION
    site     = "X/Twitter" if platform == "twitter" else "Instagram"
    critical = {"auth_token", "ct0"} if platform == "twitter" else {"sessionid", "csrftoken"}

    print(f"\n{'='*55}")
    print(f"  {site} — Otomatik Okuma")
    print(f"{'='*55}")

    best_cookies, best_browser = [], None

    for name, user_data_dir in CHROMIUM_PROFILES:
        if not user_data_dir.exists():
            continue
        log.info(f"Deneniyor: {name}")
        cookies  = read_chromium_cookies(user_data_dir)
        filtered = filter_cookies(cookies, domains)
        log.info(f"  -> {len(cookies)} toplam, {len(filtered)} {site}")
        if len(filtered) > len(best_cookies):
            best_cookies, best_browser = filtered, name

    log.info("Deneniyor: Firefox")
    ff_c     = read_firefox_cookies()
    ff_f     = filter_cookies(ff_c, domains)
    log.info(f"  -> {len(ff_c)} toplam, {len(ff_f)} {site}")
    if len(ff_f) > len(best_cookies):
        best_cookies, best_browser = ff_f, "Firefox"

    if not best_cookies:
        print(f"\n  [HATA] Hicbir tarayicida {site} cookie'si okunamadi.")
        print(f"  Muhtemelen tarayici acik ve dosya kilitli.")
        _print_manual_instructions(site, platform)
        return False

    names   = {c["name"] for c in best_cookies}
    missing = critical - names
    if missing:
        print(f"\n  [UYARI] Kritik cookie eksik: {missing} — {site}'a giris yapilmamis")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(best_cookies, f, ensure_ascii=False, indent=2)

    print(f"\n  Tarayici : {best_browser}")
    print(f"  Cookie   : {len(best_cookies)} adet")
    print(f"  Kritik   : {names & critical}")
    print(f"  Kayit    : {out_file}")
    return not missing


def _print_manual_instructions(site: str, platform: str):
    domain = "x.com" if platform == "twitter" else "instagram.com"
    arg    = "--import-twitter" if platform == "twitter" else "--import-instagram"
    fname  = "twitter_cookies.json" if platform == "twitter" else "ig_cookies.json"
    print(f"""
  MANUEL YÖNTEM (tarayici acikken):
  ─────────────────────────────────
  1. Brave'e "Cookie-Editor" extension'i kur:
     https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm

  2. {domain} adresine git

  3. Extension ikonuna tikla → "Export" → "Export All" → JSON kopyala
     veya "Export as file" ile kaydet → {fname}

  4. Calistir:
     python scrapers/capture_cookies.py {arg} {fname}
""")


# ──────────────────────────────────────────────────────────
# Session durumu
# ──────────────────────────────────────────────────────────

def verify_sessions():
    print(f"\n{'='*55}")
    print("  SESSION DURUMU")
    print(f"{'='*55}")
    for label, path, critical in [
        ("Twitter/X", X_SESSION,  {"auth_token", "ct0"}),
        ("Instagram", IG_SESSION, {"sessionid", "csrftoken"}),
    ]:
        if not os.path.isfile(path):
            print(f"  {label}: DOSYA YOK")
            continue
        with open(path, encoding="utf-8") as f:
            cookies = json.load(f)
        names  = {c["name"] for c in cookies}
        ok     = critical.issubset(names)
        mtime  = datetime.fromtimestamp(os.path.getmtime(path))
        status = "HAZIR" if ok else "EKSIK COOKIE"
        print(f"  {label}: {status} | {len(cookies)} cookie | {mtime:%Y-%m-%d %H:%M}")
        if not ok:
            print(f"    Eksik: {critical - names}")


# ──────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Tarayicidan cookie yakala",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python scrapers/capture_cookies.py                          # Otomatik (tarayici kapali)
  python scrapers/capture_cookies.py --twitter                # Sadece Twitter otomatik
  python scrapers/capture_cookies.py --import-twitter t.json  # Extension JSON import
  python scrapers/capture_cookies.py --import-twitter t.json --import-instagram i.json
        """
    )
    parser.add_argument("--twitter",          action="store_true", help="Sadece Twitter otomatik")
    parser.add_argument("--instagram",        action="store_true", help="Sadece Instagram otomatik")
    parser.add_argument("--import-twitter",   metavar="FILE",      help="Cookie-Editor JSON (Twitter)")
    parser.add_argument("--import-instagram", metavar="FILE",      help="Cookie-Editor JSON (Instagram)")
    args = parser.parse_args()

    results = {}

    # Import modu
    if args.import_twitter:
        print(f"\n[Twitter] Dosyadan import: {args.import_twitter}")
        results["twitter"] = import_from_file(args.import_twitter, "twitter")
    if args.import_instagram:
        print(f"\n[Instagram] Dosyadan import: {args.import_instagram}")
        results["instagram"] = import_from_file(args.import_instagram, "instagram")

    # Otomatik mod (import verilmemişse)
    if not args.import_twitter:
        if args.twitter or (not args.twitter and not args.instagram and not args.import_instagram):
            results["twitter"] = capture_auto("twitter")
    if not args.import_instagram:
        if args.instagram or (not args.twitter and not args.instagram and not args.import_twitter):
            results["instagram"] = capture_auto("instagram")

    verify_sessions()

    failed = [p for p, ok in results.items() if not ok]
    if failed:
        print(f"\n  Eksik/basarisiz: {failed}")
        sys.exit(1)
    else:
        print("\n  Tum session'lar hazir! Scraper'lari calistirabilirsiniz.")


if __name__ == "__main__":
    main()
