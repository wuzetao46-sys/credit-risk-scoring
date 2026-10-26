"""
Step 1: download the UCI "Default of Credit Card Clients" dataset.

Run:  python download_data.py
Result: data/default_of_credit_card_clients.xls

Dataset page (licence CC BY 4.0):
https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients
"""
import io
import urllib.request
import zipfile
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
TARGET_FILE = DATA_DIR / "default_of_credit_card_clients.xls"

# Official UCI download (a zip with the .xls inside).
UCI_ZIP_URL = "https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip"
# Fallback: a copy of the same .xls kept on GitHub, used if UCI is unreachable.
MIRROR_XLS_URL = ("https://raw.githubusercontent.com/wangzongyan/"
                  "Default-of-credit-card-clients-Data-Project/master/"
                  "default%20of%20credit%20card%20clients.xls")


def download(url: str) -> bytes:
    print(f"Downloading {url} ...")
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if TARGET_FILE.exists():
        print(f"Already downloaded: {TARGET_FILE}")
        return

    try:
        content = download(UCI_ZIP_URL)
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            xls_name = next(n for n in archive.namelist() if n.endswith(".xls"))
            TARGET_FILE.write_bytes(archive.read(xls_name))
    except Exception as error:  # network blocked, file moved, ...
        print(f"UCI download failed ({error}); trying the GitHub mirror.")
        TARGET_FILE.write_bytes(download(MIRROR_XLS_URL))

    print(f"Saved {TARGET_FILE} ({TARGET_FILE.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
