import pytest
from fastapi.testclient import TestClient


class TestJoinedFilters:
    """Tests for filtering on joined table columns."""

    def test_filter_posts_by_author_name_eq(self, client: TestClient):
        response = client.get("/posts", params={"author_name__eq": "Alice"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(p["author_name"] == "Alice" for p in data)

    def test_filter_posts_by_author_name_like(self, client: TestClient):
        response = client.get("/posts", params={"author_name__like": "li"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # Alice (2 posts) + Charlie (1 post)

    def test_filter_posts_by_author_name_ilike(self, client: TestClient):
        response = client.get("/posts", params={"author_name__ilike": "BOB"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(p["author_name"] == "Bob" for p in data)

    def test_filter_posts_by_author_age_eq(self, client: TestClient):
        response = client.get("/posts", params={"author_age__eq": 25})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Alice's posts
        assert all(p["author_age"] == 25 for p in data)

    def test_filter_posts_by_author_age_gte(self, client: TestClient):
        response = client.get("/posts", params={"author_age__gte": 30})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # Bob (30, 2 posts) + Charlie (35, 1 post)
        assert all(p["author_age"] >= 30 for p in data)

    def test_filter_posts_by_author_age_lte(self, client: TestClient):
        response = client.get("/posts", params={"author_age__lte": 28})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # Alice (25, 2 posts) + Diana (28, 1 post)
        assert all(p["author_age"] <= 28 for p in data)

    def test_filter_posts_by_author_email_like(self, client: TestClient):
        response = client.get("/posts", params={"author_email__like": "example.com"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5  # All except Charlie's post (test.org)


class TestCombinedJoinedFilters:
    """Tests for combining post filters with joined author filters."""

    def test_filter_posts_by_views_and_author_name(self, client: TestClient):
        response = client.get(
            "/posts",
            params={
                "views__gte": 150,
                "author_name__eq": "Alice",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Python Tips (150) + FastAPI Guide (300)
        assert all(p["author_name"] == "Alice" for p in data)
        assert all(p["views"] >= 150 for p in data)

    def test_filter_posts_by_title_and_author_age(self, client: TestClient):
        response = client.get(
            "/posts",
            params={
                "title__ilike": "python",
                "author_age__lte": 30,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Python Tips by Alice (25)
        assert data[0]["title"] == "Python Tips"

    def test_filter_posts_by_rating_and_author(self, client: TestClient):
        response = client.get(
            "/posts",
            params={
                "rating__gte": 4.5,
                "author_name__like": "lic",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Alice's high-rated posts
        assert all(p["rating"] >= 4.5 for p in data)

    def test_filter_posts_null_rating_by_author_age(self, client: TestClient):
        response = client.get(
            "/posts",
            params={
                "rating__is_null": True,
                "author_age__gte": 30,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["author_name"] == "Charlie"
        assert data[0]["rating"] is None


class TestJoinedOrderBy:
    """Tests for ordering by joined table columns."""

    def test_order_posts_by_author_name_asc(self, client: TestClient):
        response = client.get("/posts", params={"order_by[]": "author_name"})
        assert response.status_code == 200
        data = response.json()
        names = [p["author_name"] for p in data]
        assert names == sorted(names)

    def test_order_posts_by_author_name_desc(self, client: TestClient):
        response = client.get("/posts", params={"order_by[]": "-author_name"})
        assert response.status_code == 200
        data = response.json()
        names = [p["author_name"] for p in data]
        assert names == sorted(names, reverse=True)

    def test_order_posts_by_author_age_asc(self, client: TestClient):
        response = client.get("/posts", params={"order_by[]": "author_age"})
        assert response.status_code == 200
        data = response.json()
        ages = [p["author_age"] for p in data]
        assert ages == sorted(ages)

    def test_order_posts_by_author_age_desc(self, client: TestClient):
        response = client.get("/posts", params={"order_by[]": "-author_age"})
        assert response.status_code == 200
        data = response.json()
        ages = [p["author_age"] for p in data]
        assert ages == sorted(ages, reverse=True)


class TestJoinedFilterAndOrder:
    """Tests for combining joined filters with ordering."""

    def test_filter_by_author_and_order_by_views(self, client: TestClient):
        response = client.get(
            "/posts",
            params={
                "author_age__gte": 28,
                "order_by[]": "-views",
            }
        )
        assert response.status_code == 200
        data = response.json()
        # Bob (30), Charlie (35), Diana (28)
        assert all(p["author_age"] >= 28 for p in data)
        views = [p["views"] for p in data]
        assert views == sorted(views, reverse=True)

    def test_filter_by_views_and_order_by_author_name(self, client: TestClient):
        response = client.get(
            "/posts",
            params={
                "views__gte": 180,
                "order_by[]": "author_name",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert all(p["views"] >= 180 for p in data)
        names = [p["author_name"] for p in data]
        assert names == sorted(names)

    def test_combined_filters_with_multiple_order(self, client: TestClient):
        response = client.get(
            "/posts",
            params={
                "author_email__like": "example.com",
                "order_by[]": ["author_age", "-views"],
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5  # Exclude Charlie's post

