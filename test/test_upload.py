# tests/test_upload.py

import io

from PIL import Image


def _make_png_bytes(width=10, height=10):
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color="red").save(buffer, format="PNG")
    return buffer.getvalue()


def test_upload_valid_image(client):
    file_bytes = _make_png_bytes()
    response = client.post(
        "/upload-image",
        files={"file": ("test.png", file_bytes, "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["url"].startswith("/images/")


def test_upload_rejects_wrong_content_type(client):
    response = client.post(
        "/upload-image",
        files={"file": ("test.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_rejects_fake_image(client):
    # Correct content-type header, but the bytes are not a real image.
    response = client.post(
        "/upload-image",
        files={"file": ("fake.png", b"not really a png", "image/png")},
    )
    assert response.status_code == 400


def test_upload_rejects_oversized_dimensions(client):
    file_bytes = _make_png_bytes(width=5000, height=5000)
    response = client.post(
        "/upload-image",
        files={"file": ("huge.png", file_bytes, "image/png")},
    )
    assert response.status_code == 400


def test_upload_rate_limit(client):
    file_bytes = _make_png_bytes()
    for _ in range(10):
        response = client.post(
            "/upload-image",
            files={"file": ("test.png", file_bytes, "image/png")},
        )
        assert response.status_code == 200

    response = client.post(
        "/upload-image",
        files={"file": ("test.png", file_bytes, "image/png")},
    )
    assert response.status_code == 429