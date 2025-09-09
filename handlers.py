from telegram import ReplyKeyboardRemove
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)
import logging
from db import save_user, save_order

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- States ---
LANGUAGE, NAME, PHARMACY_NAME, REGION, PHONE, PRODUCTS, QUANTITY, BASKET, CHECKOUT, MAIN_MENU = range(10)

# --- Storage ---
user_data = {}

# --- Product List ---
PRODUCTS_LIST = [
    {"name": "Men Spray (пролонгатор)", "price": 85000},
    {"name": "Презерватив SOFT CLASSIC", "price": 13000},
    {"name": "Презерватив SOFT EXTRA", "price": 13000},
    {"name": "Презерватив SOFT INVISIBLE", "price": 13000},
    {"name": "Love Parfum Pheromones №03 жен.", "price": 80000},
    {"name": "Love Parfum Pheromones №07 муж.", "price": 80000},
    {"name": "Love Parfum Pheromones №31 муж.", "price": 80000},
    {"name": "Love Parfum Pheromones №37 жен.", "price": 80000},
    {"name": "Love Parfum Pheromones №67 муж.", "price": 80000},
    {"name": "Love Parfum Pheromones №79 жен.", "price": 80000},
    {"name": "Лубрикант SOFT ALOE 80 ml", "price": 75000},
    {"name": "Лубрикант SOFT BANAN 80ml", "price": 75000},
    {"name": "Лубрикант SOFT CHERRY 80ml", "price": 75000},
    {"name": "Лубрикант SOFT CLASSIC 80ml", "price": 75000},
    {"name": "Лубрикант SOFT COCONUT 80ml", "price": 75000},
    {"name": "Лубрикант SOFT MANGO 80ml", "price": 75000},
    {"name": "Лубрикант SOFT STRAWBERRY 80ml", "price": 75000},
    {"name": "Лубрикант SOFT TUTTI FRUTTI 80 ml", "price": 75000},
    {"name": "Лубрикант SOFT VANILLA 80 ml", "price": 75000},
    {"name": "Лубрикант SOFT VIRGIN 80 ml", "price": 85000},
    {"name": "Лубрикант SOFT WARMING 80ml", "price": 75000},
]

# --- Categories ---
CATEGORIES = {
    "Men Spray": [p for p in PRODUCTS_LIST if p["name"].startswith("Men Spray")],
    "Презерватив": [p for p in PRODUCTS_LIST if p["name"].startswith("Презерватив")],
    "Pheromones": [p for p in PRODUCTS_LIST if "Pheromones" in p["name"]],
    "Лубрикант": [p for p in PRODUCTS_LIST if p["name"].startswith("Лубрикант")],
}

# --- Languages ---
LANGUAGE_TEXTS = {
    "uz": {
        "choose_language": "Tilni tanlang:",
        "ask_name": "Dorixona nomini kiriting 🏥:",
        "ask_region": "📍 Hududni tanlang:",
        "ask_phone": "📱 Telefon raqamingizni yuboring:",
        "product_menu": "Mahsulot kategoriyasini tanlang:",
        "product_info": "{name}\nNarxi: {price} so‘m",
        "ask_quantity": "Nechta dona olasiz?",
        "added_to_basket": "{name} savatchaga qo‘shildi.",
        "basket": "🛒 Savatcha:\n{items}\n\nJami: {total} so‘m",
        "empty_basket": "Savatchangiz bo‘sh.",
        "checkout": "Buyurtmani tasdiqlaysizmi?",
        "confirmed": "✅ Buyurtma qabul qilindi",
        "canceled": "❌ Buyurtma bekor qilindi",
        "enter_number_error": "❌ Iltimos, raqam kiriting",
        "choose_from_menu": "Iltimos, menyudan tanlang:",
        "new_order": "🛒 Yangi buyurtma",
        "products_menu": "📦 Mahsulotlar",
        "confirm": "✅ Tasdiqlash",
        "cancel": "❌ Bekor qilish"
    },
    "ru": {
        "choose_language": "Выберите язык:",
        "ask_name": "Введите название аптеки 🏥:",
        "ask_region": "📍 Выберите район:",
        "ask_phone": "📱 Отправьте ваш номер телефона:",
        "product_menu": "Выберите категорию продукта:",
        "product_info": "{name}\nЦена: {price} сум",
        "ask_quantity": "Сколько штук вы хотите?",
        "added_to_basket": "{name} добавлен в корзину.",
        "basket": "🛒 Корзина:\n{items}\n\nИтого: {total} сум",
        "empty_basket": "Ваша корзина пуста.",
        "checkout": "Подтверждаете заказ?",
        "confirmed": "✅ Заказ принят",
        "canceled": "❌ Заказ отменён",
        "enter_number_error": "❌ Пожалуйста, введите число",
        "choose_from_menu": "Пожалуйста, выберите из меню:",
        "new_order": "🛒 Новый заказ",
        "products_menu": "📦 Продукты",
        "confirm": "✅ Подтвердить",
        "cancel": "❌ Отмена"
    },
}

# --- Add phone button texts ---
LANGUAGE_TEXTS["uz"]["phone_button"] = "📱 Telefon raqamni yuborish"
LANGUAGE_TEXTS["ru"]["phone_button"] = "📱 Отправить номер телефона"

# --- Regions of Tashkent (Bilingual) ---
TASHKENT_REGIONS = {
    "uz": [
        "Bektemir", "Chilonzor", "Mirobod", "Mirzo Ulug‘bek",
        "Olmazor", "Sergeli", "Shayxontohur", "Uchtepa",
        "Yakkasaroy", "Yashnobod", "Yunusobod", "Yangi hayot"
    ],
    "ru": [
        "Бектемир", "Чиланзор", "Миробод", "Мирзо Улугбек",
        "Олмазор", "Сергелий", "Шайхантахур", "Учтепа",
        "Яккасарай", "Яшнабад", "Юнусабад", "Новая жизнь"
    ]
}


# --- Helper for main menu keyboard ---
def main_menu_keyboard(lang="uz"):
    keyboard = [[
        KeyboardButton(LANGUAGE_TEXTS[lang]["new_order"]),
        KeyboardButton(LANGUAGE_TEXTS[lang]["products_menu"])
    ]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ---------------- Handlers ---------------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("🇺🇿 O‘zbekcha"), KeyboardButton("🇷🇺 Русский")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Tilni tanlang / Выберите язык:", reply_markup=reply_markup)
    return LANGUAGE


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_choice = update.message.text
    lang = "uz" if "O‘zbekcha" in lang_choice else "ru"

    user_data[update.effective_user.id] = {"language": lang, "basket": []}

    # Language-specific prompt for asking the user's name
    prompt_text = "👤 Ismingizni kiriting" if lang == "uz" else "👤 Введите ваше имя"
    await update.message.reply_text(prompt_text)

    return NAME


async def set_user_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["name"] = update.message.text
    lang = user_data[user_id]["language"]
    await update.message.reply_text(LANGUAGE_TEXTS[lang]["ask_name"])
    return PHARMACY_NAME

async def set_pharmacy_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["pharmacy_name"] = update.message.text
    lang = user_data[user_id]["language"]

    keyboard = [[KeyboardButton(r)] for r in TASHKENT_REGIONS[lang]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(LANGUAGE_TEXTS[lang]["ask_region"], reply_markup=reply_markup)
    return REGION

from telegram import ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup

async def set_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["region"] = update.message.text
    lang = user_data[user_id]["language"]

    # Phone button
    phone_keyboard = [[KeyboardButton(LANGUAGE_TEXTS[lang]["phone_button"], request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(phone_keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(LANGUAGE_TEXTS[lang]["ask_phone"], reply_markup=reply_markup)
    return PHONE

async def set_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_data[user_id]["language"]
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    user_data[user_id]["phone"] = phone

    # Save user to DB
    pool = context.application.bot_data["db_pool"]
    await save_user(
        pool,
        telegram_id=user_id,
        name=user_data[user_id]["name"],
        pharmacy_name=user_data[user_id]["pharmacy_name"],
        region=user_data[user_id]["region"],
        phone=phone,
    )

    # Remove keyboard with language-specific confirmation
    confirmation_text = "✅ Telefon raqam qabul qilindi" if lang == "uz" else "✅ Телефон принят"
    await update.message.reply_text(confirmation_text, reply_markup=ReplyKeyboardRemove())

    return await show_categories(update, context)

# --- Category & Product Selection ---
async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_data[user_id]["language"]

    keyboard = [[InlineKeyboardButton(cat, callback_data=f"category_{cat}")] for cat in CATEGORIES.keys()]
    keyboard.append([InlineKeyboardButton("🛒 " + LANGUAGE_TEXTS[lang]["checkout"], callback_data="finish_order")])

    if update.message:
        await update.message.reply_text(LANGUAGE_TEXTS[lang]["product_menu"], reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text(LANGUAGE_TEXTS[lang]["product_menu"], reply_markup=InlineKeyboardMarkup(keyboard))

    return PRODUCTS

async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    lang = user_data[user_id]["language"]

    category = query.data.split("_", 1)[1]
    user_data[user_id]["current_category"] = category
    products = CATEGORIES[category]

    keyboard = [[InlineKeyboardButton(p["name"], callback_data=f"product_{i}")] for i, p in enumerate(products)]
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_categories")])
    keyboard.append([InlineKeyboardButton("🛒 " + LANGUAGE_TEXTS[lang]["checkout"], callback_data="finish_order")])

    await query.message.reply_text(f"📂 {category}:", reply_markup=InlineKeyboardMarkup(keyboard))
    return PRODUCTS

async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    lang = user_data[user_id]["language"]

    category = user_data[user_id]["current_category"]
    products = CATEGORIES[category]
    index = int(query.data.split("_")[1])
    product = products[index]
    user_data[user_id]["current_product"] = product

    price_str = f"{product['price']:,}".replace(",", ".")
    await query.message.reply_text(LANGUAGE_TEXTS[lang]["product_info"].format(name=product["name"], price=price_str))
    await query.message.reply_text(LANGUAGE_TEXTS[lang]["ask_quantity"])
    return QUANTITY

async def get_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_data[user_id]["language"]

    try:
        qty = int(update.message.text)
    except ValueError:
        await update.message.reply_text(LANGUAGE_TEXTS[lang]["enter_number_error"])
        return QUANTITY

    product = user_data[user_id]["current_product"]
    user_data[user_id]["basket"].append({"product": product, "qty": qty})

    await update.message.reply_text(LANGUAGE_TEXTS[lang]["added_to_basket"].format(name=product["name"]))
    return await show_categories(update, context)

# --- Basket & Checkout ---
async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    lang = user_data[user_id]["language"]

    basket = user_data[user_id]["basket"]
    if not basket:
        await query.message.reply_text(LANGUAGE_TEXTS[lang]["empty_basket"])
        return BASKET

    items_text = "\n".join(
        [f"{item['product']['name']} x {item['qty']} = {(item['product']['price'] * item['qty']):,}".replace(",", ".") + " so‘m"
         for item in basket]
    )
    total = sum(item['product']['price'] * item['qty'] for item in basket)
    total_str = f"{total:,}".replace(",", ".")

    await query.message.reply_text(LANGUAGE_TEXTS[lang]["basket"].format(items=items_text, total=total_str))

    keyboard = [[
        KeyboardButton(LANGUAGE_TEXTS[lang]["confirm"]),
        KeyboardButton(LANGUAGE_TEXTS[lang]["cancel"])
    ]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await query.message.reply_text(LANGUAGE_TEXTS[lang]["checkout"], reply_markup=reply_markup)
    return CHECKOUT

async def confirm_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_data[user_id]["language"]
    text = update.message.text

    if text == LANGUAGE_TEXTS[lang]["confirm"]:
        basket = user_data[user_id]["basket"]
        total = sum(item['product']['price'] * item['qty'] for item in basket)

        # Save order to DB
        pool = context.application.bot_data["db_pool"]
        await save_order(pool, telegram_id=user_id, products=basket, total_sum=total)

        await update.message.reply_text(LANGUAGE_TEXTS[lang]["confirmed"], reply_markup=main_menu_keyboard(lang))
        logger.info(f"✅ Order confirmed: {user_data[user_id]}")
    else:  # Cancel
        await update.message.reply_text(LANGUAGE_TEXTS[lang]["canceled"], reply_markup=main_menu_keyboard(lang))
        logger.info(f"❌ Order canceled: {user_data[user_id]}")

    # Clear basket and selections
    user_data[user_id]["basket"] = []
    user_data[user_id]["current_product"] = None
    user_data[user_id]["current_category"] = None
    return MAIN_MENU

# --- Main Menu ---
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    lang = user_data[user_id]["language"]

    if text == LANGUAGE_TEXTS[lang]["new_order"]:
        user_data[user_id]["basket"] = []
        return await show_categories(update, context)
    elif text == LANGUAGE_TEXTS[lang]["products_menu"]:
        return await show_categories(update, context)
    else:
        await update.message.reply_text(LANGUAGE_TEXTS[lang]["choose_from_menu"])
        return MAIN_MENU

# --- Conversation Handler ---
def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_user_name)],
            PHARMACY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_pharmacy_name)],
            REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_region)],
            PHONE: [MessageHandler(filters.CONTACT | filters.TEXT, set_phone)],
            PRODUCTS: [
                CallbackQueryHandler(category_selected, pattern=r"^category_"),
                CallbackQueryHandler(product_selected, pattern=r"^product_"),
                CallbackQueryHandler(show_categories, pattern=r"^back_to_categories$"),
                CallbackQueryHandler(finish_order, pattern="^finish_order$"),
            ],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity)],
            BASKET: [],
            CHECKOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_checkout)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
        },
        fallbacks=[],
    )
