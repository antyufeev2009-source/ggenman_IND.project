import asyncio
import sys
from aiohttp_socks import ProxyConnector
from aiohttp import web, ClientSession

# Данные вашей Amnezia SOCKS5
SOCKS5_URL = "socks5://proxy_user:GKxnDKsJNlmaFxXL@193.233.115.130:41247"

async def handle(request):
    method = request.method
    url = str(request.url)
    headers = {k: v for k, v in request.headers.items() if k.lower() != 'host'}
    data = await request.read()
    
    connector = ProxyConnector.from_url(SOCKS5_URL)
    async with ClientSession(connector=connector) as session:
        async with session.request(method, url, headers=headers, data=data, timeout=30) as resp:
            body = await resp.read()
            return web.Response(body=body, status=resp.status, headers=dict(resp.headers))

app = web.Application()
app.router.add_route('*', '/{tail:.*}', handle)

if __name__ == '__main__':
    print("Локальный переходник SOCKS5 -> HTTP успешно запущен на порту 1080!")
    sys.stdout.flush()
    web.run_app(app, port=1080)
