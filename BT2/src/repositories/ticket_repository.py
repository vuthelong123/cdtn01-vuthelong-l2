"""Tầng truy cập dữ liệu (Repository Layer) cho hệ thống bảo hành."""
from . import db_connection as db


class MySQLTicketRepository:
    """Hiện thực kho dữ liệu trên cơ sở dữ liệu MySQL thật."""

    def find_customer_by_phone(self, phone):
        return db.query("SELECT customer_id FROM customer WHERE phone = %s", (phone,), one=True)

    def add_customer(self, full_name, phone):
        return db.execute("INSERT INTO customer (full_name, phone) VALUES (%s, %s)", (full_name, phone))

    def find_device_by_serial(self, serial_no):
        return db.query("SELECT device_id, customer_id FROM device WHERE serial_no = %s", (serial_no,), one=True)

    def add_device(self, customer_id, serial_no, model_name, purchase_date, warranty_months):
        return db.execute(
            "INSERT INTO device (customer_id, serial_no, model_name, purchase_date, warranty_months) "
            "VALUES (%s, %s, %s, %s, %s)",
            (customer_id, serial_no, model_name, purchase_date, warranty_months),
        )

    def add_ticket(
        self,
        ticket_code,
        customer_id,
        device_id,
        received_by_employee_id,
        issue_category,
        priority,
        ticket_status,
        issue_desc,
        received_at,
        due_date,
    ):
        return db.execute(
            "INSERT INTO ticket (ticket_code, customer_id, device_id, received_by_employee_id, issue_category, "
            "priority, ticket_status, issue_desc, received_at, due_date) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                ticket_code,
                customer_id,
                device_id,
                received_by_employee_id,
                issue_category,
                priority,
                ticket_status,
                issue_desc,
                received_at,
                due_date,
            ),
        )

    def set_ticket_code(self, ticket_id, ticket_code):
        db.execute("UPDATE ticket SET ticket_code = %s WHERE ticket_id = %s", (ticket_code, ticket_id))

    def add_status_log(self, ticket_id, from_status, to_status, employee_id):
        db.execute(
            "INSERT INTO ticket_status_log (ticket_id, from_status, to_status, changed_by_employee_id) "
            "VALUES (%s, %s, %s, %s)",
            (ticket_id, from_status, to_status, employee_id),
        )

    def find_tickets(self, where="", args=(), limit=200):
        sql = """
            SELECT t.*, c.full_name AS customer_name, c.phone AS customer_phone,
                   d.serial_no, d.model_name, d.purchase_date, d.warranty_months,
                   e.full_name AS tech_name
            FROM ticket t
            JOIN customer c ON c.customer_id = t.customer_id
            JOIN device d ON d.device_id = t.device_id
            LEFT JOIN technician tc ON tc.technician_id = t.technician_id
            LEFT JOIN employee e ON e.employee_id = tc.employee_id
        """
        if where:
            sql += f" WHERE {where}"
        sql += " ORDER BY t.received_at DESC LIMIT %s"
        return db.query(sql, tuple(args) + (limit,))

    def get_status_counts(self):
        rows = db.query("SELECT ticket_status, COUNT(*) AS n FROM ticket GROUP BY ticket_status")
        return {r["ticket_status"]: r["n"] for r in rows}

    def get_active_technicians(self):
        return db.query(
            "SELECT tc.technician_id, e.full_name, "
            "(SELECT COUNT(*) FROM ticket x WHERE x.technician_id = tc.technician_id "
            " AND x.ticket_status NOT IN ('HOAN_TAT','DA_DONG')) AS open_tickets "
            "FROM technician tc JOIN employee e ON e.employee_id = tc.employee_id "
            "WHERE tc.is_active = 1 AND e.is_active = 1 ORDER BY e.full_name"
        )

    def find_active_technician(self, tech_id):
        return db.query(
            "SELECT tc.technician_id, e.full_name "
            "FROM technician tc JOIN employee e ON e.employee_id = tc.employee_id "
            "WHERE tc.technician_id = %s AND tc.is_active = 1 AND e.is_active = 1",
            (tech_id,),
            one=True,
        )

    def get_ticket_for_update(self, ticket_id):
        return db.query("SELECT * FROM ticket WHERE ticket_id = %s FOR UPDATE", (ticket_id,), one=True)

    def update_ticket_classification(self, ticket_id, category, priority, due_date):
        db.execute(
            "UPDATE ticket SET issue_category = %s, priority = %s, due_date = %s WHERE ticket_id = %s",
            (category, priority, due_date, ticket_id),
        )

    def assign_technician(self, ticket_id, tech_id):
        db.execute(
            "UPDATE ticket SET technician_id = %s, ticket_status = 'DA_PHAN_CONG' WHERE ticket_id = %s",
            (tech_id, ticket_id),
        )

    def close_ticket(self, ticket_id, closed_at):
        db.execute(
            "UPDATE ticket SET ticket_status = 'DA_DONG', closed_at = %s WHERE ticket_id = %s",
            (closed_at, ticket_id),
        )

    def update_ticket_status(self, ticket_id, new_status):
        db.execute("UPDATE ticket SET ticket_status = %s WHERE ticket_id = %s", (new_status, ticket_id))

    def update_ticket_desc(self, ticket_id, issue_desc):
        db.execute("UPDATE ticket SET issue_desc = %s WHERE ticket_id = %s", (issue_desc, ticket_id))

    def admin_update_ticket(
        self, ticket_id, issue_category, priority, due_date, issue_desc, ticket_status, technician_id, closed_at=None
    ):
        db.execute(
            "UPDATE ticket SET issue_category = %s, priority = %s, due_date = %s, "
            "issue_desc = %s, ticket_status = %s, technician_id = %s, closed_at = %s "
            "WHERE ticket_id = %s",
            (issue_category, priority, due_date, issue_desc, ticket_status, technician_id, closed_at, ticket_id),
        )

    def commit(self):
        db.get_db().commit()

    def rollback(self):
        db.get_db().rollback()
