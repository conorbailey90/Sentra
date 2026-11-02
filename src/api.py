"""Web API for the Sentra screening engine."""

'uvicorn api:app --reload --app-dir src'

import sqlite3
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from screen import DB_PATH, load_names, screen
from typing import Annotated, Literal

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
    allow_methods=['GET'],
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