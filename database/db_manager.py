from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from paths import database_path

DB_PATH = database_path()
GST_RATE = 5.0
VALID_ORDER_TRANSITIONS = {
    "Pending": {"Preparing", "Ready", "Cancelled"},
    "Preparing": {"Ready", "Served", "Cancelled"},
    "Ready": {"Served", "Completed", "Cancelled"},
    "Served": {"Completed"},
    "Completed": set(),
    "Cancelled": set(),
}


class DatabaseManager:
    def __init__(self, db_path: Path | None = None):
        self.db_path = Path(db_path or DB_PATH)
        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    mobile TEXT NOT NULL UNIQUE,
                    dob TEXT NOT NULL,
                    password_hash TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS menu_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock_qty INTEGER NOT NULL,
                    reorder_level INTEGER NOT NULL DEFAULT 5,
                    is_stock_tracked INTEGER NOT NULL DEFAULT 1,
                    is_active INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS offers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    discount_type TEXT NOT NULL,
                    discount_value REAL NOT NULL,
                    min_order_amount REAL NOT NULL DEFAULT 0,
                    is_active INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    mobile TEXT NOT NULL UNIQUE,
                    email TEXT DEFAULT '',
                    address TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sales_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_number TEXT NOT NULL UNIQUE,
                    customer_id INTEGER,
                    customer_name TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    staff_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    subtotal REAL NOT NULL,
                    offer_id INTEGER,
                    offer_name TEXT,
                    discount_amount REAL NOT NULL DEFAULT 0,
                    tax_amount REAL NOT NULL DEFAULT 0,
                    total_amount REAL NOT NULL,
                    payment_status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (staff_id) REFERENCES users(id),
                    FOREIGN KEY (offer_id) REFERENCES offers(id)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    menu_item_id INTEGER NOT NULL,
                    item_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    line_total REAL NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES sales_orders(id),
                    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    method TEXT NOT NULL,
                    amount REAL NOT NULL,
                    discount_amount REAL NOT NULL DEFAULT 0,
                    offer_name TEXT,
                    payment_status TEXT NOT NULL,
                    paid_at TEXT NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES sales_orders(id)
                )
                """
            )
            connection.commit()
            self._migrate_schema(connection)
            self._seed_users(connection)
            self._seed_menu_items(connection)
            self._seed_offers(connection)
            self._seed_customers(connection)
            self._seed_orders(connection)
            self._backfill_order_customer_links(connection)
            self._recalculate_tax_fields(connection)

    @staticmethod
    def _column_names(connection: sqlite3.Connection, table_name: str) -> set[str]:
        return {row["name"] for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()}

    def _migrate_schema(self, connection: sqlite3.Connection) -> None:
        columns = self._column_names(connection, "sales_orders")
        if "customer_id" not in columns:
            connection.execute("ALTER TABLE sales_orders ADD COLUMN customer_id INTEGER")
        if "tax_amount" not in columns:
            connection.execute("ALTER TABLE sales_orders ADD COLUMN tax_amount REAL NOT NULL DEFAULT 0")
        menu_columns = self._column_names(connection, "menu_items")
        if "is_stock_tracked" not in menu_columns:
            connection.execute("ALTER TABLE menu_items ADD COLUMN is_stock_tracked INTEGER NOT NULL DEFAULT 1")
            stock_tracked_items = {"Cold Coffee", "Masala Soda", "Brownie"}
            placeholders = ",".join("?" for _ in stock_tracked_items)
            connection.execute(
                f"UPDATE menu_items SET is_stock_tracked = CASE WHEN name IN ({placeholders}) THEN 1 ELSE 0 END",
                tuple(stock_tracked_items),
            )
            connection.execute("UPDATE menu_items SET stock_qty = 0, reorder_level = 0 WHERE is_stock_tracked = 0")
        connection.commit()

    def _backfill_order_customer_links(self, connection: sqlite3.Connection) -> None:
        customer_rows = connection.execute("SELECT id, full_name FROM customers").fetchall()
        customer_map = {str(row["full_name"]).strip().lower(): int(row["id"]) for row in customer_rows}
        order_rows = connection.execute(
            """
            SELECT id, customer_name
            FROM sales_orders
            WHERE customer_id IS NULL AND customer_name IS NOT NULL AND TRIM(customer_name) != '' AND customer_name != 'Walk-in'
            """
        ).fetchall()
        for row in order_rows:
            customer_id = customer_map.get(str(row["customer_name"]).strip().lower())
            if customer_id:
                connection.execute(
                    "UPDATE sales_orders SET customer_id = ? WHERE id = ?",
                    (customer_id, int(row["id"])),
                )
        connection.commit()

    def _recalculate_tax_fields(self, connection: sqlite3.Connection) -> None:
        rows = connection.execute(
            "SELECT id, subtotal, discount_amount FROM sales_orders"
        ).fetchall()
        for row in rows:
            totals = self._calculate_order_totals(float(row["subtotal"]), None, float(row["discount_amount"]))
            connection.execute(
                "UPDATE sales_orders SET tax_amount = ?, total_amount = ? WHERE id = ?",
                (totals["tax_amount"], totals["grand_total"], int(row["id"])),
            )
        connection.execute(
            """
            UPDATE payments
            SET amount = COALESCE(
                (SELECT total_amount FROM sales_orders WHERE sales_orders.id = payments.order_id),
                amount
            )
            """
        )
        connection.commit()

    def _seed_users(self, connection: sqlite3.Connection) -> None:
        users = [
            ("admin", "Breaktime Admin", "Administrator", "9876543210", "1995-06-15", self._hash_password("123")),
            ("manager", "Riya Sharma", "Manager", "9123456780", "1994-11-08", self._hash_password("manager123")),
            ("cashier", "Aman Verma", "Cashier", "9012345678", "1998-02-19", self._hash_password("cash123")),
            ("captain", "Neha Kapoor", "Captain", "9988776655", "1997-03-11", self._hash_password("captain123")),
            ("reception", "Priya Malhotra", "Receptionist", "9090909090", "1999-07-21", self._hash_password("recep123")),
        ]
        connection.executemany(
            """
            INSERT OR IGNORE INTO users (username, full_name, role, mobile, dob, password_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            users,
        )
        connection.commit()

    def _seed_menu_items(self, connection: sqlite3.Connection) -> None:
        existing = connection.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0]
        if existing:
            return

        items = [
            ("Paneer Tikka", "Starter", 180.0, 0, 0, 0, 1),
            ("Butter Naan", "Bread", 45.0, 0, 0, 0, 1),
            ("Pasta Alfredo", "Main Course", 240.0, 0, 0, 0, 1),
            ("Garlic Bread", "Starter", 120.0, 0, 0, 0, 1),
            ("Burger Combo", "Fast Food", 210.0, 0, 0, 0, 1),
            ("Cold Coffee", "Beverage", 95.0, 30, 8, 1, 1),
            ("Paneer Tikka Pizza", "Pizza", 320.0, 0, 0, 0, 1),
            ("Family Thali", "Main Course", 420.0, 0, 0, 0, 1),
            ("Masala Soda", "Beverage", 60.0, 40, 10, 1, 1),
            ("Dal Makhani", "Main Course", 220.0, 0, 0, 0, 1),
            ("Jeera Rice", "Main Course", 160.0, 0, 0, 0, 1),
            ("Brownie", "Dessert", 110.0, 12, 4, 1, 1),
        ]
        connection.executemany(
            """
            INSERT INTO menu_items (name, category, price, stock_qty, reorder_level, is_stock_tracked, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            items,
        )
        connection.commit()

    def _seed_customers(self, connection: sqlite3.Connection) -> None:
        existing = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        if existing:
            return

        customers = [
            ("Aarav Mehta", "9811111111", "aarav@example.com", "Sector 18"),
            ("Riya Singh", "9822222222", "riya@example.com", "Civil Lines"),
            ("Kabir Khan", "9833333333", "kabir@example.com", "Model Town"),
            ("Meera Joshi", "9844444444", "meera@example.com", "MG Road"),
        ]
        connection.executemany(
            """
            INSERT INTO customers (full_name, mobile, email, address, created_at)
            VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
            """,
            customers,
        )
        connection.commit()

    def _seed_offers(self, connection: sqlite3.Connection) -> None:
        existing = connection.execute("SELECT COUNT(*) FROM offers").fetchone()[0]
        if existing:
            return

        offers = [
            ("Lunch Saver 10%", "percent", 10.0, 300.0, 1),
            ("Flat 80 Off", "flat", 80.0, 500.0, 1),
            ("Happy Hours 15%", "percent", 15.0, 250.0, 1),
        ]
        connection.executemany(
            """
            INSERT INTO offers (name, discount_type, discount_value, min_order_amount, is_active)
            VALUES (?, ?, ?, ?, ?)
            """,
            offers,
        )
        connection.commit()

    def _seed_orders(self, connection: sqlite3.Connection) -> None:
        existing = connection.execute("SELECT COUNT(*) FROM sales_orders").fetchone()[0]
        if existing:
            return

        menu_map = {
            row["name"]: dict(row)
            for row in connection.execute("SELECT id, name, price, stock_qty, is_stock_tracked FROM menu_items").fetchall()
        }
        user_map = {
            row["username"]: row["id"]
            for row in connection.execute("SELECT id, username FROM users").fetchall()
        }
        customer_map = {
            row["full_name"]: row["id"]
            for row in connection.execute("SELECT id, full_name FROM customers").fetchall()
        }
        offer_map = {
            row["name"]: dict(row)
            for row in connection.execute("SELECT id, name, discount_type, discount_value, min_order_amount FROM offers").fetchall()
        }

        seed_orders = [
            {
                "customer": "Aarav Mehta",
                "table": "T-05",
                "order_type": "Dine In",
                "staff_username": "manager",
                "status": "Completed",
                "payment_status": "Paid",
                "created_at": "2026-03-28 13:05:00",
                "offer": "Lunch Saver 10%",
                "payment_method": "Cash",
                "items": {"Paneer Tikka": 1, "Butter Naan": 3},
            },
            {
                "customer": "Riya Singh",
                "table": "T-03",
                "order_type": "Dine In",
                "staff_username": "captain",
                "status": "Preparing",
                "payment_status": "Unpaid",
                "created_at": "2026-04-01 19:02:00",
                "offer": None,
                "payment_method": None,
                "items": {"Pasta Alfredo": 1, "Garlic Bread": 1, "Cold Coffee": 2},
            },
            {
                "customer": "Walk-in",
                "table": "Takeaway",
                "order_type": "Takeaway",
                "staff_username": "cashier",
                "status": "Ready",
                "payment_status": "Pending",
                "created_at": "2026-04-01 18:31:00",
                "offer": "Happy Hours 15%",
                "payment_method": None,
                "items": {"Burger Combo": 1, "Cold Coffee": 1},
            },
            {
                "customer": "Kabir Khan",
                "table": "T-11",
                "order_type": "Dine In",
                "staff_username": "manager",
                "status": "Served",
                "payment_status": "Paid",
                "created_at": "2026-04-01 18:48:00",
                "offer": "Flat 80 Off",
                "payment_method": "Card",
                "items": {"Family Thali": 1, "Masala Soda": 2},
            },
            {
                "customer": "Meera Joshi",
                "table": "T-04",
                "order_type": "Dine In",
                "staff_username": "captain",
                "status": "Pending",
                "payment_status": "Unpaid",
                "created_at": "2026-04-01 20:10:00",
                "offer": None,
                "payment_method": None,
                "items": {"Dal Makhani": 1, "Jeera Rice": 1, "Butter Naan": 2},
            },
        ]

        for order_index, seed in enumerate(seed_orders, start=1):
            subtotal = 0.0
            order_lines = []
            for item_name, quantity in seed["items"].items():
                menu_item = menu_map[item_name]
                line_total = menu_item["price"] * quantity
                subtotal += line_total
                order_lines.append((menu_item["id"], item_name, quantity, menu_item["price"], line_total))
                if int(menu_item["is_stock_tracked"]) == 1:
                    connection.execute(
                        "UPDATE menu_items SET stock_qty = stock_qty - ? WHERE id = ?",
                        (quantity, menu_item["id"]),
                    )

            offer_row = offer_map.get(seed["offer"]) if seed["offer"] else None
            totals = self._calculate_order_totals(subtotal, offer_row)
            order_number = f"ORD-{1000 + order_index}"

            cursor = connection.execute(
                """
                INSERT INTO sales_orders (
                    order_number, customer_id, customer_name, table_name, order_type, staff_id, status,
                    subtotal, offer_id, offer_name, discount_amount, tax_amount, total_amount, payment_status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_number,
                    customer_map.get(seed["customer"]),
                    seed["customer"],
                    seed["table"],
                    seed["order_type"],
                    user_map.get(seed["staff_username"], user_map.get("manager", user_map.get("admin"))),
                    seed["status"],
                    subtotal,
                    offer_row["id"] if offer_row else None,
                    offer_row["name"] if offer_row else None,
                    totals["discount_amount"],
                    totals["tax_amount"],
                    totals["grand_total"],
                    seed["payment_status"],
                    seed["created_at"],
                ),
            )
            order_id = cursor.lastrowid

            connection.executemany(
                """
                INSERT INTO order_items (order_id, menu_item_id, item_name, quantity, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (order_id, menu_item_id, item_name, quantity, unit_price, line_total)
                    for menu_item_id, item_name, quantity, unit_price, line_total in order_lines
                ],
            )

            if seed["payment_method"]:
                connection.execute(
                    """
                    INSERT INTO payments (order_id, method, amount, discount_amount, offer_name, payment_status, paid_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        seed["payment_method"],
                        totals["grand_total"],
                        totals["discount_amount"],
                        offer_row["name"] if offer_row else None,
                        "Paid",
                        seed["created_at"],
                    ),
                )

        connection.commit()

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def _calculate_discount(subtotal: float, offer_row: dict | sqlite3.Row | None) -> float:
        if not offer_row:
            return 0.0
        minimum = float(offer_row["min_order_amount"])
        if subtotal < minimum:
            return 0.0
        if offer_row["discount_type"] == "percent":
            return round(subtotal * (float(offer_row["discount_value"]) / 100.0), 2)
        return min(round(float(offer_row["discount_value"]), 2), round(subtotal, 2))

    @staticmethod
    def _calculate_tax_amount(taxable_amount: float) -> float:
        return round(max(float(taxable_amount), 0.0) * (GST_RATE / 100.0), 2)

    @classmethod
    def _calculate_order_totals(
        cls,
        subtotal: float,
        offer_row: dict | sqlite3.Row | None,
        discount_override: float | None = None,
    ) -> dict:
        discount_amount = cls._calculate_discount(subtotal, offer_row) if discount_override is None else round(float(discount_override), 2)
        taxable_amount = max(round(float(subtotal) - discount_amount, 2), 0.0)
        tax_amount = cls._calculate_tax_amount(taxable_amount)
        grand_total = round(taxable_amount + tax_amount, 2)
        return {
            "discount_amount": round(discount_amount, 2),
            "taxable_amount": taxable_amount,
            "tax_amount": tax_amount,
            "grand_total": grand_total,
        }

    def _upsert_customer(
        self,
        connection: sqlite3.Connection,
        full_name: str,
        mobile: str,
        email: str = "",
        address: str = "",
    ) -> dict:
        cleaned_name = full_name.strip()
        cleaned_mobile = mobile.strip()
        cleaned_email = email.strip()
        cleaned_address = address.strip()
        existing = connection.execute(
            """
            SELECT id, full_name, mobile, email, address
            FROM customers
            WHERE mobile = ?
            """,
            (cleaned_mobile,),
        ).fetchone()
        if existing:
            connection.execute(
                """
                UPDATE customers
                SET full_name = ?, email = ?, address = ?
                WHERE id = ?
                """,
                (cleaned_name or existing["full_name"], cleaned_email, cleaned_address, int(existing["id"])),
            )
            row = connection.execute(
                "SELECT id, full_name, mobile, email, address FROM customers WHERE id = ?",
                (int(existing["id"]),),
            ).fetchone()
            return dict(row)

        cursor = connection.execute(
            """
            INSERT INTO customers (full_name, mobile, email, address, created_at)
            VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
            """,
            (cleaned_name, cleaned_mobile, cleaned_email, cleaned_address),
        )
        row = connection.execute(
            "SELECT id, full_name, mobile, email, address FROM customers WHERE id = ?",
            (int(cursor.lastrowid),),
        ).fetchone()
        return dict(row)
    def authenticate_user(self, username: str, password: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, username, full_name, role
                FROM users
                WHERE LOWER(username) = LOWER(?)
                AND password_hash = ?
                """,
                (username.strip(), self._hash_password(password)),
            ).fetchone()
        return dict(row) if row else None

    def find_user_for_password_reset(self, mobile: str, dob: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, username, full_name
                FROM users
                WHERE mobile = ? AND dob = ?
                """,
                (mobile.strip(), dob),
            ).fetchone()
        return dict(row) if row else None

    def update_password(self, user_id: int, password: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (self._hash_password(password), int(user_id)),
            )
            connection.commit()

    def get_all_users(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, username, full_name, role, mobile, dob
                FROM users
                ORDER BY full_name
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_all_customers(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, full_name, mobile, email, address, created_at
                FROM customers
                ORDER BY datetime(created_at) DESC, full_name
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def add_customer(self, full_name: str, mobile: str, email: str = "", address: str = "") -> None:
        with self._connect() as connection:
            self._upsert_customer(connection, full_name, mobile, email, address)
            connection.commit()

    def delete_customer(self, customer_id: int) -> None:
        with self._connect() as connection:
            linked_orders = connection.execute(
                "SELECT COUNT(*) FROM sales_orders WHERE customer_id = ?",
                (int(customer_id),),
            ).fetchone()[0]
            if int(linked_orders or 0) > 0:
                raise ValueError("This customer is linked to existing orders and cannot be deleted.")
            connection.execute(
                "DELETE FROM customers WHERE id = ?",
                (int(customer_id),),
            )
            connection.commit()

    def get_customer_by_id(self, customer_id: int) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, full_name, mobile, email, address, created_at
                FROM customers
                WHERE id = ?
                """,
                (int(customer_id),),
            ).fetchone()
        return dict(row) if row else None

    def get_menu_items(self, include_inactive: bool = True) -> list[dict]:
        query = "SELECT id, name, category, price, stock_qty, reorder_level, is_stock_tracked, is_active FROM menu_items"
        if not include_inactive:
            query += " WHERE is_active = 1"
        query += " ORDER BY category, name"
        with self._connect() as connection:
            rows = connection.execute(query).fetchall()
        return [dict(row) for row in rows]

    def add_menu_item(self, name: str, category: str, price: float, stock_qty: int, reorder_level: int, is_stock_tracked: bool) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO menu_items (name, category, price, stock_qty, reorder_level, is_stock_tracked, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    name.strip(),
                    category.strip(),
                    float(price),
                    int(stock_qty) if is_stock_tracked else 0,
                    int(reorder_level) if is_stock_tracked else 0,
                    1 if is_stock_tracked else 0,
                ),
            )
            connection.commit()

    def update_menu_item(self, item_id: int, name: str, category: str, price: float, reorder_level: int, is_stock_tracked: bool) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE menu_items
                SET name = ?, category = ?, price = ?, reorder_level = ?, is_stock_tracked = ?
                WHERE id = ?
                """,
                (
                    name.strip(),
                    category.strip(),
                    float(price),
                    int(reorder_level) if is_stock_tracked else 0,
                    1 if is_stock_tracked else 0,
                    int(item_id),
                ),
            )
            if not is_stock_tracked:
                connection.execute("UPDATE menu_items SET stock_qty = 0 WHERE id = ?", (int(item_id),))
            connection.commit()

    def add_user(self, username: str, full_name: str, password: str, role: str, mobile: str, dob: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO users (username, full_name, password_hash, role, mobile, dob)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    username.strip(),
                    full_name.strip(),
                    self._hash_password(password),
                    role.strip(),
                    mobile.strip(),
                    dob.strip(),
                ),
            )
            connection.commit()

    def update_user(
        self,
        user_id: int,
        username: str,
        full_name: str,
        role: str,
        mobile: str,
        dob: str,
        password: str = "",
    ) -> None:
        with self._connect() as connection:
            if password.strip():
                connection.execute(
                    """
                    UPDATE users
                    SET username = ?, full_name = ?, role = ?, mobile = ?, dob = ?, password_hash = ?
                    WHERE id = ?
                    """,
                    (
                        username.strip(),
                        full_name.strip(),
                        role.strip(),
                        mobile.strip(),
                        dob.strip(),
                        self._hash_password(password),
                        int(user_id),
                    ),
                )
            else:
                connection.execute(
                    """
                    UPDATE users
                    SET username = ?, full_name = ?, role = ?, mobile = ?, dob = ?
                    WHERE id = ?
                    """,
                    (
                        username.strip(),
                        full_name.strip(),
                        role.strip(),
                        mobile.strip(),
                        dob.strip(),
                        int(user_id),
                    ),
                )
            connection.commit()

    def update_menu_stock(self, item_id: int, stock_qty: int) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE menu_items SET stock_qty = ? WHERE id = ?",
                (int(stock_qty), int(item_id)),
            )
            connection.commit()

    def toggle_menu_item(self, item_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE menu_items
                SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END
                WHERE id = ?
                """,
                (int(item_id),),
            )
            connection.commit()

    def get_offers(self, include_inactive: bool = True) -> list[dict]:
        query = "SELECT id, name, discount_type, discount_value, min_order_amount, is_active FROM offers"
        if not include_inactive:
            query += " WHERE is_active = 1"
        query += " ORDER BY name"
        with self._connect() as connection:
            rows = connection.execute(query).fetchall()
        return [dict(row) for row in rows]

    def add_offer(self, name: str, discount_type: str, discount_value: float, min_order_amount: float) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO offers (name, discount_type, discount_value, min_order_amount, is_active)
                VALUES (?, ?, ?, ?, 1)
                """,
                (name.strip(), discount_type, float(discount_value), float(min_order_amount)),
            )
            connection.commit()

    def update_offer(self, offer_id: int, name: str, discount_type: str, discount_value: float, min_order_amount: float) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE offers
                SET name = ?, discount_type = ?, discount_value = ?, min_order_amount = ?
                WHERE id = ?
                """,
                (name.strip(), discount_type, float(discount_value), float(min_order_amount), int(offer_id)),
            )
            connection.commit()

    def toggle_offer(self, offer_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE offers
                SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END
                WHERE id = ?
                """,
                (int(offer_id),),
            )
            connection.commit()

    def _next_order_number(self, connection: sqlite3.Connection) -> str:
        max_id = connection.execute("SELECT COALESCE(MAX(id), 0) FROM sales_orders").fetchone()[0]
        return f"ORD-{1000 + max_id + 1}"

    def create_order(
        self,
        customer_name: str,
        table_name: str,
        order_type: str,
        staff_id: int,
        items: list[dict],
        offer_id: int | None = None,
        customer_id: int | None = None,
        customer_mobile: str = "",
        customer_email: str = "",
        customer_address: str = "",
        save_customer: bool = False,
    ) -> int:
        if not items:
            raise ValueError("At least one item is required to create an order.")

        with self._connect() as connection:
            resolved_customer_id = int(customer_id) if customer_id else None
            resolved_customer_name = customer_name.strip() or "Walk-in"
            if resolved_customer_id is not None:
                customer_row = connection.execute(
                    """
                    SELECT id, full_name
                    FROM customers
                    WHERE id = ?
                    """,
                    (resolved_customer_id,),
                ).fetchone()
                if not customer_row:
                    raise ValueError("Selected customer was not found.")
                resolved_customer_name = str(customer_row["full_name"]).strip()
            elif save_customer:
                if not customer_name.strip() or not customer_mobile.strip():
                    raise ValueError("New customers require at least name and mobile number.")
                customer_row = self._upsert_customer(
                    connection,
                    customer_name,
                    customer_mobile,
                    customer_email,
                    customer_address,
                )
                resolved_customer_id = int(customer_row["id"])
                resolved_customer_name = str(customer_row["full_name"]).strip()

            menu_ids = [int(item["menu_item_id"]) for item in items]
            placeholders = ",".join("?" for _ in menu_ids)
            menu_rows = connection.execute(
                f"SELECT id, name, price, stock_qty, reorder_level, is_stock_tracked, is_active FROM menu_items WHERE id IN ({placeholders})",
                menu_ids,
            ).fetchall()
            menu_map = {row["id"]: dict(row) for row in menu_rows}

            subtotal = 0.0
            order_lines = []
            for item in items:
                menu_item_id = int(item["menu_item_id"])
                quantity = int(item["quantity"])
                if quantity <= 0:
                    raise ValueError("Item quantity must be greater than zero.")

                menu_item = menu_map.get(menu_item_id)
                if not menu_item or int(menu_item["is_active"]) != 1:
                    raise ValueError("Selected menu item is unavailable.")
                if int(menu_item["is_stock_tracked"]) == 1 and int(menu_item["stock_qty"]) < quantity:
                    raise ValueError(f"Insufficient stock for {menu_item['name']}.")

                line_total = float(menu_item["price"]) * quantity
                subtotal += line_total
                order_lines.append((menu_item_id, menu_item["name"], quantity, float(menu_item["price"]), line_total))

            offer_row = None
            if offer_id:
                offer = connection.execute(
                    """
                    SELECT id, name, discount_type, discount_value, min_order_amount
                    FROM offers
                    WHERE id = ? AND is_active = 1
                    """,
                    (int(offer_id),),
                ).fetchone()
                offer_row = dict(offer) if offer else None

            totals = self._calculate_order_totals(subtotal, offer_row)
            order_number = self._next_order_number(connection)

            cursor = connection.execute(
                """
                INSERT INTO sales_orders (
                    order_number, customer_id, customer_name, table_name, order_type, staff_id, status,
                    subtotal, offer_id, offer_name, discount_amount, tax_amount, total_amount, payment_status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
                """,
                (
                    order_number,
                    resolved_customer_id,
                    resolved_customer_name,
                    table_name.strip() or "Takeaway",
                    order_type,
                    int(staff_id),
                    "Pending",
                    round(subtotal, 2),
                    offer_row["id"] if offer_row else None,
                    offer_row["name"] if offer_row else None,
                    totals["discount_amount"],
                    totals["tax_amount"],
                    totals["grand_total"],
                    "Unpaid",
                ),
            )
            order_id = cursor.lastrowid

            connection.executemany(
                """
                INSERT INTO order_items (order_id, menu_item_id, item_name, quantity, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (order_id, menu_item_id, item_name, quantity, unit_price, line_total)
                    for menu_item_id, item_name, quantity, unit_price, line_total in order_lines
                ],
            )

            for menu_item_id, _, quantity, _, _ in order_lines:
                menu_item = menu_map.get(menu_item_id)
                if menu_item and int(menu_item["is_stock_tracked"]) == 1:
                    connection.execute(
                        "UPDATE menu_items SET stock_qty = stock_qty - ? WHERE id = ?",
                        (quantity, menu_item_id),
                    )

            connection.commit()
            return int(order_id)

    def update_order_status(self, order_id: int, status: str) -> None:
        with self._connect() as connection:
            order = connection.execute(
                "SELECT status, payment_status FROM sales_orders WHERE id = ?",
                (int(order_id),),
            ).fetchone()
            if not order:
                raise ValueError("Order not found.")

            current_status = order["status"]
            payment_status = order["payment_status"]
            if current_status == status:
                return
            if payment_status == "Paid" and status == "Cancelled":
                raise ValueError("A paid order cannot be cancelled.")
            if payment_status != "Paid" and status == "Served":
                raise ValueError("Payment must be completed before marking an order as served.")

            allowed_statuses = VALID_ORDER_TRANSITIONS.get(current_status, set())
            if status not in allowed_statuses:
                raise ValueError(f"Cannot change order from {current_status} to {status}.")

            final_status = status
            if status == "Served":
                final_status = "Completed"

            connection.execute("UPDATE sales_orders SET status = ? WHERE id = ?", (final_status, int(order_id)))
            connection.commit()

    def apply_offer_to_order(self, order_id: int, offer_id: int | None) -> None:
        with self._connect() as connection:
            order = connection.execute(
                "SELECT id, subtotal, payment_status FROM sales_orders WHERE id = ?",
                (int(order_id),),
            ).fetchone()
            if not order:
                raise ValueError("Order not found.")
            if order["payment_status"] == "Paid":
                raise ValueError("Cannot change offers after payment is completed.")

            offer_row = None
            if offer_id:
                offer = connection.execute(
                    """
                    SELECT id, name, discount_type, discount_value, min_order_amount
                    FROM offers
                    WHERE id = ? AND is_active = 1
                    """,
                    (int(offer_id),),
                ).fetchone()
                if not offer:
                    raise ValueError("Selected offer is unavailable.")
                offer_row = dict(offer)

            subtotal = float(order["subtotal"])
            totals = self._calculate_order_totals(subtotal, offer_row)
            connection.execute(
                """
                UPDATE sales_orders
                SET offer_id = ?, offer_name = ?, discount_amount = ?, tax_amount = ?, total_amount = ?
                WHERE id = ?
                """,
                (
                    offer_row["id"] if offer_row else None,
                    offer_row["name"] if offer_row else None,
                    totals["discount_amount"],
                    totals["tax_amount"],
                    totals["grand_total"],
                    int(order_id),
                ),
            )
            connection.commit()

    def record_payment(self, order_id: int, method: str) -> None:
        with self._connect() as connection:
            order = connection.execute(
                """
                SELECT id, total_amount, discount_amount, offer_name, payment_status, status
                FROM sales_orders
                WHERE id = ?
                """,
                (int(order_id),),
            ).fetchone()
            if not order:
                raise ValueError("Order not found.")
            if order["payment_status"] == "Paid":
                raise ValueError("Payment is already completed for this order.")
            if order["status"] == "Cancelled":
                raise ValueError("Cancelled orders cannot be paid.")

            connection.execute(
                """
                INSERT INTO payments (order_id, method, amount, discount_amount, offer_name, payment_status, paid_at)
                VALUES (?, ?, ?, ?, ?, 'Paid', datetime('now', 'localtime'))
                """,
                (
                    int(order_id),
                    method,
                    float(order["total_amount"]),
                    float(order["discount_amount"]),
                    order["offer_name"],
                ),
            )
            next_status = "Completed" if order["status"] in {"Ready", "Served"} else order["status"]
            connection.execute(
                "UPDATE sales_orders SET payment_status = 'Paid', status = ? WHERE id = ?",
                (next_status, int(order_id)),
            )
            connection.commit()

    def get_unpaid_orders(self) -> list[dict]:
        return [
            order
            for order in self.get_all_orders()
            if order["payment_status"] != "Paid" and order["status"] != "Cancelled"
        ]

    def get_active_orders(self) -> list[dict]:
        return [
            order
            for order in self.get_all_orders()
            if order["status"] not in {"Completed", "Cancelled"}
            and not (order["status"] == "Served" and order["payment_status"] == "Paid")
        ]

    def get_all_orders(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT so.id, so.order_number, so.customer_id, so.customer_name, so.table_name, so.order_type,
                       u.full_name AS staff_name, so.status, so.subtotal, so.offer_name,
                       so.discount_amount, so.tax_amount, so.total_amount, so.payment_status, so.created_at,
                       COALESCE(SUM(oi.quantity), 0) AS items_count
                FROM sales_orders so
                JOIN users u ON u.id = so.staff_id
                LEFT JOIN order_items oi ON oi.order_id = so.id
                GROUP BY so.id
                ORDER BY datetime(so.created_at) DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_order_items(self, order_id: int) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, item_name, quantity, unit_price, line_total
                FROM order_items
                WHERE order_id = ?
                ORDER BY id
                """,
                (int(order_id),),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_order_invoice(self, order_id: int) -> dict | None:
        with self._connect() as connection:
            order = connection.execute(
                """
                SELECT so.id, so.order_number, so.customer_id, so.customer_name, so.table_name, so.order_type,
                       so.status, so.subtotal, so.offer_name, so.discount_amount, so.tax_amount, so.total_amount,
                       so.payment_status, so.created_at, u.full_name AS staff_name,
                       c.mobile AS customer_mobile, c.email AS customer_email, c.address AS customer_address
                FROM sales_orders so
                JOIN users u ON u.id = so.staff_id
                LEFT JOIN customers c ON c.id = so.customer_id
                WHERE so.id = ?
                """,
                (int(order_id),),
            ).fetchone()
            if not order:
                return None

            item_rows = connection.execute(
                """
                SELECT item_name, quantity, unit_price, line_total
                FROM order_items
                WHERE order_id = ?
                ORDER BY id
                """,
                (int(order_id),),
            ).fetchall()
            payment = connection.execute(
                """
                SELECT method, amount, paid_at
                FROM payments
                WHERE order_id = ?
                ORDER BY datetime(paid_at) DESC
                LIMIT 1
                """,
                (int(order_id),),
            ).fetchone()

        order_data = dict(order)
        taxable_amount = max(round(float(order_data["subtotal"]) - float(order_data["discount_amount"]), 2), 0.0)
        tax_amount = round(float(order_data["tax_amount"]), 2)
        return {
            **order_data,
            "items": [dict(row) for row in item_rows],
            "taxable_amount": taxable_amount,
            "gst_rate": GST_RATE,
            "cgst_rate": round(GST_RATE / 2.0, 2),
            "sgst_rate": round(GST_RATE / 2.0, 2),
            "cgst_amount": round(tax_amount / 2.0, 2),
            "sgst_amount": round(tax_amount / 2.0, 2),
            "payment_method": payment["method"] if payment else "-",
            "paid_at": payment["paid_at"] if payment else "",
            "payment_amount": float(payment["amount"]) if payment else float(order_data["total_amount"]),
        }

    def get_recent_orders(self, limit: int = 5) -> list[dict]:
        return self.get_all_orders()[:limit]

    def get_kitchen_queue(self, limit: int = 5) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT so.id, so.order_number, so.customer_name, so.table_name, so.status,
                       so.payment_status, so.created_at, u.full_name AS staff_name,
                       GROUP_CONCAT(oi.item_name || ' x' || oi.quantity, ', ') AS item_summary
                FROM sales_orders so
                JOIN users u ON u.id = so.staff_id
                LEFT JOIN order_items oi ON oi.order_id = so.id
                WHERE so.status IN ('Pending', 'Preparing', 'Ready', 'Served')
                GROUP BY so.id
                ORDER BY datetime(so.created_at) DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_recent_payments(self, limit: int = 10) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT p.id, so.order_number, so.customer_name, p.method, p.amount,
                       p.discount_amount, p.offer_name, p.payment_status, p.paid_at
                FROM payments p
                JOIN sales_orders so ON so.id = p.order_id
                ORDER BY datetime(p.paid_at) DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_dashboard_metrics(self) -> dict:
        with self._connect() as connection:
            total_sales = connection.execute(
                "SELECT COALESCE(SUM(total_amount), 0) FROM sales_orders WHERE status != 'Cancelled'"
            ).fetchone()[0]
            total_orders = connection.execute("SELECT COUNT(*) FROM sales_orders").fetchone()[0]
            total_customers = connection.execute(
                "SELECT COUNT(DISTINCT customer_name) FROM sales_orders WHERE customer_name != 'Walk-in'"
            ).fetchone()[0]
            active_orders = connection.execute(
                "SELECT COUNT(*) FROM sales_orders WHERE status IN ('Pending', 'Preparing', 'Ready')"
            ).fetchone()[0]
            ready_to_serve = connection.execute(
                "SELECT COUNT(*) FROM sales_orders WHERE status = 'Ready'"
            ).fetchone()[0]
            pending_bills = connection.execute(
                "SELECT COALESCE(SUM(total_amount), 0) FROM sales_orders WHERE payment_status != 'Paid' AND status != 'Cancelled'"
            ).fetchone()[0]
            total_discount = connection.execute(
                "SELECT COALESCE(SUM(discount_amount), 0) FROM sales_orders"
            ).fetchone()[0]

        return {
            "total_sales": round(float(total_sales or 0), 2),
            "total_orders": int(total_orders or 0),
            "total_customers": int(total_customers or 0),
            "active_orders": int(active_orders or 0),
            "ready_to_serve": int(ready_to_serve or 0),
            "pending_bills": round(float(pending_bills or 0), 2),
            "total_discount": round(float(total_discount or 0), 2),
        }

    def get_sales_series(self) -> dict:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT created_at, total_amount, status FROM sales_orders ORDER BY datetime(created_at)"
            ).fetchall()

        if not rows:
            return {"days": [], "current_month": [], "previous_month": []}

        parsed = []
        for row in rows:
            created_at = row["created_at"]
            amount = float(row["total_amount"]) if row["status"] != "Cancelled" else 0.0
            parsed.append({"month": created_at[:7], "day": int(created_at[8:10]), "amount": amount})

        current_month = parsed[-1]["month"]
        previous_month = self._get_previous_month(current_month)
        days = sorted({row["day"] for row in parsed if row["month"] in {current_month, previous_month}})
        current_map = {day: 0.0 for day in days}
        previous_map = {day: 0.0 for day in days}

        for row in parsed:
            if row["month"] == current_month:
                current_map[row["day"]] += row["amount"]
            elif row["month"] == previous_month:
                previous_map[row["day"]] += row["amount"]

        return {
            "days": days,
            "current_month": [round(current_map[day], 2) for day in days],
            "previous_month": [round(previous_map[day], 2) for day in days],
        }

    def get_customer_insights(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT customer_name,
                       COUNT(*) AS total_orders,
                       ROUND(SUM(total_amount), 2) AS total_spent,
                       SUM(CASE WHEN payment_status = 'Paid' THEN 1 ELSE 0 END) AS paid_orders
                FROM sales_orders
                WHERE customer_name != 'Walk-in'
                GROUP BY customer_name
                ORDER BY total_spent DESC, total_orders DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_staff_sales_report(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT u.full_name, u.role,
                       COUNT(so.id) AS total_orders,
                       ROUND(COALESCE(SUM(so.total_amount), 0), 2) AS total_sales,
                       ROUND(COALESCE(SUM(so.discount_amount), 0), 2) AS discount_given
                FROM users u
                LEFT JOIN sales_orders so ON so.staff_id = u.id
                GROUP BY u.id
                ORDER BY total_sales DESC, total_orders DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_offer_sales_report(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT COALESCE(offer_name, 'No Offer') AS offer_name,
                       COUNT(*) AS total_orders,
                       ROUND(COALESCE(SUM(discount_amount), 0), 2) AS total_discount,
                       ROUND(COALESCE(SUM(total_amount), 0), 2) AS net_sales
                FROM sales_orders
                GROUP BY COALESCE(offer_name, 'No Offer')
                ORDER BY net_sales DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_payment_method_report(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT method,
                       COUNT(*) AS total_payments,
                       ROUND(SUM(amount), 2) AS amount_collected
                FROM payments
                GROUP BY method
                ORDER BY amount_collected DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_stock_report(self) -> list[dict]:
        report = []
        for item in self.get_menu_items(include_inactive=True):
            if int(item["is_stock_tracked"]) != 1:
                continue
            status = "Low Stock" if int(item["stock_qty"]) <= int(item["reorder_level"]) else "Healthy"
            report.append({**item, "stock_status": status})
        return report

    def get_top_menu_items(self, limit: int = 8) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT item_name,
                       SUM(quantity) AS total_quantity,
                       ROUND(SUM(line_total), 2) AS total_sales
                FROM order_items
                GROUP BY item_name
                ORDER BY total_quantity DESC, total_sales DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _get_previous_month(year_month: str) -> str:
        year, month = year_month.split("-")
        year_value = int(year)
        month_value = int(month)
        if month_value == 1:
            return f"{year_value - 1}-12"
        return f"{year_value:04d}-{month_value - 1:02d}"


_database = DatabaseManager()


def get_database() -> DatabaseManager:
    return _database
