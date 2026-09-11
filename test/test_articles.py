# tests/test_articles.py

def test_create_and_read_article(client):
    response = client.post("/create", json={"name": "My first article", "content": "# Hello"})
    assert response.status_code == 200
    data = response.json()
    assert data["articleUrl"] == "My_first_article"
    assert "<h1>Hello</h1>" in data["content"]

    response = client.get(f"/article/{data['articleUrl']}")
    assert response.status_code == 200
    assert response.json()["source"] == "# Hello"


def test_create_article_rejects_empty_content(client):
    response = client.post("/create", json={"name": "Empty", "content": ""})
    assert response.status_code == 400


def test_create_article_rejects_duplicate(client):
    client.post("/create", json={"name": "Duplicate", "content": "content"})
    response = client.post("/create", json={"name": "Duplicate", "content": "content"})
    assert response.status_code == 409


def test_list_articles(client):
    client.post("/create", json={"name": "Article A", "content": "content"})
    client.post("/create", json={"name": "Article B", "content": "content"})

    response = client.get("/list")
    names = [a["name"] for a in response.json()]
    assert "Article A" in names
    assert "Article B" in names


def test_edit_article_preserves_omitted_fields(client):
    client.post("/create", json={"name": "Editable", "content": "content", "author": "Alex"})

    response = client.post("/article/Editable/edit", json={"content": "new content"})
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "new content"
    assert data["author"] == "Alex"  # untouched, so preserved


def test_edit_article_clears_explicit_empty_field(client):
    client.post("/create", json={"name": "Editable2", "content": "content", "author": "Alex"})

    response = client.post("/article/Editable2/edit", json={"author": ""})
    assert response.json()["author"] == ""


def test_delete_article_moves_to_trash(client):
    client.post("/create", json={"name": "ToDelete", "content": "content"})

    response = client.get("/article/ToDelete/delete")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    response = client.get("/list")
    assert all(a["articleUrl"] != "ToDelete" for a in response.json())