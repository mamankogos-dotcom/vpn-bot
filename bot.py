import asyncio
import io
import os
import time
import httpx
import qrcode
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, LabeledPrice, PreCheckoutQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile,
)
from aiogram.filters import CommandStart

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
MARZBAN_URL = os.getenv("MARZBAN_URL", "http://127.0.0.1:8000")
MARZBAN_USER = os.getenv("MARZBAN_USER")
MARZBAN_PASS = os.getenv("MARZBAN_PASS")
SUB_DAYS = int(os.getenv("SUB_DAYS", "30"))
PRICE_STARS = int(os.getenv("PRICE_STARS", "100"))

_token = {"value": None, "exp": 0}
async def _get_token():
if _token["value"] and _token["exp"] > time.time():
return _token["value"]
async with httpx.AsyncClient(base_url=MARZBAN_URL, timeout=15) as c:
r = await c.post("/api/admin/token", data={"username": MARZBAN_USER, "password": MARZBAN_PASS})
r.raise_for_status()
tok = r.json()["access_token"]
_token["value"] = tok
_token["exp"] = time.time() + 3000
return tok
async def create_or_renew_user(tg_id):
token = await _get_token()
headers = {"Authorization": f"Bearer {token}"}
username = f"tg_{tg_id}"
expire = int(time.time()) + SUB_DAYS * 86400
payload = {
	"username": username,
"proxies": {"vless": {}},
"inbounds": {},
"expire": expire,
"data_limit": 0,
"status": "active",
}
async with httpx.AsyncClient(base_url=MARZBAN_URL, timeout=15) as c:
r = await c.post("/api/user", headers=headers, json=payload)
if r.status_code == 409:
r = await c.put(f"/api/user/{username}", headers=headers, json={"expire": expire, "status": "active"})
r.raise_for_status()
return r.json()
async def get_user_links(tg_id):
token = await _get_token()
headers = {"Authorization": f"Bearer {token}"}
username = f"tg_{tg_id}"
async with httpx.AsyncClient(base_url=MARZBAN_URL, timeout=15) as c:
r = await c.get(f"/api/user/{username}", headers=headers)
r.raise_for_status()
return r.json().get("links", [])
bot = Bot(BOT_TOKEN)
dp = Dispatcher()
@dp.message(CommandStart())
async def start(m: Message):
kb = InlineKeyboardMarkup(inline_keyboard=[
[InlineKeyboardButton(text=f" Купить VPN ({PRICE_STARS} / {SUB_DAYS} дн.)", callback_data="buy")],
[InlineKeyboardButton(text=" Мой ключ", callback_data="mykey")],
])
await m.answer("Привет! Это VPN-бот.nn1) Купи подпискуn2) Получи ключ и QRn3) Открой его в v2RayTun / Hiddify.", reply_markup=kb)
@dp.callback_query(F.data == "buy")
async def buy(cq):
	await bot.send_invoice(
chat_id=cq.from_user.id,
title="VPN подписка",
description=f"Доступ к VPN на {SUB_DAYS} дней",
payload="vpn_sub",
currency="XTR",
prices=[LabeledPrice(label="VPN", amount=PRICE_STARS)],
)
await cq.answer()
@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
await bot.answer_pre_checkout_query(q.id, ok=True)
@dp.message(F.successful_payment)
async def paid(m: Message):
await create_or_renew_user(m.from_user.id)
await send_key(m.from_user.id)
@dp.callback_query(F.data == "mykey")
async def mykey(cq):
await send_key(cq.from_user.id)
await cq.answer()
async def send_key(tg_id):
links = await get_user_links(tg_id)
if not links:
await bot.send_message(tg_id, " Ключ ещё формируется, нажми «Мой ключ» через минуту.")
return
vless = links[0]
img = qrcode.make(vless)
buf = io.BytesIO()
img.save(buf, format="PNG")
buf.seek(0)
await bot.send_photo(
chat_id=tg_id,
photo=BufferedInputFile(buf.read(), filename="vpn.png"),
caption=" Подписка активна!nnТвой ключ (скопируй или отсканируй QR):n" + f"{vless}" + "nnОткрой v2RayTun / Hiddify → «+» → «Импорт из буфера» → подключись.",
parse_mode="Markdown",
)
async def main():
await dp.start_polling(bot)
if name == "main":
asyncio.run(main())
