"""Route xác thực người dùng và phân quyền (Authentication / Authorization)."""
from functools import wraps

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash

from repositories import query

from .helpers import get_payload, wants_json

auth_bp = Blueprint("auth", __name__)

ROLE_LABELS = {
    "TIEP_NHAN": "Nhân viên tiếp nhận",
    "QUAN_TRI": "Quản trị viên",
    "KY_THUAT": "Kỹ thuật viên",
}

ROLE_HOME = {
    "TIEP_NHAN": "reception",
    "QUAN_TRI": "admin",
    "KY_THUAT": "technician",
}


def login_required(*roles):
    """Decorator kiểm tra đăng nhập và quyền hạn vai trò."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if "employee_id" not in session:
                if wants_json():
                    return jsonify(error="Chưa đăng nhập."), 401
                return redirect(url_for("login"))
            if roles and session.get("role") not in roles:
                if wants_json():
                    return jsonify(error="Bạn không có quyền truy cập chức năng này."), 403
                flash("Bạn không có quyền truy cập trang này.", "error")
                return redirect(url_for(ROLE_HOME.get(session["role"], "login")))
            return view(*args, **kwargs)
        return wrapper
    return decorator


@auth_bp.route("/", endpoint="index")
def index():
    if "employee_id" in session:
        return redirect(url_for(ROLE_HOME.get(session["role"], "login")))
    return redirect(url_for("login"))


@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    if request.method == "POST":
        payload = get_payload()
        username = (payload.get("username") or "").strip()
        password = payload.get("password") or ""
        emp = query("SELECT * FROM employee WHERE username = %s", (username,), one=True)

        if not emp or not emp["password_hash"] or not check_password_hash(emp["password_hash"], password):
            if wants_json():
                return jsonify(error="Sai tên đăng nhập hoặc mật khẩu."), 401
            flash("Sai tên đăng nhập hoặc mật khẩu.", "error")
        elif not emp["is_active"]:
            if wants_json():
                return jsonify(error="Tài khoản đã bị ngừng hoạt động."), 403
            flash("Tài khoản đã bị ngừng hoạt động.", "error")
        elif emp["role"] not in ROLE_HOME:
            if wants_json():
                return jsonify(error="Vai trò tài khoản không hợp lệ."), 403
            flash("Vai trò tài khoản không hợp lệ.", "error")
        else:
            session.clear()
            session.update(employee_id=emp["employee_id"], full_name=emp["full_name"], role=emp["role"])
            if emp["role"] == "KY_THUAT":
                tech = query(
                    "SELECT technician_id FROM technician WHERE employee_id = %s",
                    (emp["employee_id"],),
                    one=True,
                )
                if not tech:
                    session.clear()
                    if wants_json():
                        return jsonify(error="Tài khoản chưa được cấu hình là kỹ thuật viên."), 403
                    flash("Tài khoản chưa được cấu hình là kỹ thuật viên.", "error")
                    return render_template("login.html")
                session["technician_id"] = tech["technician_id"]
            if wants_json():
                return jsonify(
                    employee_id=emp["employee_id"],
                    full_name=emp["full_name"],
                    role=emp["role"],
                ), 200
            return redirect(url_for(ROLE_HOME[emp["role"]]))
    return render_template("login.html")


@auth_bp.route("/logout", endpoint="logout")
def logout():
    session.clear()
    if wants_json():
        return jsonify(message="Đã đăng xuất."), 200
    return redirect(url_for("login"))
