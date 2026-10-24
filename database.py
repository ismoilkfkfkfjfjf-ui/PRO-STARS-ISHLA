import aiosqlite
import datetime
from contextlib import asynccontextmanager
from config import DB_PATH, DEFAULT_REF_BONUS, MIN_WITHDRAW

@asynccontextmanager
async def get_connection():
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode = WAL;")
    await conn.execute("PRAGMA synchronous = NORMAL;")
    await conn.execute("PRAGMA busy_timeout = 5000;")
    try:
        yield conn
    finally:
        await conn.close()

async def init_db():
    async with get_connection() as conn:
        # Users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                balance REAL DEFAULT 0.0,
                referred_by INTEGER,
                referrals_count INTEGER DEFAULT 0,
                total_withdrawn REAL DEFAULT 0.0,
                is_banned INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_referred_by ON users(referred_by);")

        # Orders (Withdrawal requests) table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                target_account TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                reject_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);")

        # Settings table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Mandatory channels table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE NOT NULL,
                channel_title TEXT,
                invite_link TEXT
            )
        """)

        # Default settings if not exist
        await conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('ref_bonus', ?)", (str(DEFAULT_REF_BONUS),))
        await conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('min_withdraw', ?)", (str(MIN_WITHDRAW),))

        await conn.commit()

# Settings helpers
async def get_setting(key: str, default: str = "") -> str:
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row["value"] if row else default

async def set_setting(key: str, value: str):
    async with get_connection() as conn:
        await conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, str(value)))
        await conn.commit()

# User helpers
async def get_user(user_id: int):
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def add_or_update_user(user_id: int, full_name: str, username: str, referred_by: int | None = None) -> tuple[dict, bool]:
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        existing = await cursor.fetchone()

        if existing:
            await conn.execute(
                "UPDATE users SET full_name = ?, username = ? WHERE user_id = ?",
                (full_name, username, user_id)
            )
            await conn.commit()
            return dict(existing), False

        valid_ref = None
        if referred_by and referred_by != user_id:
            ref_cursor = await conn.execute("SELECT user_id FROM users WHERE user_id = ?", (referred_by,))
            if await ref_cursor.fetchone():
                valid_ref = referred_by

        await conn.execute("""
            INSERT INTO users (user_id, full_name, username, balance, referred_by, referrals_count, total_withdrawn, is_banned)
            VALUES (?, ?, ?, 0.0, ?, 0, 0.0, 0)
        """, (user_id, full_name, username, valid_ref))
        await conn.commit()

        cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        new_row = await cursor.fetchone()
        return dict(new_row), True

async def reward_referrer(referrer_id: int, bonus_amount: float):
    async with get_connection() as conn:
        await conn.execute("""
            UPDATE users
            SET balance = balance + ?, referrals_count = referrals_count + 1
            WHERE user_id = ?
        """, (bonus_amount, referrer_id))
        await conn.commit()

async def update_user_balance(user_id: int, delta: float) -> bool:
    async with get_connection() as conn:
        if delta < 0:
            cursor = await conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            if not row or row["balance"] < abs(delta):
                return False
        await conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (delta, user_id))
        await conn.commit()
        return True

async def get_all_user_ids():
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT user_id FROM users WHERE is_banned = 0")
        rows = await cursor.fetchall()
        return [row["user_id"] for row in rows]

# Orders / Withdrawal helpers
async def create_withdrawal_order(user_id: int, amount: float, target_account: str) -> int | None:
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row or row["balance"] < amount:
            return None

        await conn.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        cur = await conn.execute("""
            INSERT INTO orders (user_id, amount, target_account, status)
            VALUES (?, ?, ?, 'pending')
        """, (user_id, amount, target_account))
        await conn.commit()
        return cur.lastrowid

async def get_order(order_id: int):
    async with get_connection() as conn:
        cursor = await conn.execute("""
            SELECT o.*, u.full_name, u.username
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            WHERE o.id = ?
        """, (order_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_user_orders(user_id: int, limit: int = 10):
    async with get_connection() as conn:
        cursor = await conn.execute("""
            SELECT * FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def get_pending_orders(limit: int = 20):
    async with get_connection() as conn:
        cursor = await conn.execute("""
            SELECT o.*, u.full_name, u.username
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            WHERE o.status = 'pending'
            ORDER BY o.id ASC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def update_order_status(order_id: int, status: str, reject_reason: str = None) -> dict | None:
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = await cursor.fetchone()
        if not order or order["status"] != "pending":
            return None

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if status == "approved":
            await conn.execute("""
                UPDATE orders
                SET status = 'approved', processed_at = ?
                WHERE id = ?
            """, (now, order_id))
            await conn.execute("""
                UPDATE users
                SET total_withdrawn = total_withdrawn + ?
                WHERE user_id = ?
            """, (order["amount"], order["user_id"]))

        elif status == "rejected":
            await conn.execute("""
                UPDATE orders
                SET status = 'rejected', reject_reason = ?, processed_at = ?
                WHERE id = ?
            """, (reject_reason, now, order_id))
            await conn.execute("""
                UPDATE users
                SET balance = balance + ?
                WHERE user_id = ?
            """, (order["amount"], order["user_id"]))

        await conn.commit()

        cur2 = await conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        updated = await cur2.fetchone()
        return dict(updated) if updated else None

# Channels (Mandatory Subscription) helpers
async def get_channels():
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM channels")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def add_channel(channel_id: str, channel_title: str, invite_link: str) -> bool:
    async with get_connection() as conn:
        try:
            await conn.execute("""
                INSERT INTO channels (channel_id, channel_title, invite_link)
                VALUES (?, ?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET channel_title = excluded.channel_title, invite_link = excluded.invite_link
            """, (channel_id, channel_title, invite_link))
            await conn.commit()
            return True
        except Exception:
            return False

async def delete_channel(channel_id: str):
    async with get_connection() as conn:
        await conn.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        await conn.commit()

# Stats helpers
async def get_stats():
    async with get_connection() as conn:
        total_users = (await (await conn.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        today = datetime.date.today().strftime("%Y-%m-%d")
        today_users = (await (await conn.execute("SELECT COUNT(*) FROM users WHERE DATE(joined_at) = ?", (today,))).fetchone())[0]

        total_orders = (await (await conn.execute("SELECT COUNT(*) FROM orders")).fetchone())[0]
        pending_orders = (await (await conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")).fetchone())[0]
        approved_orders = (await (await conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'approved'")).fetchone())[0]
        rejected_orders = (await (await conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'rejected'")).fetchone())[0]

        sum_withdrawn = (await (await conn.execute("SELECT COALESCE(SUM(amount), 0) FROM orders WHERE status = 'approved'")).fetchone())[0]
        sum_balances = (await (await conn.execute("SELECT COALESCE(SUM(balance), 0) FROM users")).fetchone())[0]

        return {
            "total_users": total_users,
            "today_users": today_users,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "approved_orders": approved_orders,
            "rejected_orders": rejected_orders,
            "sum_withdrawn": sum_withdrawn,
            "sum_balances": sum_balances
        }
