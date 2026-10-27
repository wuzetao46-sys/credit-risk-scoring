"""
Step 1: download the Lending Club loan dataset.

Run:  python download_data.py
Result: data/lending_club_loans.csv  (about 17 MB, 163,987 loans)

Source: Lending Club public loan data (USA), cleaned and published by H2O.ai for
their consumer-loan tutorial: https://github.com/h2oai/app-consumer-loan
"""
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
TARGET_FILE = DATA_DIR / "lending_club_loans.csv"

URLS = [
    "https://s3.amazonaws.com/h2o-public-test-data/bigdata/laptop/lending-club/loan.csv",
    # Fallback: the same file in H2O's GitHub repository.
    "https://raw.githubusercontent.com/h2oai/app-consumer-loan/master/data/loan.csv",
]


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if TARGET_FILE.exists():
        print(f"Already downloaded: {TARGET_FILE}")
        return

    for url in URLS:
        try:
            print(f"Downloading {url} ...")
            with urllib.request.urlopen(url, timeout=120) as response:
                TARGET_FILE.write_bytes(response.read())
            print(f"Saved {TARGET_FILE} ({TARGET_FILE.stat().st_size // 1024} KB)")
            return
        except Exception as error:  # network blocked, file moved, ...
            print(f"  failed: {error}")

    raise SystemExit("Could not download the dataset. Check your internet connection and try again.")


if __name__ == "__main__":
    main()
