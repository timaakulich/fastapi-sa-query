import pytest
from fastapi.testclient import TestClient


class TestEqualsFilter:
    def test_filter_by_name_eq(self, client: TestClient):
        response = client.get("/users", params={"name__eq": "Alice"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Alice"

    def test_filter_by_age_eq(self, client: TestClient):
        response = client.get("/users", params={"age__eq": 25})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(u["age"] == 25 for u in data)


class TestComparisonFilters:
    def test_filter_age_gte(self, client: TestClient):
        response = client.get("/users", params={"age__gte": 30})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(u["age"] >= 30 for u in data)

    def test_filter_age_lte(self, client: TestClient):
        response = client.get("/users", params={"age__lte": 28})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(u["age"] <= 28 for u in data)

    def test_filter_age_gt(self, client: TestClient):
        response = client.get("/users", params={"age__gt": 28})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(u["age"] > 28 for u in data)

    def test_filter_age_lt(self, client: TestClient):
        response = client.get("/users", params={"age__lt": 28})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(u["age"] < 28 for u in data)

    def test_filter_age_range(self, client: TestClient):
        response = client.get("/users", params={"age__gte": 25, "age__lte": 30})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert all(25 <= u["age"] <= 30 for u in data)


class TestLikeFilters:
    def test_filter_name_like(self, client: TestClient):
        response = client.get("/users", params={"name__like": "lic"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("lic" in u["name"] for u in data)

    def test_filter_name_ilike_case_insensitive(self, client: TestClient):
        response = client.get("/users", params={"name__ilike": "ALICE"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_filter_email_like(self, client: TestClient):
        response = client.get("/users", params={"email__like": "example.com"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert all("example.com" in u["email"] for u in data)


class TestInFilter:
    def test_filter_age_in(self, client: TestClient):
        response = client.get("/users", params={"age__in[]": [25, 30]})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(u["age"] in [25, 30] for u in data)

    def test_filter_age_in_single_value(self, client: TestClient):
        response = client.get("/users", params={"age__in[]": [35]})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Charlie"


class TestIsNullFilter:
    def test_filter_score_is_null_true(self, client: TestClient):
        response = client.get("/users", params={"score__is_null": True})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(u["score"] is None for u in data)

    def test_filter_score_is_null_false(self, client: TestClient):
        response = client.get("/users", params={"score__is_null": False})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(u["score"] is not None for u in data)


class TestDateTimeFilters:
    def test_filter_created_at_gte(self, client: TestClient):
        response = client.get("/users", params={"created_at__gte": "2024-03-01T00:00:00"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_filter_created_at_lte(self, client: TestClient):
        response = client.get("/users", params={"created_at__lte": "2024-02-28T23:59:59"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestCombinedFilters:
    def test_multiple_filters(self, client: TestClient):
        response = client.get(
            "/users",
            params={
                "age__gte": 25,
                "email__like": "example.com",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert all(u["age"] >= 25 for u in data)
        assert all("example.com" in u["email"] for u in data)

    def test_combined_with_null_check(self, client: TestClient):
        response = client.get(
            "/users",
            params={
                "score__is_null": False,
                "age__gte": 28,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(u["score"] is not None for u in data)
        assert all(u["age"] >= 28 for u in data)


class TestOrderBy:
    def test_order_by_age_asc(self, client: TestClient):
        response = client.get("/users", params={"order_by[]": "age"})
        assert response.status_code == 200
        data = response.json()
        ages = [u["age"] for u in data]
        assert ages == sorted(ages)

    def test_order_by_age_desc(self, client: TestClient):
        response = client.get("/users", params={"order_by[]": "-age"})
        assert response.status_code == 200
        data = response.json()
        ages = [u["age"] for u in data]
        assert ages == sorted(ages, reverse=True)

    def test_order_by_name_asc(self, client: TestClient):
        response = client.get("/users", params={"order_by[]": "name"})
        assert response.status_code == 200
        data = response.json()
        names = [u["name"] for u in data]
        assert names == sorted(names)

    def test_order_by_multiple_fields(self, client: TestClient):
        response = client.get("/users", params={"order_by[]": ["age", "-name"]})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5


class TestFilterWithOrderBy:
    def test_filter_and_order(self, client: TestClient):
        response = client.get(
            "/users",
            params={
                "age__gte": 25,
                "order_by[]": "-age",
            }
        )
        assert response.status_code == 200
        data = response.json()
        ages = [u["age"] for u in data]
        assert ages == sorted(ages, reverse=True)
        assert all(age >= 25 for age in ages)

