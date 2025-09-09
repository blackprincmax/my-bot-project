import asyncpg
import json
import logging

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "user": "postgres",
    "password": "jasurbek123",
    "database": "soft1",
    "host": "localhost",   # or your server
    "port": 5432
}

# --- Create connection pool ---
async def init_db():
    return await asyncpg.create_pool(**DB_CONFIG)


# --- Save or update user ---
async def save_user(pool, telegram_id, name, pharmacy_name, region, phone):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (telegram_id, name, pharmacy_name, region, phone)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (telegram_id)
            DO UPDATE SET name=$2, pharmacy_name=$3, region=$4, phone=$5;
            """,
            telegram_id, name, pharmacy_name, region, phone
        )
        logger.info(f"User {telegram_id} saved/updated.")


# --- Save order ---
# db.py

async def save_order(pool, telegram_id, products, total_sum):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO orders (telegram_id, products, total_sum, created_at)
            VALUES ($1, $2, $3, NOW())
            """,
            telegram_id,
            json.dumps(products),
            total_sum,
        )



# --- Get all orders of a user ---
async def get_orders_by_user(pool, telegram_id):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, products, total_sum, status, created_at
            FROM orders
            WHERE telegram_id=$1
            ORDER BY created_at DESC;
            """,
            telegram_id
        )
        return [dict(r) for r in rows]

