import time
import httpx
from config import MARZBAN_URL, MARZBAN_USER, MARZBAN_PASS, SUB_DAYS

_token = {"value": None, "exp": 0}


async def _get_token() -> str:
	if _token["value"] and _token["exp"] > time.time():
		return _token["value"]
	async with httpx.AsyncClient(base_url=MARZBAN_URL, timeout=15) as c:
		r = await c.post(
			"/api/admin/token",
			data={"username": MARZBAN_USER, "password": MARZBAN_PASS},
		)
		r.raise_for_status()
		tok = r.json()["access_token"]
		_token["value"] = tok
		_token["exp"] = time.time() + 3000
		return tok


async def create_or_renew_user(tg_id: int) -> dict:
	"""Создаёт пользователя в Marzban или продлевает подписку. Возвращает ключи."""
	token = await _get_token()
	headers = {"Authorization": f"Bearer {token}"}
	username = f"tg_{tg_id}"
	expire = int(time.time()) + SUB_DAYS * 86400

	payload = {
		"username": username,
		"proxies": {"vless": {}},
		"inbounds": {},  # пусто = все активные инбаунды
		"expire": expire,
		"data_limit": 0,  # 0 = безлимит
		"status": "active",
	}

	async with httpx.AsyncClient(base_url=MARZBAN_URL, timeout=15) as c:
		# пробуем создать
		r = await c.post("/api/user", headers=headers, json=payload)
		if r.status_code == 409:
			# уже существует -> продлеваем
			r = await c.put(
				f"/api/user/{username}",
				headers=headers,
				json={"expire": expire, "status": "active"},
			)
		r.raise_for_status()
		return r.json()


async def get_subscription_url(tg_id: int) -> str:
	"""Возвращает subscription-ссылку пользователя."""
	token = await _get_token()
	headers = {"Authorization": f"Bearer {token}"}
	username = f"tg_{tg_id}"
	async with httpx.AsyncClient(base_url=MARZBAN_URL, timeout=15) as c:
		r = await c.get(f"/api/user/{username}", headers=headers)
		r.raise_for_status()
		data = r.json()
		return MARZBAN_URL + data["subscription_url"]
