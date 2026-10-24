from datetime import date
from importlib.resources import path
from pathlib import Path

import requests

FCDO_LIST_LINK = 'https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.csv'

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / 'data' / 'raw'


def download_uk_list() -> Path:
    """Download the UK Sanctions List CSV and save a dated copy.

    Returns the path of the saved file.
    """
    # 1. Create data/raw if it doesn't exist; parents=True creates data/ too,
    #    exist_ok=True means no error if it's already there
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Download, giving up after 60 seconds if the server doesn't respond
    response = requests.get(FCDO_LIST_LINK, timeout=60)

    # 3. Raise an error for failed downloads (e.g. 404 or 500), rather than
    #    silently saving an error page as if it were the list
    response.raise_for_status()

    # 4. Build a dated filename, e.g. uk_sanctions_2026-10-23.csv
    filename = f'uk_sanctions_{date.today().isoformat()}.csv'
    file_path = RAW_DATA_DIR / filename

    # 5. Save the raw bytes exactly as published
    file_path.write_bytes(response.content)

    # 6. Return the path so other code can use the file
    return file_path


if __name__ == '__main__':
    saved_path = download_uk_list()
    print(f'Saved to {saved_path}')

    with open(saved_path, encoding='utf-8') as f:
        for _ in range(5):
            print(repr(f.readline()))