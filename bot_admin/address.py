import aiohttp

# Проверяет существование адреса через Google Maps и возвращает ссылку на него или None
async def validate_address(address: str) -> str | None:
    url = (
        "https://www.google.com/maps/search/"
        f"?api=1&query={address.replace(' ', '+')}"
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            text = await resp.text()

            if "did not match any locations" in text.lower():
                return None

            return url