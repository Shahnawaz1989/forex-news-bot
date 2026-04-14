import telebot

# ==== CONFIG ====
MENU_BOT_TOKEN = "8217083753:AAG14e-puoUpeGqFmDdtFOI60Ay32ErfyqY"   # BotFather se naya token
EA_BOT_CHAT_ID = 487621983                     # wahi chat_id jo EA Inputs me AllowedChatId hai

bot = telebot.TeleBot(MENU_BOT_TOKEN)

# per-user temporary state
user_state = {}   # chat_id -> dict

# ---------- step helpers ----------

def reset_state(chat_id):
    user_state[chat_id] = {
        "symbol": None,
        "side": None,
        "type": None,
        "lot": None,
        "entry": None,
        "sl": None,
        "tp": None,
        "expiry": None,
        "tpx": None,
    }

# ---------- start / symbol ----------

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    reset_state(chat_id)
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("EURUSD","GBPUSD","XAUUSD")
    kb.row("AUDCAD","CADCHF","NZDUSD")
    bot.send_message(chat_id, "Step 1/7: Symbol select karo:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["EURUSD","GBPUSD","XAUUSD","AUDCAD","CADCHF","NZDUSD"])
def got_symbol(message):
    chat_id = message.chat.id
    st = user_state.setdefault(chat_id, {})
    st["symbol"] = message.text
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("BUY","SELL")
    bot.send_message(chat_id, "Step 2/7: Direction (BUY/SELL):", reply_markup=kb)

# ---------- direction ----------

@bot.message_handler(func=lambda m: m.text in ["BUY","SELL"])
def got_side(message):
    chat_id = message.chat.id
    st = user_state.setdefault(chat_id, {})
    st["side"] = message.text
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    if message.text == "BUY":
        kb.row("BUY MARKET","BUY LIMIT","BUY STOP")
    else:
        kb.row("SELL MARKET","SELL LIMIT","SELL STOP")
    bot.send_message(chat_id, "Step 3/7: Order type:", reply_markup=kb)

# ---------- type ----------

def is_type_text(text):
    keys = ["BUY MARKET","SELL MARKET","BUY LIMIT","SELL LIMIT","BUY STOP","SELL STOP"]
    return text in keys

@bot.message_handler(func=lambda m: is_type_text(m.text))
def got_type(message):
    chat_id = message.chat.id
    st = user_state.setdefault(chat_id, {})
    txt = message.text   # e.g. "BUY LIMIT"
    side, t = txt.split()   # ["BUY","LIMIT"]
    st["side"] = side
    if t == "MARKET":
        st["type"] = "MARKET"
    else:
        st["type"] = side + "_" + t   # e.g. BUY_LIMIT / SELL_STOP

    bot.send_message(chat_id, "Step 4/7: Lot size (e.g. 0.01):")
    bot.register_next_step_handler(message, got_lot)

# ---------- lot ----------

def got_lot(message):
    chat_id = message.chat.id
    st = user_state.setdefault(chat_id, {})
    st["lot"] = message.text.strip()
    if st["type"] != "MARKET":
        bot.send_message(chat_id, "Step 5/7: Entry price (pending ke liye):")
        bot.register_next_step_handler(message, got_entry)
    else:
        bot.send_message(chat_id, "Step 5/7: SL price (ya 0):")
        bot.register_next_step_handler(message, got_sl)

def got_entry(message):
    chat_id = message.chat.id
    st = user_state.setdefault(chat_id, {})
    st["entry"] = message.text.strip()
    bot.send_message(chat_id, "Step 6/7: SL price (ya 0):")
    bot.register_next_step_handler(message, got_sl)

def got_sl(message):
    chat_id = message.chat.id
    st = user_state.setdefault(chat_id, {})
    st["sl"] = message.text.strip()
    bot.send_message(chat_id, "Step 6/7: TP price (ya 0):")
    bot.register_next_step_handler(message, got_tp)

def got_tp(message):
    chat_id = message.chat.id
    st = user_state.setdefault(chat_id, {})
    st["tp"] = message.text.strip()
    if st["type"] != "MARKET":
        bot.send_message(chat_id, "Step 7/7: Expiry IST (HH:MM, 0 = no expiry):")
        bot.register_next_step_handler(message, got_expiry)
    else:
        ask_tpx(message)

def got_expiry(message):
    chat_id = message.chat.id
    st = user_state.setdefault(chat_id, {})
    st["expiry"] = message.text.strip()
    ask_tpx(message)

# ---------- TP touch-exit ----------

def ask_tpx(message):
    chat_id = message.chat.id
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("TP_TOUCH_EXIT YES","TP_TOUCH_EXIT NO")
    bot.send_message(chat_id, "TP touch-exit enable kare? (YES/NO)", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["TP_TOUCH_EXIT YES","TP_TOUCH_EXIT NO"])
def final_confirm(message):
    chat_id = message.chat.id
    st = user_state.setdefault(chat_id, {})
    st["tpx"] = "YES" if "YES" in message.text else "NO"

    side   = st["side"]
    symbol = st["symbol"]
    otype  = st["type"]          # MARKET or BUY_LIMIT / SELL_STOP
    lot    = st["lot"]
    sl     = st["sl"]
    tp     = st["tp"]
    expiry = st.get("expiry","0")
    tpx    = st["tpx"]

    # TYPE field for EA
    if otype == "MARKET":
        type_for_ea = "MARKET"
    else:
        type_for_ea = otype       # already BUY_LIMIT / SELL_STOP etc.

    parts = [
        "ORDER: " + side,
        "SYMBOL: " + symbol,
        "TYPE: " + type_for_ea,
        "LOT: " + lot
    ]

    if otype != "MARKET":
        parts.append("ENTRY: " + st["entry"])
    parts.append("SL: " + sl)
    parts.append("TP: " + tp)
    parts.append("MODE: DIRECT")
    if otype != "MARKET" and expiry != "0":
        parts.append("EXPIRY_IST: " + expiry)
    parts.append("TP_TOUCH_EXIT: " + tpx)

    text = " | ".join(parts)

    # Send to EA bot chat
    bot.send_message(EA_BOT_CHAT_ID, text)
    bot.send_message(chat_id, "MT4 ko ye command bheji gayi hai:\n"+text)

    reset_state(chat_id)

# ---------- run ----------
print("Menu bot started...")
bot.infinity_polling()
