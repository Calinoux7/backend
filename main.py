# main.py

import markdown2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from article import ARTICLES_DIR, get_article_content, write_article
from models import Article, ArticleInfo, EditArticle, New_article


app = FastAPI()

# Allow our frontend to call the backend in local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ROUTE 1: check that the server is running.
@app.get("/")
def root():
    return {"message": "It works !!!"}


@app.post("/create", response_model=Article)
def create_article(article: New_article):
    name = article.name.strip()
    source = article.content

    if len(name) == 0:
        raise HTTPException(400, "The title is too short")
    if len(name) > 50:
        raise HTTPException(400, "The title is too long")
    if len(source) == 0:
        raise HTTPException(400, "The content must not be empty")
    if len(source) > 100000:
        raise HTTPException(400, "The content is too long")

    # Avoid empty names or names containing path elements.
    if any(c in name for c in '/\\:*?"<>|') or ".." in name:
        raise HTTPException(400, "Invalid article name")

    # Same convention as our other routes.
    article_url = "_".join(name.split())
    metadata = {"author": article.author, "tags": article.tags}

    # overwrite=False: write_article raises 409 if the article already exists.
    write_article(article_url, metadata, source, overwrite=False)

    return Article(
        name=name,
        articleUrl=article_url,
        content=markdown2.markdown(source),
        source=source,
        author=metadata["author"],
        tags=metadata["tags"],
    )


# ROUTE 2: return the list of articles.
# response_model describes the expected response in /docs.
@app.get("/list", response_model=list[ArticleInfo])
def list_article() -> list[dict[str, str]]:
    articles = []

    for file in sorted(ARTICLES_DIR.iterdir()):
        if file.is_file() and file.suffix.lower() == ".md":
            # Strip the extension and turn underscores back into spaces.
            display_name = file.stem.replace("_", " ")

            articles.append({
                "name": display_name,
                "articleUrl": "_".join(display_name.split()),
            })

    return articles


# ROUTE 3: read an article and convert its Markdown body to HTML.
@app.get("/article/{article_url}", response_model=Article)
def read_article(article_url: str) -> Article:
    metadata, markdown_body = get_article_content(article_url)

    return Article(
        name=article_url.replace("_", " "),
        articleUrl=article_url,
        content=markdown2.markdown(markdown_body),
        source=markdown_body,
        author=metadata.get("author"),
        tags=metadata.get("tags", []),
    )


# ROUTE 4: edit an existing article. Fields left out of the request keep their
# current value; fields explicitly sent (even empty) overwrite it.
@app.post("/article/{article_url}/edit", response_model=Article)
def edit_article(article_url: str, edit: EditArticle) -> Article:
    metadata, current_body = get_article_content(article_url)
    provided_fields = edit.model_fields_set

    new_body = edit.content if "content" in provided_fields else current_body
    new_author = edit.author if "author" in provided_fields else metadata.get("author")
    new_tags = edit.tags if "tags" in provided_fields else metadata.get("tags", [])

    if len(new_body) == 0:
        raise HTTPException(400, "The content must not be empty")
    if len(new_body) > 100000:
        raise HTTPException(400, "The content is too long")

    # Preserve any other metadata fields (e.g. "category") that this route
    # doesn't manage explicitly, instead of dropping them on every edit.
    new_metadata = {**metadata, "author": new_author, "tags": new_tags}
    write_article(article_url, new_metadata, new_body, overwrite=True)

    return Article(
        name=article_url.replace("_", " "),
        articleUrl=article_url,
        content=markdown2.markdown(new_body),
        source=new_body,
        author=new_author,
        tags=new_tags,
    )