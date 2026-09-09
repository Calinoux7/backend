import json
from pathlib import Path

from fastapi import HTTPException


# Same folder used by main.py, so both files always agree on where articles live.
ARTICLES_DIR = Path(__file__).resolve().parent.parent / "articles"


def parse_article_file(raw_text: str) -> tuple[dict, str]:
    # Split a raw article file into (metadata, markdown_body).

    first_line, _, rest = raw_text.partition("\n")

    try:
        metadata = json.loads(first_line)
        if not isinstance(metadata, dict):
            raise ValueError("Metadata line is not a JSON object")
    except (json.JSONDecodeError, ValueError):
        # Not a metadata line: the whole file is the Markdown body.
        return {}, raw_text

    return metadata, rest


def build_article_file(metadata: dict, markdown_body: str) -> str:
    # Combine metadata and Markdown body into the on-disk file format
    metadata_line = json.dumps(metadata, ensure_ascii=False)
    return f"{metadata_line}\n{markdown_body}"


def get_article_content(article_url: str) -> tuple[dict, str]:
    # Read an article file and return (metadata, markdown_body)
    article_path = ARTICLES_DIR / (article_url + ".md")

    try:
        raw_text = article_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HTTPException(404, "The article does not exist.")

    return parse_article_file(raw_text)


def write_article(article_url: str, metadata: dict, markdown_body: str, *, overwrite: bool = False) -> None:
    # Write an article file, encoding metadata on the first line.
    article_path = ARTICLES_DIR / (article_url + ".md")

    if article_path.exists() and not overwrite:
        raise HTTPException(409, "This article already exists.")

    file_content = build_article_file(metadata, markdown_body)
    article_path.write_text(file_content, encoding="utf-8")