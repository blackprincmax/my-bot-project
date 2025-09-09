import json
from collections import defaultdict
from datetime import datetime
import calendar
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)
import asyncpg
import os
import asyncio

# ------------------- Database Config -------------------
DB_CONFIG = {
    "user": "postgres",
    "password": "jasurbek123",
    "database": "soft1",
    "host": "localhost",
    "port": 5432,
}

# ------------------- Bot Token -------------------
BOT_TOKEN = "8388457861:AAFsOUu_29BXXVXhGABIArQ2B3JyrBocAuk"

# ------------------- Helper: Month Keyboard -------------------
def month_keyboard(year=None):
    months_ru = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                 "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    if year is None:
        year = datetime.now().year
    keyboard = []
    for i, m in enumerate(months_ru, 1):
        keyboard.append([InlineKeyboardButton(f"{m} {year}", callback_data=f"month_{year}_{i}")])
    return InlineKeyboardMarkup(keyboard)

# ------------------- Command: /report -------------------
async def report_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите месяц для отчета:", reply_markup=month_keyboard())

# ------------------- Handle Month Selection -------------------
async def month_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    year = int(data[1])
    month = int(data[2])

    await query.message.reply_text(f"Генерируется отчет за {month}/{year}...")

    file_path = await generate_monthly_report(context, year, month)
    with open(file_path, "rb") as f:
        await query.message.reply_document(f, filename=os.path.basename(file_path))

# ------------------- Generate Excel Report -------------------

async def generate_monthly_report(context, year, month):
    pool = context.bot_data.get("db_pool")
    if pool is None:
        pool = await asyncpg.create_pool(**DB_CONFIG)
        context.bot_data["db_pool"] = pool

    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)

    rows = await pool.fetch("""
        SELECT o.id, o.telegram_id, u.name, u.pharmacy_name, u.region, u.phone, o.products, o.total_sum, o.created_at
        FROM orders o
        JOIN users u ON o.telegram_id = u.telegram_id
        WHERE o.created_at BETWEEN $1 AND $2
        ORDER BY o.telegram_id, o.created_at ASC
    """, start_date, end_date)

    users_orders = defaultdict(list)
    for row in rows:
        users_orders[row["telegram_id"]].append(row)

    month_name_ru = ["Январь","Февраль","Март","Апрель","Май","Июнь",
                     "Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"][month-1].upper()
    file_path = f"Отчет_{month_name_ru}_{year}.xlsx"

    overall_products = defaultdict(lambda: {"qty": 0, "total": 0})

    # Use context manager to handle ExcelWriter
    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        start_row = 0

        for telegram_id, orders in users_orders.items():
            first_order = orders[0]
            user_info = f"Пользователь: {first_order['name']} | Телефон: {first_order['phone']} | Регион: {first_order['region']} | Аптека: {first_order['pharmacy_name']}"

            user_lines = []
            total_qty = 0
            total_sum = 0
            for idx, order in enumerate(orders, 1):
                products = json.loads(order["products"])
                for p_idx, p in enumerate(products, 1):
                    name = p["product"]["name"]
                    qty = p["qty"]
                    total = qty * p["product"]["price"]
                    user_lines.append([f"Заказ {idx}.{p_idx}", name, qty, total])
                    total_qty += qty
                    total_sum += total
                    overall_products[name]["qty"] += qty
                    overall_products[name]["total"] += total

            user_df = pd.DataFrame(user_lines, columns=["№ заказа", "Продукт", "Количество", "Сумма"])
            pd.DataFrame([[user_info]]).to_excel(writer, index=False, header=False, startrow=start_row)
            start_row += 1
            user_df.to_excel(writer, index=False, startrow=start_row)
            start_row += len(user_df) + 1
            pd.DataFrame([[f"Итог: Количество товаров: {total_qty}, Сумма: {total_sum}"]]).to_excel(
                writer, index=False, header=False, startrow=start_row
            )
            start_row += 3

        # Overall product summary
        overall_lines = [[name, v["qty"], v["total"]] for name, v in overall_products.items()]
        overall_df = pd.DataFrame(overall_lines, columns=["Продукт", "Общее количество", "Сумма"])
        pd.DataFrame([["Общий отчет по продуктам"]]).to_excel(writer, index=False, header=False, startrow=start_row)
        start_row += 1
        overall_df.to_excel(writer, index=False, startrow=start_row)

    return file_path



# ------------------- Main -------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("report", report_start))
    app.add_handler(CallbackQueryHandler(month_selected, pattern=r"^month_\d+_\d+$"))

    # Initialize DB pool before polling
    async def startup(app):
        pool = await asyncpg.create_pool(**DB_CONFIG)
        app.bot_data["db_pool"] = pool

    app.post_init = startup

    print("Bot is running...")
    app.run_polling()  # <-- no asyncio.run() needed

