import io
import uuid
from pathlib import Path

import markdown2
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

from article import ARTICLES_DIR, get_article_content, write_article
from moderation import contains_banned_word
from rate_limit import rate_limiter
from models import (
    Article,
    ArticleInfo,
    Comment,
    CommentEdit,
    CommentIn,
    EditArticle,
    ImageUploadResponse,
    New_article,
)

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
    metadata = {"author": article.author, "category": article.category, "tags": article.tags}

    # overwrite=False: write_article raises 409 if the article already exists.
    write_article(article_url, metadata, source, overwrite=False)

    return Article(
        name=name,
        articleUrl=article_url,
        content=markdown2.markdown(source),
        source=source,
        author=metadata["author"],
        category=metadata["category"],
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
        author=metadata.get("author", ""),
        category=metadata.get("category", ""),
        tags=metadata.get("tags", []),
    )


# ROUTE 4: edit an existing article. Fields left out of the request keep their
# current value; fields explicitly sent (even empty) overwrite it.
@app.post("/article/{article_url}/edit", response_model=Article)
def edit_article(article_url: str, edit: EditArticle) -> Article:
    metadata, current_body = get_article_content(article_url)
    provided_fields = edit.model_fields_set

    new_body = edit.content if "content" in provided_fields else current_body
    new_author = edit.author if "author" in provided_fields else metadata.get("author", "")
    new_category = edit.category if "category" in provided_fields else metadata.get("category", "")
    new_tags = edit.tags if "tags" in provided_fields else metadata.get("tags", [])

    if len(new_body) == 0:
        raise HTTPException(400, "The content must not be empty")
    if len(new_body) > 100000:
        raise HTTPException(400, "The content is too long")

    # Preserve any other metadata fields this route doesn't manage explicitly.
    new_metadata = {**metadata, "author": new_author, "category": new_category, "tags": new_tags}
    write_article(article_url, new_metadata, new_body, overwrite=True)

    return Article(
        name=article_url.replace("_", " "),
        articleUrl=article_url,
        content=markdown2.markdown(new_body),
        source=new_body,
        author=new_author,
        category=new_category,
        tags=new_tags,
    )


# ROUTE 5: move an article to trash instead of deleting it permanently.
@app.get("/article/{article_url}/delete")
def delete_article(article_url: str) -> dict[str, bool]:
    source = ARTICLES_DIR / f"{article_url}.md"
    metadata_source = ARTICLES_DIR / f"{article_url}.json"

    if not source.exists():
        raise HTTPException(404, "The article does not exist.")

    destination = TRASH_DIR / source.name
    if destination.exists():
        destination.unlink()
    source.rename(destination)

    # Move the metadata companion file too, if it exists.
    if metadata_source.exists():
        metadata_destination = TRASH_DIR / metadata_source.name
        if metadata_destination.exists():
            metadata_destination.unlink()
        metadata_source.rename(metadata_destination)

    return {"deleted": True}


# In-memory storage: a plain Python list, as suggested by the exercise.
# Resets whenever the server restarts.
comments: list[Comment] = []
_next_comment_id = 1


@app.get("/comments", response_model=list[Comment])
def list_comments() -> list[Comment]:
    return comments


@app.post(
    "/comments",
    response_model=Comment,
    dependencies=[Depends(rate_limiter("comments", max_requests=5, window_seconds=60))],
)
def create_comment(comment: CommentIn) -> Comment:
    if contains_banned_word(comment.content) or (comment.author and contains_banned_word(comment.author)):
        raise HTTPException(400, "Nice try, but no insults here.")

    global _next_comment_id

    new_comment = Comment(
        id=_next_comment_id,
        author=comment.author,
        content=comment.content,
    )
    comments.append(new_comment)
    _next_comment_id += 1

    return new_comment


@app.patch("/comments/{comment_id}", response_model=Comment)
def edit_comment(comment_id: int, edit: CommentEdit) -> Comment:
    comment = next((c for c in comments if c.id == comment_id), None)
    if comment is None:
        raise HTTPException(404, "Comment not found")

    provided_fields = edit.model_fields_set

    if "content" in provided_fields:
        new_content = (edit.content or "").strip()
        if not new_content:
            raise HTTPException(400, "Content must not be blank")
        if contains_banned_word(new_content):
            raise HTTPException(400, "Nice try, but no insults here.")
        comment.content = new_content

    if "author" in provided_fields:
        if edit.author and contains_banned_word(edit.author):
            raise HTTPException(400, "Nice try, but no insults here.")
        comment.author = edit.author

    return comment


@app.delete("/comments/{comment_id}")
def delete_comment(comment_id: int) -> dict[str, bool]:
    original_length = len(comments)
    comments[:] = [c for c in comments if c.id != comment_id]

    if len(comments) == original_length:
        raise HTTPException(404, "Comment not found")

    return {"deleted": True}


@app.post("/comments/{comment_id}/like", response_model=Comment)
def like_comment(comment_id: int) -> Comment:
    comment = next((c for c in comments if c.id == comment_id), None)
    if comment is None:
        raise HTTPException(404, "Comment not found")

    comment.likes += 1
    return comment


@app.post("/comments/{comment_id}/unlike", response_model=Comment)
def unlike_comment(comment_id: int) -> Comment:
    comment = next((c for c in comments if c.id == comment_id), None)
    if comment is None:
        raise HTTPException(404, "Comment not found")

    comment.likes = max(0, comment.likes - 1)
    return comment


# Sibling folder to "articles", created on first run if missing.
IMAGES_DIR = ARTICLES_DIR.parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)

# Sibling folder to "articles", used by the delete route above.
TRASH_DIR = ARTICLES_DIR.parent / "trash"
TRASH_DIR.mkdir(exist_ok=True)

# Serve uploaded images directly at /images/<filename>.
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_IMAGE_FORMATS = {"jpeg", "png", "gif", "webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_IMAGE_DIMENSION = 4000  # pixels, width or height


@app.post(
    "/upload-image",
    response_model=ImageUploadResponse,
    dependencies=[Depends(rate_limiter("upload-image", max_requests=10, window_seconds=60))],
)
async def upload_image(file: UploadFile = File(...)) -> ImageUploadResponse:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "Only JPEG, PNG, GIF or WEBP images are allowed")

    file_bytes = await file.read()

    if len(file_bytes) == 0:
        raise HTTPException(400, "The image must not be empty")
    if len(file_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(400, "The image is too large (max 5 MB)")

    # Verify the file is a genuine, decodable image — not just a file with a
    # spoofed extension or Content-Type header.
    try:
        with Image.open(io.BytesIO(file_bytes)) as probe:
            probe.verify()
        # verify() leaves the file object unusable for further reads, so we
        # reopen a fresh copy to read its actual size and format.
        with Image.open(io.BytesIO(file_bytes)) as image:
            width, height = image.size
            image_format = (image.format or "").lower()
    except UnidentifiedImageError:
        raise HTTPException(400, "The uploaded file is not a valid image.")

    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise HTTPException(400, "Only JPEG, PNG, GIF or WEBP images are allowed")
    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        raise HTTPException(400, f"Image dimensions must not exceed {MAX_IMAGE_DIMENSION}px.")

    # Generate a random filename to avoid collisions and path traversal,
    # keeping only the original extension.
    extension = Path(file.filename).suffix.lower()
    filename = f"{uuid.uuid4().hex}{extension}"
    image_path = IMAGES_DIR / filename

    image_path.write_bytes(file_bytes)

    return ImageUploadResponse(url=f"/images/{filename}")