"""API / Route, Bảo mật (OWASP A01) và Tính tái lập test cho ứng dụng Flask."""
import pytest
from tests.db_test_helper import reset_db
from main import app
from repositories import db_connection


@pytest.fixture(autouse=True)
def clean_database():
    reset_db()
    yield
    reset_db()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def login(client, username, password="123456"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


class TestHealthAndReproducibility:
    def test_health_endpoint_returns_200_ok(self, client):
        """Kiểm tra endpoint /health cho Docker healthcheck và Deployment Guide."""
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "ok"
        assert body["database"] == "ok"

    def test_customer_lookup_is_reproducible_across_runs(self, client):
        """Tính tái lập: Gọi /api/customer 2 lần liên tiếp với cùng đầu vào trả kết quả giống hệt nhau."""
        login(client, "nhanvientiepnhan")
        resp1 = client.get("/api/customer?phone=0843310647")
        resp2 = client.get("/api/customer?phone=+84 843 310 647")

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.get_json() == resp2.get_json()
        assert resp1.get_json()["full_name"] == "Vu The Long"


class TestApiValidationAndErrors:
    def test_invalid_phone_on_api_customer_returns_400_and_message(self, client):
        """Dữ liệu sai: SĐT không hợp lệ -> HTTP 400 + thông báo lỗi rõ ràng."""
        login(client, "nhanvientiepnhan")
        resp = client.get("/api/customer?phone=123")

        assert resp.status_code == 400
        data = resp.get_json()
        assert data["valid"] is False
        assert "không hợp lệ" in data["error"]

    def test_create_ticket_api_rejects_short_description_with_400(self, client):
        """Dữ liệu sai: Mô tả dưới 10 ký tự qua API JSON -> HTTP 400 + thông báo lỗi."""
        login(client, "nhanvientiepnhan")
        resp = client.post(
            "/reception/create",
            json={
                "phone": "0843310647",
                "full_name": "Vu The Long",
                "serial_no": "IMEI350000000000001",
                "model_name": "Mekong Phone X1",
                "issue_category": "MAN_HINH",
                "priority": "CAO",
                "issue_desc": "qua ngan",
            },
            headers={"Accept": "application/json"},
        )

        assert resp.status_code == 400
        data = resp.get_json()
        assert "ít nhất 10 ký tự" in data["error"]

    def test_assign_nonexistent_technician_via_api_returns_400(self, client):
        """Dữ liệu sai: Gán technician_id không tồn tại -> HTTP 400, không sập 500."""
        login(client, "quantrivien")
        resp = client.post(
            "/admin/assign/2",
            json={"technician_id": 999},
            headers={"Accept": "application/json"},
        )

        assert resp.status_code == 400
        assert "không tồn tại" in resp.get_json()["error"]

    def test_login_invalid_credentials_returns_401_json(self, client):
        """Dữ liệu sai: Sai mật khẩu qua API JSON -> HTTP 401 + thông báo an toàn."""
        resp = client.post(
            "/login",
            json={"username": "nhanvientiepnhan", "password": "wrong-password"},
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 401
        assert "Sai tên đăng nhập hoặc mật khẩu" in resp.get_json()["error"]

    def test_internal_error_does_not_leak_traceback_or_db_details(self, client, monkeypatch):
        """Bảo mật lỗi nội bộ: ngoại lệ bất ngờ không lộ chi tiết SQL/traceback ra phản hồi."""
        from routes import reception_routes

        def boom(*_args, **_kwargs):
            raise RuntimeError("MYSQL_SECRET_PASSWORD_LEAK_TEST")

        monkeypatch.setattr(reception_routes, "create_ticket", boom)
        login(client, "nhanvientiepnhan")
        resp = client.post(
            "/reception/create",
            json={"phone": "0843310647"},
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 500
        body = resp.get_json()
        assert "MYSQL_SECRET_PASSWORD_LEAK_TEST" not in body["error"]
        assert "Đã xảy ra lỗi hệ thống" in body["error"]


class TestSecurityAccessControlA01:
    def test_unauthenticated_api_request_returns_401(self, client):
        """A01 OWASP: Gọi /api/customer khi chưa đăng nhập -> 401 Unauthorized."""
        resp = client.get("/api/customer?phone=0843310647")
        assert resp.status_code == 401
        assert "Chưa đăng nhập" in resp.get_json()["error"]

    def test_wrong_role_accessing_admin_assign_returns_403(self, client):
        """A01 OWASP: Nhân viên tiếp nhận không được phép phân công KTV -> 403 Forbidden."""
        login(client, "nhanvientiepnhan")
        resp = client.post(
            "/admin/assign/2",
            json={"technician_id": 1},
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 403
        assert "không có quyền" in resp.get_json()["error"]

    def test_technician_cannot_update_another_technicians_ticket(self, client):
        """A01 OWASP (Ownership): kythuatvien2 cập nhật phiếu BH-0001 của kythuatvien1 -> 403 Forbidden."""
        login(client, "kythuatvien2")
        resp = client.post(
            "/technician/update/1",
            data={"new_status": "CHO_LINH_KIEN"},
            headers={"Accept": "application/json"},
        )

        assert resp.status_code == 403
        assert "không được phân công cho bạn" in resp.get_json()["error"]

        with app.app_context():
            row = db_connection.query("SELECT ticket_status FROM ticket WHERE ticket_id = 1", one=True)
            assert row["ticket_status"] == "DANG_XU_LY"


class TestEndToEndApiFlow:
    def test_full_api_workflow_create_assign_update_close(self, client):
        """API E2E luồng chính: Tiếp nhận tạo -> Quản trị gán -> KTV xử lý -> Đóng phiếu."""
        login(client, "nhanvientiepnhan")
        create_resp = client.post(
            "/reception/create",
            json={
                "phone": "0977888999",
                "full_name": "Nguyen Thi Mai",
                "serial_no": "IMEI358888888888001",
                "model_name": "Mekong Phone Z1",
                "purchase_date": "2026-05-01",
                "warranty_months": "12",
                "issue_category": "PIN",
                "priority": "CAO",
                "issue_desc": "Pin tut nhanh tu 100% xuong 20% trong 1 gio",
            },
            headers={"Accept": "application/json"},
        )
        assert create_resp.status_code == 201
        tid = create_resp.get_json()["ticket_id"]

        login(client, "quantrivien")
        assign_resp = client.post(
            f"/admin/assign/{tid}",
            json={"technician_id": 1},
            headers={"Accept": "application/json"},
        )
        assert assign_resp.status_code == 200

        login(client, "kythuatvien")
        for st in ("DANG_XU_LY", "CHO_LINH_KIEN", "HOAN_TAT"):
            up_resp = client.post(
                f"/technician/update/{tid}",
                json={"new_status": st},
                headers={"Accept": "application/json"},
            )
            assert up_resp.status_code == 200
            assert up_resp.get_json()["new_status"] == st

        login(client, "nhanvientiepnhan")
        close_resp = client.post(
            f"/reception/close/{tid}",
            headers={"Accept": "application/json"},
        )
        assert close_resp.status_code == 200
        assert close_resp.get_json()["ticket_status"] == "DA_DONG"
