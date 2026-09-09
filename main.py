from pathlib import Path

import markdown2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import Article, ArticleInfo, New_article


app = FastAPI()

# Autorise notre frontend à appeler le backend en développement local.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Le dossier articles est à côté du dossier backend.
ARTICLES_DIR = Path(__file__).resolve().parent.parent / "articles"


# ROUTE 1 : vérifier que le serveur fonctionne.
@app.get("/")
def root():
    return {"message": "It works !!!"}


@app.post("/create", response_model=Article)
def create_article(article: New_article):
    # Récupérer le titre et le Markdown envoyés par le client.
    name = article.name.strip()
    source = article.content

    if len(name) == 0:
        raise HTTPException(400, "Le titre est trop court")
    if len(name) > 50:
        raise HTTPException(400, "Le titre est trop long")
    if len(source) == 0:
        raise HTTPException(400, "Le contenu ne doit pas être vide")
    if len(source) > 100000:
        raise HTTPException(400, "Le contenu est trop long")

    # Éviter les noms vides ou contenant des éléments de chemin.
    if any(c in name for c in '/\\:*?"<>|') or ".." in name:
        raise HTTPException(400, "Nom d'article invalide")

    # Même convention que nos autres routes.
    article_url = "_".join(name.split())
    new_article_file = ARTICLES_DIR / (article_url + ".md")

    # Le mode "x" crée un fichier sans écraser un article existant.
    try:
        with new_article_file.open("x", encoding="utf-8") as fichier:
            fichier.write(source)
    except FileExistsError:
        raise HTTPException(409, "Cet article existe déjà")

    # Renvoyer l'article créé, comme demandé dans le README.
    return Article(
        name=name,
        articleUrl=article_url,
        content=markdown2.markdown(source),
        source=source,
    )


# ROUTE 2 : renvoyer la liste des articles.
# response_model décrit la réponse attendue dans /docs.
@app.get("/list", response_model=list[ArticleInfo])
def list_article() -> list[dict[str, str]]:
    articles = []

    for fichier in sorted(ARTICLES_DIR.iterdir()):
        if fichier.is_file() and fichier.suffix.lower() == ".md":
            # Retirer l'extension et remplacer les underscores.
            nom = fichier.stem.replace("_", " ")

            articles.append({
                "name": nom,
                "articleUrl": "_".join(nom.split()),
            })

    return articles


# ROUTE 3 : lire un article et convertir son Markdown en HTML.
@app.get("/article/{article_url}", response_model=Article)
def read_article(article_url: str) -> dict[str, str]:
    fichier_trouve = None

    for fichier in sorted(ARTICLES_DIR.iterdir()):
        if fichier.is_file() and fichier.suffix.lower() == ".md":
            nom = fichier.stem.replace("_", " ")
            url = "_".join(nom.split())

            if url == article_url:
                fichier_trouve = fichier
                break

    # Aucun fichier ne correspond à l'article demandé.
    if fichier_trouve is None:
        raise HTTPException(
            status_code=404,
            detail="Article introuvable",
        )

    # Lire le Markdown original et le convertir en HTML pour le frontend.
    source = fichier_trouve.read_text(encoding="utf-8-sig")
    contenu_html = markdown2.markdown(source)

    return {
        "name": fichier_trouve.stem.replace("_", " "),
        "articleUrl": article_url,
        "content": contenu_html,
        "source": source,
    }