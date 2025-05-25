import os
import pytest
import time
from fastapi.testclient import TestClient
from backend import app, client as mongo_client
from pymongo.errors import ServerSelectionTimeoutError

client = TestClient(app)

TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "testpassword123"
TEST_NAME = "Test User"

ACCESS_TOKEN = None
ENCRYPTION_KEY = None
ENCRYPTED_FILE_NAME = None
FOLDER_ID = None
SHARED_EMAIL = "shareduser@example.com"

def wait_for_mongodb(max_retries=5, delay=2):
    """Wait for MongoDB to be available with retries"""
    for i in range(max_retries):
        try:
            # Try to ping the server
            mongo_client.admin.command('ping')
            return True
        except ServerSelectionTimeoutError:
            if i < max_retries - 1:
                time.sleep(delay)
            else:
                raise Exception("Could not connect to MongoDB after multiple retries")

@pytest.fixture(scope="session", autouse=True)
def setup_user():
    global ACCESS_TOKEN
    # Wait for MongoDB to be available
    wait_for_mongodb()
    
    # Signup
    # client.post(
    #     "/api/auth/signup",
    #     json={"name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASSWORD}
    # )
    # Login
    response = client.post(
        "/api/auth/login",
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    ACCESS_TOKEN = response.json()["access_token"]


def test_encrypt_endpoint():
    global ENCRYPTION_KEY, ENCRYPTED_FILE_NAME
    test_image_path = "tests/test_image.tiff"
    if not os.path.exists(test_image_path):
        pytest.skip("Test image not found")
    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/encrypt",
            files={"file": ("test_image.tiff", f, "image/TIFF")},
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
        )
    assert response.status_code == 200
    data = response.json()
    ENCRYPTION_KEY = data["encryption_key"]
    ENCRYPTED_FILE_NAME = os.path.basename(data["encrypted_array_path"]).replace(".npy", "")
    assert "preview_image_path" in data


def test_create_folder():
    global FOLDER_ID
    response = client.post(
        "/api/folders",
        data={"name": "TestFolder"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    assert response.status_code in (200, 400)
    FOLDER_ID = "testfolder"


def test_list_folders():
    response = client.get(
        "/api/folders",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_items():
    response = client.get(
        "/api/items",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_star_unstar_move():
    # List items to get an image id
    response = client.get(
        "/api/items",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    items = response.json()
    if not items:
        pytest.skip("No items to star/unstar/move")
    image_id = items[0]["id"]
    # Star
    response = client.post(
        f"/api/items/{image_id}/star",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    assert response.status_code == 200
    # Unstar
    response = client.post(
        f"/api/items/{image_id}/unstar",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    assert response.status_code == 200
    # Move
    response = client.post(
        f"/api/items/{image_id}/move",
        data={"folder_id": FOLDER_ID},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    assert response.status_code == 200


def test_decrypt_endpoint():
    if not (ENCRYPTION_KEY and ENCRYPTED_FILE_NAME):
        pytest.skip("Encryption test did not run or failed")
    response = client.post(
        "/api/decrypt",
        data={"filename": f"{ENCRYPTED_FILE_NAME}", "key": ENCRYPTION_KEY},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")


def test_share_image():
    # List items to get an image id
    response = client.get(
        "/api/items",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    items = response.json()
    if not items:
        pytest.skip("No items to share")
    image_id = items[0]["id"]
    response = client.post(
        "/api/share",
        json={"image_ids": [image_id], "email": SHARED_EMAIL},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_list_starred_items():
    response = client.get(
        "/api/items/starred",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    assert response.status_code == 200


def test_list_recent_items():
    response = client.get(
        "/api/items/recent",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    assert response.status_code == 200


def test_list_shared_items():
    response = client.get(
        "/api/items?shared=true",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    assert response.status_code == 200


def test_search_items():
    response = client.get(
        "/api/search?query=test",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    assert response.status_code == 200


def test_preview():
    if not ENCRYPTED_FILE_NAME:
        pytest.skip("No encrypted file for preview")
    response = client.get(f"/api/preview/{ENCRYPTED_FILE_NAME}_preview")
    assert response.status_code in (200, 404)  # 404 if preview not generated


def test_delete_folder():
    response = client.delete(
        f"/api/folders/{FOLDER_ID}",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    assert response.status_code in (200, 404)  # 404 if already deleted 