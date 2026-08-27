FROM python:3.11-slim
RUN pip install --no-cache-dir aiohttp aiohttp_socks
WORKDIR /app
COPY proxy_bridge.py .
CMD ["python", "proxy_bridge.py"]
