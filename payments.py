
from database import get_connection
from datetime import datetime


def record_payment(
    tenant_id,
    amount,
    payment_date,
    rent_month,
    method="M-Pesa",
    reference=None,
):
    """Record a rent payment for an existing tenant."""

    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    if not rent_month:
        raise ValueError("Rent month is required.")

    try:
        datetime.strptime(payment_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise ValueError("Payment date must use YYYY-MM-DD format.")

    try:
        datetime.strptime(rent_month, "%Y-%m")
    except (ValueError, TypeError):
        raise ValueError("Rent month must use YYYY-MM format, e.g. 2026-10.")

    if not method or not method.strip():
        raise ValueError("Payment method is required.")

    connection = get_connection()

    try:
        tenant = connection.execute(
            """
            SELECT id, property_id, status
            FROM tenants
            WHERE id = ?
            """,
            (tenant_id,),
        ).fetchone()

        if tenant is None:
            raise ValueError("Tenant was not found.")

        if tenant["status"] != "Active":
            raise ValueError("Cannot record rent for an inactive tenant.")

        cursor = connection.execute(
            """
            INSERT INTO rent_payments (
                tenant_id,
                property_id,
                amount,
                payment_date,
                rent_month,
                method,
                reference
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
                tenant["property_id"],
                amount,
                payment_date,
                rent_month,
                method.strip(),
                reference.strip() if reference and reference.strip() else None,
            ),
        )

        connection.commit()
        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_all_payments():
    """Return all payments with tenant and property details."""

    connection = get_connection()

    try:
        return connection.execute(
            """
            SELECT
                rp.id,
                rp.tenant_id,
                t.full_name AS tenant_name,
                rp.property_id,
                p.name AS property_name,
                p.unit_number,
                rp.amount,
                rp.payment_date,
                rp.rent_month,
                rp.method,
                rp.reference,
                rp.recorded_at
            FROM rent_payments rp
            JOIN tenants t ON t.id = rp.tenant_id
            JOIN properties p ON p.id = rp.property_id
            ORDER BY rp.payment_date DESC, rp.id DESC
            """
        ).fetchall()
    finally:
        connection.close()


def get_payments_by_tenant(tenant_id):
    """Return payment history for one tenant."""

    connection = get_connection()

    try:
        return connection.execute(
            """
            SELECT
                id,
                tenant_id,
                property_id,
                amount,
                payment_date,
                rent_month,
                method,
                reference,
                recorded_at
            FROM rent_payments
            WHERE tenant_id = ?
            ORDER BY payment_date DESC, id DESC
            """,
            (tenant_id,),
        ).fetchall()
    finally:
        connection.close()


def get_payments_by_month(rent_month):
    """Return payments for a month in YYYY-MM format."""

    try:
        datetime.strptime(rent_month, "%Y-%m")
    except (ValueError, TypeError):
        raise ValueError("Rent month must use YYYY-MM format.")

    connection = get_connection()

    try:
        return connection.execute(
            """
            SELECT
                rp.id,
                t.full_name AS tenant_name,
                p.name AS property_name,
                p.unit_number,
                rp.amount,
                rp.payment_date,
                rp.rent_month,
                rp.method,
                rp.reference
            FROM rent_payments rp
            JOIN tenants t ON t.id = rp.tenant_id
            JOIN properties p ON p.id = rp.property_id
            WHERE rp.rent_month = ?
            ORDER BY rp.payment_date DESC, rp.id DESC
            """,
            (rent_month,),
        ).fetchall()
    finally:
        connection.close()


def get_total_collected(rent_month=None):
    """Return the total amount collected, optionally for one rent month."""

    connection = get_connection()

    try:
        if rent_month is None:
            row = connection.execute(
                "SELECT COALESCE(SUM(amount), 0) AS total FROM rent_payments"
            ).fetchone()
        else:
            try:
                datetime.strptime(rent_month, "%Y-%m")
            except (ValueError, TypeError):
                raise ValueError("Rent month must use YYYY-MM format.")

            row = connection.execute(
                """
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM rent_payments
                WHERE rent_month = ?
                """,
                (rent_month,),
            ).fetchone()

        return row["total"]
    finally:
        connection.close()
