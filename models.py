# models.py

from pydantic import BaseModel, Field, field_validator


class Article(BaseModel):
    name: str = Field(description="Name of the article", examples=["My first article"])
    content: str
    articleUrl: str
    source: str
    author: str = ""
    category: str = ""
    tags: list[str] = Field(default_factory=list)


# Structure d'un résumé d'article, utilisée par /list.
class ArticleInfo(BaseModel):
    name: str
    articleUrl: str


class New_article(BaseModel):
    name: str
    content: str
    author: str = ""
    category: str = ""
    tags: list[str] = Field(default_factory=list)


class EditArticle(BaseModel):
    """All fields are optional: only the ones provided get updated."""
    content: str | None = None
    author: str | None = None
    category: str | None = None
    tags: list[str] | None = None


class CommentIn(BaseModel):
    """What the client sends to POST /comments."""
    content: str
    author: str | None = None

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Content must not be blank")
        return value


class Comment(BaseModel):
    """A stored comment, as returned by GET/POST /comments."""
    id: int
    author: str | None = None
    content: str


class CommentEdit(BaseModel):
    """All fields are optional: only the ones provided get updated."""
    content: str | None = None
    author: str | None = None

class Comment(BaseModel):
    """A stored comment, as returned by GET/POST /comments."""
    id: int
    author: str | None = None
    content: str
    likes: int = 0


class ImageUploadResponse(BaseModel):
    url: str
