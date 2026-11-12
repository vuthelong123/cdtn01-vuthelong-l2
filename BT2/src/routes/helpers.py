"""Các hàm tiện ích dùng chung cho tầng Route (JSON API và HTML form SSR)."""
from flask import current_app, flash, jsonify, redirect, request, url_for


def wants_json():
    """Xác định request yêu cầu phản hồi JSON (endpoint /api/* hoặc Accept/Content-Type JSON)."""
    if request.path.startswith("/api/") or request.is_json:
        return True
    accept = request.headers.get("Accept", "")
    return "application/json" in accept and "text/html" not in accept


def get_payload():
    """Đọc dữ liệu đầu vào từ JSON body hoặc HTML form."""
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form


def validation_error_response(exc, fallback_endpoint):
    """Trả về lỗi nghiệp vụ/phân quyền theo chuẩn JSON hoặc redirect kèm flash."""
    if wants_json():
        return jsonify(error=exc.message, fields=exc.fields), exc.status_code
    if exc.status_code == 403:
        return exc.message, 403
    flash(exc.message, "error")
    return redirect(request.referrer or url_for(fallback_endpoint))


def internal_error_response(exc, fallback_endpoint):
    """Ghi log lỗi nội bộ ở server và trả thông báo an toàn, không lộ chi tiết kỹ thuật."""
    current_app.logger.exception("Unhandled error in route %s", request.path, exc_info=exc)
    safe_msg = "Đã xảy ra lỗi hệ thống, vui lòng thử lại sau."
    if wants_json():
        return jsonify(error=safe_msg), 500
    flash(safe_msg, "error")
    return redirect(request.referrer or url_for(fallback_endpoint))

