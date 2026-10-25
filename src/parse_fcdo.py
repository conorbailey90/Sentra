"""Parse the UK Sanctions List CSV into clean entities and names tables."""

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'processed' / 'sentra.db'

ENTRY_COLS = ['Unique ID', 'OFSI Group ID', 'UN Reference Number',
               'Designation Type', 'Regime Name', 'Designation source',
               'Sanctions Imposed', 'Date Designated', 'Last Updated']

NAME_PARTS = [f'Name {i}' for i in range(1, 7)]
NAME_COLS = (['Unique ID'] + NAME_PARTS +
             ['Title', 'Name type', 'Alias strength',
              'Name non-latin script', 'Non-latin script type', 'Non-latin script language'])


def read_report_date(path: Path):
    """Read the list version from the first line, e.g. 'Report Date: 16-Oct-2026'."""
    with open(path, encoding='utf-8') as f:
        first_line = f.readline().strip()
    date_text = first_line.split(':', 1)[1].strip()
    return datetime.strptime(date_text, '%d-%b-%Y').date()


def load_raw(path: Path) -> pd.DataFrame:
    """Load the CSV, skipping the report date line, with everything as text."""
    return pd.read_csv(path, skiprows=1, dtype=str)


def build_entities(df: pd.DataFrame) -> pd.DataFrame:
    """One row per designation."""
    entities = df[ENTRY_COLS].drop_duplicates()
    assert not entities['Unique ID'].duplicated().any(), 'Make sure there are no duplicated entries'
    return entities


def build_names(df: pd.DataFrame) -> pd.DataFrame:
    """One row per name, with cleaned labels and a full name."""

    # 1. Keep only the name-related columns, and remove the duplicate rows
    #    created by the file listing every combination of names, addresses etc.
    names = df[NAME_COLS].drop_duplicates().copy()

    # 2. Fix inconsistent capitalisation in the labels,
    #    e.g. 'Primary Name' and 'Primary name' both become 'primary name'
    names['Name type'] = names['Name type'].str.strip().str.lower()

    # 3. Build the full name by joining Name 1 to Name 6
    names['full_name'] = (
        names[NAME_PARTS]
        .fillna('')                # empty parts become blank text instead of NaN
        .agg(' '.join, axis=1)     # join the six parts with spaces, row by row
        .str.split()               # split on spaces, which discards the blanks...
        .str.join(' ')             # ...then rejoin with single spaces
    )

    # 4. Set aside names with no Latin-script parts (e.g. non-Latin-only names).
    #    The current matching engine can't use them, so report how many there are
    empty = names['full_name'] == ''
    if empty.any():
        print(f'Setting aside {empty.sum()} names with no Latin-script parts')
    names = names[~empty]

    return names


def validate(entries: pd.DataFrame, names: pd.DataFrame) -> None:
    """Fail loudly if the data doesn't look the way we expect."""
    print(names.head(5))
    has_primary = names.loc[names['Name type'] == 'primary name', 'Unique ID'].nunique()
    assert has_primary == len(entries), f'{len(entries) - has_primary} designations lack a primary name'
    assert (names['full_name'] != '').all(), 'Some names are empty'


def save(entries: pd.DataFrame, names: pd.DataFrame, report_date) -> None:
    """Save both tables, plus the list version, to SQLite."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        entries.to_sql('entries', conn, if_exists='replace', index=False)
        names.to_sql('names', conn, if_exists='replace', index=False)
        pd.DataFrame({'report_date': [str(report_date)]}).to_sql(
            'metadata', conn, if_exists='replace', index=False)


def parse_uk(path: Path) -> None:
    """Run the whole pipeline on one downloaded file."""
    report_date = read_report_date(path)
    df = load_raw(path)
    entries = build_entities(df)
    names = build_names(df)
    print(len(names), 'names after setting aside empties')
    print(names['Name type'].value_counts(dropna=False))
    validate(entries, names)
    save(entries, names, report_date)
    print(f'List dated {report_date}: {len(entries)} designations, {len(names)} names')


if __name__ == '__main__':
    # Parse the most recent downloaded file
    latest = sorted((PROJECT_ROOT / 'data' / 'raw').glob('uk_sanctions_*.csv'))[-1]
    parse_uk(latest)