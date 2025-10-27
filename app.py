from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Query
import hashlib
from collections import Counter
from pydantic import BaseModel, field_validator
from sqlmodel import select
import re

from .models import String, SessionDep, create_db_and_tables

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

class StringAnalysisRequest(BaseModel):
    value: str

    @field_validator('value')
    def check_value_is_string(cls, v):
        if not isinstance(v, str):
            raise ValueError('must be a string')
        return v

def _is_palindrome(string: str) -> bool:
    """Check if string is a palindrome (ignoring spaces, punctuation, case)."""
    cleaned = ''.join(char.lower() for char in string if char.isalnum())
    return cleaned == cleaned[::-1]

def _get_unique_char_count(string: str) -> int:
    """Count unique characters in the string."""
    cleaned = ''.join(char.lower() for char in string if not char.isspace())
    return len(set(cleaned))

def _get_word_count(string: str) -> int:
    """Count words in the string."""
    return len(string.split())

def _get_sha256_hash(string: str) -> str:
    """Generate SHA256 hash of the string."""
    return hashlib.sha256(string.encode('utf-8')).hexdigest()

def _get_char_freq_map(string: str) -> dict[str, int]:
    """Get character frequency map (case-insensitive, excludes whitespace)."""
    cleaned = ''.join(char.lower() for char in string if not char.isspace())
    return dict(Counter(cleaned))

def _analyze_string(string: str) -> dict:
    """Analyze a string and return comprehensive analysis."""
    sha256_hash = _get_sha256_hash(string)
    
    analysis = {
        "id": sha256_hash,
        "value": string,
        "properties": {
            "length": len(string.strip()),
            "is_palindrome": _is_palindrome(string),
            "unique_characters": _get_unique_char_count(string),
            "word_count": _get_word_count(string),
            "sha256_hash": sha256_hash,
            "character_frequency_map": _get_char_freq_map(string)
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    return analysis

@app.post("/strings", status_code=201)
async def analyze_string(request: StringAnalysisRequest, session: SessionDep) -> dict:
    """Endpoint to analyze a string and return its properties."""
    existing_string = session.exec(select(String).where(String.value == request.value)).first()
    if existing_string:
        raise HTTPException(status_code=409, detail="String already exists in the system")

    analysis = _analyze_string(request.value)
    
    new_string = String(
        value=analysis["value"],
        properties=analysis["properties"],
        created_at=analysis["created_at"]
    )
    
    session.add(new_string)
    session.commit()
    session.refresh(new_string)
    
    return analysis

@app.get("/strings/filter-by-natural-language")
async def filter_by_natural_language(query: str, session: SessionDep) -> dict:
    """Endpoint to filter strings by natural language."""
    parsed_filters = {}
    
    if "single word" in query:
        parsed_filters["word_count"] = 1
    if "palindromic" in query:
        parsed_filters["is_palindrome"] = True
    
    length_match = re.search(r'longer than (\d+) characters', query)
    if length_match:
        parsed_filters["min_length"] = int(length_match.group(1)) + 1

    char_match = re.search(r'containing the letter (\w)', query)
    if char_match:
        parsed_filters["contains_character"] = char_match.group(1)

    if not parsed_filters:
        raise HTTPException(status_code=400, detail="Unable to parse natural language query")

    db_query = select(String)
    if "word_count" in parsed_filters:
        db_query = db_query.where(String.properties["word_count"].as_integer() == parsed_filters["word_count"])
    if "is_palindrome" in parsed_filters:
        db_query = db_query.where(String.properties["is_palindrome"].as_boolean() == parsed_filters["is_palindrome"])
    if "min_length" in parsed_filters:
        db_query = db_query.where(String.properties["length"].as_integer() >= parsed_filters["min_length"])
    if "contains_character" in parsed_filters:
        db_query = db_query.where(String.properties["character_frequency_map"].op('->>')(parsed_filters["contains_character"]) != None)

    strings = session.exec(db_query).all()

    return {
        "data": [
            {
                "id": s.properties["sha256_hash"],
                "value": s.value,
                "properties": s.properties,
                "created_at": s.created_at
            } for s in strings
        ],
        "count": len(strings),
        "interpreted_query": {
            "original": query,
            "parsed_filters": parsed_filters
        }
    }

@app.get("/strings/{string_value}")
async def get_string(string_value: str, session: SessionDep) -> dict:
    """Endpoint to get a specific string."""
    string = session.exec(select(String).where(String.value == string_value)).first()
    if not string:
        raise HTTPException(status_code=404, detail="String does not exist in the system")
    
    return {
        "id": string.properties["sha256_hash"],
        "value": string.value,
        "properties": string.properties,
        "created_at": string.created_at
    }

@app.get("/strings")
async def get_all_strings(
    session: SessionDep,
    is_palindrome: bool = Query(None),
    min_length: int = Query(None),
    max_length: int = Query(None),
    word_count: int = Query(None),
    contains_character: str = Query(None)
) -> dict:
    """Endpoint to get all strings with filtering."""
    query = select(String)
    filters_applied = {}

    if is_palindrome is not None:
        query = query.where(String.properties["is_palindrome"].as_boolean() == is_palindrome)
        filters_applied["is_palindrome"] = is_palindrome
    if min_length is not None:
        query = query.where(String.properties["length"].as_integer() >= min_length)
        filters_applied["min_length"] = min_length
    if max_length is not None:
        query = query.where(String.properties["length"].as_integer() <= max_length)
        filters_applied["max_length"] = max_length
    if word_count is not None:
        query = query.where(String.properties["word_count"].as_integer() == word_count)
        filters_applied["word_count"] = word_count
    if contains_character is not None:
        query = query.where(String.properties["character_frequency_map"].op('->>')(contains_character) != None)
        filters_applied["contains_character"] = contains_character

    strings = session.exec(query).all()
    
    return {
        "data": [
            {
                "id": s.properties["sha256_hash"],
                "value": s.value,
                "properties": s.properties,
                "created_at": s.created_at
            } for s in strings
        ],
        "count": len(strings),
        "filters_applied": filters_applied
    }

@app.delete("/strings/{string_value}", status_code=204)
async def delete_string(string_value: str, session: SessionDep):
    """Endpoint to delete a string."""
    string = session.exec(select(String).where(String.value == string_value)).first()
    if not string:
        raise HTTPException(status_code=404, detail="String does not exist in the system")
    
    session.delete(string)
    session.commit()
    return