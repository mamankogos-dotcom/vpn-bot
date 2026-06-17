import asyncio
import io
import qrcode
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
	Message,
	LabeledPrice,
	PreCheckoutQuery,
	InlineKeyboardMarkup,
	InlineKeyboardButton,
	BufferedInputFile,
)
from aiogram.filters import CommandStart, Command

from config import BOT_TOKEN, PRICE_STARS, SUB_DAYS
from marzban import create_or_renew_user, get_subscription_url

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(m: Message):
	kb = InlineKeyboardMarkup(
		inline_keyboard=[
			[InlineKeyboardButton(text=f"💳 Купить VPN ({PRICE_STARS}⭐ / {SUB_DAYS} дн.)", callback_data="buy")],
			[InlineKeyboardButton(text="🔑 Мой ключ", callback_data="mykey")],
		]
	)
	await m.answer(
		"Привет! Это VPN-бот.\n\n"
		"1) Купи подписку\n"
		"2) Получи ключ и QR\n"
		"3) Открой его в приложении v2RayTun / Hiddify — и ты в VPN.",
		reply_markup=kb,
	)


@dp.callback_query(F.data == "buy")
async def buy(cq):
	await bot.send_invoice(
		chat_id=cq.from_user.id,
		title="VPN подписка",
		description=f"Доступ к VPN на {SUB_DAYS} дней",
		payload="vpn_sub",
		currency="XTR",  # Telegram Stars
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


async def send_key(tg_id: int):
	sub_url = await get_subscription_url(tg_id)

	# QR-код для подписки
	img = qrcode.make(sub_url)
	buf = io.BytesIO()
	img.save(buf, format="PNG")
	buf.seek(0)

	# deep-link: открыть подписку прямо в клиенте v2RayTun
	deep = f"v2raytun://import/{sub_url}"
	kb = InlineKeyboardMarkup(
		inline_keyboard=[[InlineKeyboardButton(text="📲 Открыть в v2RayTun", url=deep)]]
	)

	await bot.send_photo(
		chat_id=tg_id,
		photo=BufferedInputFile(buf.read(), filename="vpn.png"),
		caption=(
			"✅ Подписка активна!\n\n"
			f"Ссылка-подписка:\n`{sub_url}`\n\n"
			"Отсканируй QR в приложении v2RayTun / Hiddify "
			"или нажми кнопку ниже для импорта в один тап."
		),
		parse_mode="Markdown",
		reply_markup=kb,
	)


async def main():
	await dp.start_polling(bot)


if __name__ == "__main__":
	asyncio.run(main())
