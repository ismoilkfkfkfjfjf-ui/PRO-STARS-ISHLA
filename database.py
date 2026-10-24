import aiosqlite
import datetime
from contextlib import asynccontextmanager
from config import DB_PATH, DEFAULT_REF_BONUS, MIN_WITHDRAW, INITIAL_ADMINS

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
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # In case table was created earlier without last_active
        try:
            await conn.execute("ALTER TABLE users ADD COLUMN last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except Exception:
            pass

        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_referred_by ON users(referred_by);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active);")

        # Admins table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed initial admins
        for admin_id in INITIAL_ADMINS:
            await conn.execute("INSERT OR IGNORE INTO admins (user_id, added_by) VALUES (?, 0)", (admin_id,))

        # Orders table
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

# --- ADMIN MANAGEMENT HELPERS ---

async def is_user_admin(user_id: int) -> bool:
    if user_id in INITIAL_ADMINS:
        return True
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
        return (await cursor.fetchone()) is not None

async def get_all_admins() -> list[dict]:
    async with get_connection() as conn:
        cursor = await conn.execute("""
            SELECT a.user_id, a.added_by, a.added_at, u.full_name, u.username
            FROM admins a
            LEFT JOIN users u ON a.user_id = u.user_id
            ORDER BY a.added_at ASC
        """)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def add_admin(user_id: int, added_by: int) -> bool:
    async with get_connection() as conn:
        try:
            await conn.execute("INSERT OR IGNORE INTO admins (user_id, added_by) VALUES (?, ?)", (user_id, added_by))
            await conn.commit()
            return True
        except Exception:
            return False

async def remove_admin(user_id: int) -> bool:
    async with get_connection() as conn:
        cursor = await conn.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        await conn.commit()
        return cursor.rowcount > 0

# --- USER MANAGEMENT & ACTIVITY HELPERS ---

async def touch_user_activity(user_id: int):
    async with get_connection() as conn:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await conn.execute("UPDATE users SET last_active = ? WHERE user_id = ?", (now, user_id))
        await conn.commit()

async def get_user(user_id: int):
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def add_or_update_user(user_id: int, full_name: str, username: str, referred_by: int | None = None) -> tuple[dict, bool]:
    async with get_connection() as conn:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        existing = await cursor.fetchone()

        if existing:
            await conn.execute(
                "UPDATE users SET full_name = ?, username = ?, last_active = ? WHERE user_id = ?",
                (full_name, username, now, user_id)
            )
            await conn.commit()
            return dict(existing), False

        valid_ref = None
        if referred_by and referred_by != user_id:
            ref_cursor = await conn.execute("SELECT user_id FROM users WHERE user_id = ?", (referred_by,))
            if await ref_cursor.fetchone():
                valid_ref = referred_by

        await conn.execute("""
            INSERT INTO users (user_id, full_name, username, balance, referred_by, referrals_count, total_withdrawn, is_banned, last_active)
            VALUES (?, ?, ?, 0.0, ?, 0, 0.0, 0, ?)
        """, (user_id, full_name, username, valid_ref, now))
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

async def set_user_ban(user_id: int, is_banned: int) -> bool:
    async with get_connection() as conn:
        cursor = await conn.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (is_banned, user_id))
        await conn.commit()
        return cursor.rowcount > 0

async def search_user(query: str) -> dict | None:
    query = query.strip().replace("@", "")
    async with get_connection() as conn:
        if query.isdigit():
            cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (int(query),))
        else:
            cursor = await conn.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (query,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_all_user_ids(only_active: bool = False):
    async with get_connection() as conn:
        if only_active:
            cursor = await conn.execute("SELECT user_id FROM users WHERE is_banned = 0")
        else:
            cursor = await conn.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()
        return [row["user_id"] for row in rows]

# --- ADVANCED STATS HELPERS ---

async def get_detailed_user_stats() -> dict:
    async with get_connection() as conn:
        total = (await (await conn.execute("SELECT COUNT(*) FROM users")).fetchone())[0]

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        today = (await (await conn.execute("SELECT COUNT(*) FROM users WHERE DATE(joined_at) = ?", (today_str,))).fetchone())[0]

        # Active users in last 24h and last 7 days
        since_24h = (datetime.datetime.now() - datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        active_24h = (await (await conn.execute("SELECT COUNT(*) FROM users WHERE last_active >= ?", (since_24h,))).fetchone())[0]

        since_7d = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        active_7d = (await (await conn.execute("SELECT COUNT(*) FROM users WHERE last_active >= ?", (since_7d,))).fetchone())[0]

        banned = (await (await conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")).fetchone())[0]
        total_referrals = (await (await conn.execute("SELECT COALESCE(SUM(referrals_count), 0) FROM users")).fetchone())[0]

        sum_balances = (await (await conn.execute("SELECT COALESCE(SUM(balance), 0) FROM users")).fetchone())[0]
        sum_withdrawn = (await (await conn.execute("SELECT COALESCE(SUM(total_withdrawn), 0) FROM users")).fetchone())[0]

        return {
            "total_users": total,
            "today_users": today,
            "active_users_24h": active_24h,
            "active_users_7d": active_7d,
            "banned_users": banned,
            "total_referrals": total_referrals,
            "sum_balances": sum_balances,
            "sum_withdrawn": sum_withdrawn
        }

async def get_top_referrers(limit: int = 10) -> list[dict]:
    async with get_connection() as conn:
        cursor = await conn.execute("""
            SELECT user_id, full_name, username, referrals_count, balance, total_withdrawn
            FROM users
            WHERE referrals_count > 0
            ORDER BY referrals_count DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def get_recent_users(limit: int = 10) -> list[dict]:
    async with get_connection() as conn:
        cursor = await conn.execute("""
            SELECT user_id, full_name, username, balance, referrals_count, joined_at
            FROM users
            ORDER BY joined_at DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

# --- ORDERS HELPERS ---

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

# --- CHANNELS HELPERS ---

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

# --- SETTINGS HELPERS ---

async def get_setting(key: str, default: str = "") -> str:
    async with get_connection() as conn:
        cursor = await conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row["value"] if row else default

async def set_setting(key: str, value: str):
    async with get_connection() as conn:
        await conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, str(value)))
        await conn.commit()

async def get_stats():
    async with get_connection() as conn:
        u_stats = await get_detailed_user_stats()

        total_orders = (await (await conn.execute("SELECT COUNT(*) FROM orders")).fetchone())[0]
        pending_orders = (await (await conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")).fetchone())[0]
        approved_orders = (await (await conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'approved'")).fetchone())[0]
        rejected_orders = (await (await conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'rejected'")).fetchone())[0]

        admins_count = (await (await conn.execute("SELECT COUNT(*) FROM admins")).fetchone())[0]

        return {
            **u_stats,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "approved_orders": approved_orders,
            "rejected_orders": rejected_orders,
            "admins_count": admins_count
        }
