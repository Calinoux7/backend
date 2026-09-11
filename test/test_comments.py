# tests/test_comments.py

def test_create_and_list_comments(client):
    response = client.post("/comments", json={"author": "Alex", "content": "Great articles!"})
    assert response.status_code == 200
    comment = response.json()
    assert comment["id"] == 1
    assert comment["likes"] == 0

    response = client.get("/comments")
    assert response.json() == [comment]


def test_comment_content_required_non_blank(client):
    response = client.post("/comments", json={"content": "   "})
    assert response.status_code == 422


def test_comment_moderation_blocks_banned_word(client):
    response = client.post("/comments", json={"content": "merde"})
    assert response.status_code == 400


def test_edit_comment_updates_only_provided_fields(client):
    created = client.post("/comments", json={"author": "Alex", "content": "Original"}).json()

    response = client.patch(f"/comments/{created['id']}", json={"content": "Updated"})
    assert response.status_code == 200
    assert response.json()["author"] == "Alex"
    assert response.json()["content"] == "Updated"


def test_delete_comment(client):
    created = client.post("/comments", json={"content": "To delete"}).json()

    response = client.delete(f"/comments/{created['id']}")
    assert response.status_code == 200

    response = client.get("/comments")
    assert response.json() == []


def test_like_and_unlike_comment(client):
    created = client.post("/comments", json={"content": "Likeable"}).json()

    response = client.post(f"/comments/{created['id']}/like")
    assert response.json()["likes"] == 1

    response = client.post(f"/comments/{created['id']}/unlike")
    assert response.json()["likes"] == 0


def test_comment_rate_limit(client):
    for _ in range(5):
        response = client.post("/comments", json={"content": "Spam-proof comment"})
        assert response.status_code == 200

    response = client.post("/comments", json={"content": "One too many"})
    assert response.status_code == 429