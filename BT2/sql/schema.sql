CREATE DATABASE IF NOT EXISTS warranty_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE warranty_db;

CREATE TABLE employee (
    employee_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(120) NOT NULL,
    role VARCHAR(30) NOT NULL,
    phone VARCHAR(20),
    is_active BOOLEAN NOT NULL,
    username VARCHAR(50) NULL UNIQUE,
    password_hash VARCHAR(255) NULL
);

CREATE TABLE customer (
    customer_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(120) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(120),
    segment VARCHAR(30),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE device (
    device_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    customer_id BIGINT NOT NULL,
    serial_no VARCHAR(60) NOT NULL UNIQUE,
    model_name VARCHAR(120) NOT NULL,
    purchase_date DATE,
    warranty_months INT,

    FOREIGN KEY (customer_id)
        REFERENCES customer(customer_id)
);

CREATE TABLE technician (
    technician_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    employee_id BIGINT NOT NULL UNIQUE,
    center_id BIGINT NOT NULL,
    is_active BOOLEAN NOT NULL,
    FOREIGN KEY (employee_id)
        REFERENCES employee(employee_id)
);

CREATE TABLE ticket (
    ticket_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ticket_code VARCHAR(20) NOT NULL UNIQUE,

    customer_id BIGINT NOT NULL,
    device_id BIGINT NOT NULL,
    technician_id BIGINT NULL,

    received_by_employee_id BIGINT NOT NULL,

    issue_category VARCHAR(50) NOT NULL,

    priority VARCHAR(20) NOT NULL
        CHECK (priority IN ('CAO', 'TRUNG_BINH', 'THAP')),

    ticket_status VARCHAR(30) NOT NULL
        CHECK (
            ticket_status IN (
                'MOI',
                'DA_PHAN_CONG',
                'DANG_XU_LY',
                'CHO_LINH_KIEN',
                'HOAN_TAT',
                'DA_DONG'
            )
        ),

    issue_desc TEXT NOT NULL,

    received_at TIMESTAMP NOT NULL,
    due_date TIMESTAMP NOT NULL,
    closed_at TIMESTAMP NULL,

    FOREIGN KEY (customer_id)
        REFERENCES customer(customer_id),

    FOREIGN KEY (device_id)
        REFERENCES device(device_id),

    FOREIGN KEY (technician_id)
        REFERENCES technician(technician_id),

    FOREIGN KEY (received_by_employee_id)
        REFERENCES employee(employee_id)
);

CREATE TABLE ticket_status_log (
    log_id BIGINT PRIMARY KEY AUTO_INCREMENT,

    ticket_id BIGINT NOT NULL,

    from_status VARCHAR(30),

    to_status VARCHAR(30) NOT NULL,

    changed_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    changed_by_employee_id BIGINT NOT NULL,

    FOREIGN KEY (ticket_id)
        REFERENCES ticket(ticket_id),

    FOREIGN KEY (changed_by_employee_id)
        REFERENCES employee(employee_id)
);

CREATE INDEX idx_ticket_status_due
    ON ticket(ticket_status, due_date);

CREATE INDEX idx_ticket_tech_due
    ON ticket(technician_id, due_date);

CREATE INDEX idx_customer_phone
    ON customer(phone);

CREATE INDEX idx_log_ticket
    ON ticket_status_log(ticket_id, changed_at);