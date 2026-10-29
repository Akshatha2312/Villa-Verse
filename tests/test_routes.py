import pytest
from app.models.villa import Villa

class TestHTTPRoutes:
    """End-to-end integration tests for Flask Blueprint routes."""

    def test_dashboard_route(self, client, sample_villa):
        response = client.get("/")
        assert response.status_code == 200
        assert b"Operations overview" in response.data
        assert b"Occupancy" in response.data
        assert b"Demonstration data" in response.data

    def test_chart_data_api(self, client, sample_villa):
        response = client.get("/api/chart-data")
        assert response.status_code == 200
        assert response.is_json
        data = response.get_json()
        assert "occupancy" in data
        assert "cashflow" in data
        assert "maintenance_categories" in data

    def test_villas_index_and_detail(self, client, sample_villa):
        resp = client.get("/villas/")
        assert resp.status_code == 200
        assert b"Community register" in resp.data
        assert b"Search villa, plot or type" in resp.data
        assert b"V-TEST-01" in resp.data

        resp_detail = client.get(f"/villas/{sample_villa.id}")
        assert resp_detail.status_code == 200
        assert b"V-TEST-01" in resp_detail.data
        assert b"Property Specifications" in resp_detail.data

    def test_create_villa_route(self, client, db_session):
        data = {
            "villa_id": "V-HTTP-99",
            "plot_number": "PL-HTTP-99",
            "villa_type": "The Royal Tuscan (5BHK)",
            "built_up_area": 5200.0,
            "bedrooms": 5,
            "bathrooms": 5,
            "stories": 3,
            "parking_slots": 3,
            "status": "Available",
            "notes": "Route integration test estate."
        }
        resp = client.post("/villas/new", data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert b"registered successfully" in resp.data

        created = Villa.query.filter_by(villa_id="V-HTTP-99").first()
        assert created is not None

    def test_residents_routes(self, client, sample_owner):
        resp = client.get("/residents/")
        assert resp.status_code == 200
        assert b"Residents &amp; owners" in resp.data
        assert b"Arthur Pendelton" in resp.data

        resp_detail = client.get(f"/residents/{sample_owner.id}")
        assert resp_detail.status_code == 200
        assert b"Arthur Pendelton" in resp_detail.data

    def test_maintenance_routes(self, client, sample_villa):
        resp = client.get("/maintenance/")
        assert resp.status_code == 200
        assert b"Maintenance requests" in resp.data
        assert b"Due by" in resp.data

    def test_finance_routes(self, client, sample_villa):
        resp = client.get("/finance/")
        assert resp.status_code == 200
        assert b"Community dues" in resp.data
        assert b"Outstanding" in resp.data

        resp_exp = client.get("/finance/expenses")
        assert resp_exp.status_code == 200
        assert b"Operating expenses" in resp_exp.data
        assert "₹".encode("utf-8") in resp_exp.data

    def test_reports_and_csv_exports(self, client, sample_villa):
        resp = client.get("/reports/")
        assert resp.status_code == 200
        assert b"Community reports" in resp.data
        assert b"Financial position" in resp.data

        villas_csv = client.get("/reports/export/villas.csv")
        assert villas_csv.status_code == 200
        assert villas_csv.content_type == "text/csv; charset=utf-8"
        assert b"Villa ID,Plot Number" in villas_csv.data

        maint_csv = client.get("/reports/export/maintenance.csv")
        assert maint_csv.status_code == 200
        assert maint_csv.content_type == "text/csv; charset=utf-8"

        fin_csv = client.get("/reports/export/finance.csv")
        assert fin_csv.status_code == 200
        assert fin_csv.content_type == "text/csv; charset=utf-8"

    def test_404_handling(self, client, db_session):
        resp = client.get("/villas/999999")
        # Should redirect to index with flash message or show 404
        assert resp.status_code in (200, 302, 404)
