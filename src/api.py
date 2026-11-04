"""Web API for the Sentra screening engine."""

'uvicorn api:app --reload --app-dir src'

import sqlite3
import io

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from screen import DB_PATH, load_names, screen, evaluate_cases
from typing import Annotated, Literal
import pandas as pd

MAX_ROWS = 300
MAX_BYTES = 1_000_000  # 1 MB

Method = Literal['hybrid', 'token_set', 'token_sort', 'ratio', 'jaro_winkler', 'levenshtein']

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs when the server starts and stops."""
    load_names()   # startup: load the names into memory, so the first search is fast
    yield          # the server runs while we're paused here
    # anything after 'yield' runs on shutdown (nothing needed for now)


app = FastAPI(title='Sentra', lifespan=lifespan)

# Allow your SvelteKit dev server to call this API from the browser.
# 5173 is SvelteKit's default port; add your deployed address later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_methods=['GET', 'POST'],
    allow_headers=['*'],
)


@app.get('/screen')
def screen_name(
    name: Annotated[str, Query(min_length=1, description='The name to screen')],
    limit: Annotated[int, Query(ge=1, le=50, description='Maximum matches to return')] = 10,
    threshold: Annotated[float, Query(ge=0, le=100, description='Minimum score to include')] = 85,
    method: Annotated[Method, Query(description='Matching method')] = 'hybrid',
):
    """Screen a name against the UK Sanctions List."""
    return {'query': name, 'method': method,
            'matches': screen(name, limit=limit, threshold=threshold, method=method)}


@app.get('/list-info')
def list_info():
    """Which version of the list is loaded, and how many names it contains."""
    with sqlite3.connect(DB_PATH) as conn:
        report_date = conn.execute('SELECT report_date FROM metadata').fetchone()[0]
    return {'report_date': report_date, 'names': len(load_names())}

@app.post('/evaluate-upload')
async def evaluate_upload(
    file: Annotated[UploadFile, File(description='CSV with a test_name column')],
    methods: Annotated[list[Method], Query(max_length=3)] = ['hybrid'],
    threshold: Annotated[float, Query(ge=0, le=100)] = 85,
):
    """Evaluate uploaded test names. The file is processed in memory and never stored."""
    content = await file.read()
    # if len(content) > MAX_BYTES:
    #     raise HTTPException(413, 'File too large (limit 1 MB)')

    try:
        cases = pd.read_csv(io.BytesIO(content), dtype=str)
    except Exception:
        raise HTTPException(400, 'Could not read the file as CSV')

    if 'test_name' not in cases.columns:
        raise HTTPException(400, "The CSV needs a 'test_name' column")
    # if len(cases) > MAX_ROWS:
    #     raise HTTPException(400, f'Too many rows (limit {MAX_ROWS})')

    results = evaluate_cases(cases.dropna(subset=['test_name']), list(methods))

    # Summarise using the same logic as the main evaluation
    has_truth = results['true_id'].notna()
    summary = []
    for method, group in results.groupby('method'):
        pos, neg = group[has_truth[group.index]], group[~has_truth[group.index]]
        summary.append({
            'method': method,
            'catch_rate': round((pos['true_score'] >= threshold).mean(), 3) if len(pos) else None,
            'false_alert_rate': round((neg['top_score'] >= threshold).mean(), 3) if len(neg) else None,
        })

    return {'threshold': threshold, 'summary': summary,
            'rows': results.astype(object).where(results.notna(), None).to_dict(orient='records')}
  