# article.py

import json
from pathlib import Path

from fastapi import HTTPException


ARTICLES_DIR = Path(__file__).resolve().parent.parent / "articles"

DEFAULT_METADATA = {"author": "", "category": "", "tags": []}


def read_metadata(article_url: str) -> dict:
    """Read the metadata companion file, or return defaults if it's missing."""
    metadata_path = ARTICLES_DIR / (article_url + ".json")
    metadata = dict(DEFAULT_METADATA)

    if metadata_path.exists():
        with metadata_path.open("r", encoding="utf-8") as file:
            metadata.update(json.load(file))

    return metadata


def write_metadata(article_url: str, metadata: dict) -> None:
    """Write the metadata companion file."""
    metadata_path = ARTICLES_DIR / (article_url + ".json")
    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)


def get_article_content(article_url: str) -> tuple[dict, str]:
    """Read an article's Markdown body and its metadata."""
    article_path = ARTICLES_DIR / (article_url + ".md")

    try:
        markdown_body = article_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HTTPException(404, "The article does not exist.")

    return read_metadata(article_url), markdown_body


def write_article(article_url: str, metadata: dict, markdown_body: str, *, overwrite: bool = False) -> None:
    """Write an article's Markdown file and its metadata companion file."""
    article_path = ARTICLES_DIR / (article_url + ".md")

    if article_path.exists() and not overwrite:
        raise HTTPException(409, "This article already exists.")

    article_path.write_text(markdown_body, encoding="utf-8")
    write_metadata(article_url, metadata)