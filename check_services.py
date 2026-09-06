import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

ENDPOINTS = {
    "API Gateway": "http://localhost:8000/health",
    "Database Service": "http://localhost:5432/health",
    "Blockchain RPC Node": "http://localhost:8545",
    "Escrow Protocol Module": "http://localhost:5000/status"
}

async def check_service(session, name, url):
    try:
        async with session.get(url, timeout=3) as response:
            if response.status == 200:
                logging.info(f"[ХЭВИЙН] {name} бүрэн холбогдсон ({url})")
                return True
            else:
                logging.warning(f"[АНХААРУУЛГА] {name} алдаатай код буцаалаа: {response.status}")
                return False
    except Exception as e:
        logging.error(f"[ТАСАРСАН] {name} холбогдож чадсангүй ({url}). Шалтгаан: {e}")
        return False

async def main():
    logging.info("Системийн нэгдсэн холболт болон ажиллагааны шалгалт эхэлж байна...")
    async with aiohttp.ClientSession() as session:
        tasks = [check_service(session, name, url) for name, url in ENDPOINTS.items()]
        results = await asyncio.gather(*tasks)

        if all(results):
            logging.info("Бүх бүрэлдэхүүн хэсгүүд хоорондоо амжилттай холбогдож, нэгдмэл байдлаар ажиллаж байна.")
        else:
            logging.warning("Системийн зарим зангилаа холболтод алдаа гарлаа. Дээрх логыг шалгана уу.")

if __name__ == "__main__":
    asyncio.run(main())
