from fastapi import HTTPException


from pathlib import Path


"""def get_article_content(articleurl):
    article_dir = Path("../../../1_blog/articles")
    article_path = article_dir / (articleurl + ".md")
    if not article_path.exists(): # We need to send an error 
        raise HTTPException(404, "The article does not exist.")

    source = article_path.read_text()
    return source """

def get_article_content(articleurl):
    article_dir = Path("../../../1_blog/articles")
    article_path = article_dir / (articleurl + ".md")

    try:
        source = article_path.read_text()
        return source
    except FileNotFoundError:
        raise HTTPException(404, "The article does not exist.")


def write_article(name,content):
    article_dir = Path("../../../1_blog/articles")
    article_path = article_dir / (name + ".md")
    if article_path.exists(): # We need to send an error 
        raise HTTPException(404, "The article already exists.")
    with open(article_path, "w", encoding="utf-8") as f:
        f.write(content)