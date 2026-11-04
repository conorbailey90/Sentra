"""Screen names against the parsed sanctions list."""

import re
import sqlite3
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz, process
from rapidfuzz.distance import JaroWinkler, Levenshtein



PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'processed' / 'sentra.db'


def jaro_winkler(s1: str, s2: str, **kwargs) -> float:
    """Jaro-Winkler similarity on a 0-100 scale, to match the other scorers."""
    return JaroWinkler.normalized_similarity(s1, s2) * 100

def levenshtein(s1: str, s2: str, **kwargs) -> float:
    """Levenshtein similarity on a 0-100 scale, to match the other scorers."""
    return Levenshtein.normalized_similarity(s1, s2) * 100


def normalise(name: str) -> str:
    """Lower case, remove accents and punctuation, tidy spaces."""
    name = unicodedata.normalize('NFKD', name)
    name = ''.join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r'[^a-z0-9]+', ' ', name.lower())
    return name.strip()


def hybrid(s1: str, s2: str, **kwargs) -> float:
    """Single word on either side: strict comparison. Otherwise: word-based."""
    if len(s1.split()) == 1 or len(s2.split()) == 1:
        return fuzz.ratio(s1, s2)
    return fuzz.token_set_ratio(s1, s2)


@lru_cache(maxsize=1)
def load_names() -> pd.DataFrame:
    """Load the names with their designation details, once, and keep them in memory."""
    with sqlite3.connect(DB_PATH) as conn:
        names = pd.read_sql(
            '''SELECT n."Unique ID", n.full_name, n."Name type",
                      e."Designation Type", e."Regime Name"
               FROM names n
               JOIN entries e 
               ON n."Unique ID" = e."Unique ID"
            ''',
            conn,
        )
    names['normalised_name'] = names['full_name'].apply(normalise)
    return names[names['normalised_name'] != ''].reset_index(drop=True)


METHODS = {
    'hybrid': hybrid,
    'token_set': fuzz.token_set_ratio,
    'token_sort': fuzz.token_sort_ratio,
    'ratio': fuzz.ratio,
    'jaro_winkler': jaro_winkler,
    'levenshtein': levenshtein
}


def screen(query: str, limit: int = 10, threshold: float = 0,
           method: str = 'hybrid') -> list[dict]:
    """Return the closest matches for a name, highest score first."""
    names = load_names()
    results = process.extract(normalise(query), names['normalised_name'],
                              scorer=METHODS[method], limit=limit, score_cutoff=threshold)
    return [
        {
            'unique_id': names.at[idx, 'Unique ID'],
            'name': names.at[idx, 'full_name'],
            'name_type': names.at[idx, 'Name type'],
            'designation_type': names.at[idx, 'Designation Type'],
            'regime': names.at[idx, 'Regime Name'],
            'score': round(score, 1),
        }
        for _, score, idx in results
    ]

def evaluate_cases(cases: pd.DataFrame, methods: list[str]) -> pd.DataFrame:
    print('bitch')
    """Score each test case with each method. Nothing is stored."""
    names = load_names()
    names_by_id = names.groupby('Unique ID')['normalised_name'].apply(list).to_dict()
    rows = []

    for case in cases.itertuples(index=False):
        query = normalise(str(case.test_name))
        true_id = getattr(case, 'true_id', None)
        true_id = true_id if isinstance(true_id, str) and true_id.strip() else None

        for method in methods:
            scorer = METHODS[method]
            _, top_score, idx = process.extractOne(query, names['normalised_name'], scorer=scorer)

            true_score = None
            if true_id in names_by_id:
                true_score = max(scorer(query, n) for n in names_by_id[true_id])

            rows.append({
                'test_name': case.test_name,
                'true_id': true_id,
                'variation_type': getattr(case, 'variation_type', None) or 'unlabelled',
                'method': method,
                'top_match': names.at[idx, 'full_name'],
                'top_id': names.at[idx, 'Unique ID'],
                'top_score': round(top_score, 1),
                'true_score': None if true_score is None else round(true_score, 1),
            })

    return pd.DataFrame(rows)

if __name__ == '__main__':
    for match in screen('Vladimir Putin', limit=5):
        print(match)