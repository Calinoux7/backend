from pydantic import BaseModel, Field


class Article(BaseModel):
    name: str = Field(description="Name of the article", examples=["My first article"])
    content: str
    articleUrl: str
    source: str
    author: str | None = None
    tags: list[str] = Field(default_factory=list)


# Structure d'un résumé d'article, utilisée par /list.
class ArticleInfo(BaseModel):
    name: str
    articleUrl: str


class New_article(BaseModel):
    name: str
    content: str
    author: str | None = None
    tags: list[str] = Field(default_factory=list)


class EditArticle(BaseModel):
    content: str | None = None
    author: str | None = None
    tags: list[str] | None = None