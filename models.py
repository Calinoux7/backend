from pydantic import BaseModel, Field


class Article(BaseModel):
    name: str = Field (description ="nam of the article", exemple = "My first article")
    content: str
    articleUrl: str
    source: str

# Structure d'un résumé d'article, utilisée par /list.
class ArticleInfo(BaseModel):
    name: str
    articleUrl: str

class New_article(BaseModel):
    name: str
    content: str
