import os
import base64
import aiohttp
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def main():
    token = os.getenv("SECURITY_BOT_TOKEN")
    if not token:
        print("No SECURITY_BOT_TOKEN found in .env")
        return

    banner_path = "assets/rai_sentinel_banner.jpg"
    if not os.path.exists(banner_path):
        print(f"File {banner_path} does not exist.")
        return

    with open(banner_path, "rb") as f:
        image_data = f.read()
    
    b64_image = f"data:image/jpeg;base64,{base64.b64encode(image_data).decode('utf-8')}"

    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        # 1. Update user banner (Bot Profile Banner)
        payload = {"banner": b64_image}
        async with session.patch("https://discord.com/api/v10/users/@me", json=payload, headers=headers) as resp:
            status = resp.status
            text = await resp.text()
            print(f"User banner update response [{status}]: {text}")

if __name__ == "__main__":
    asyncio.run(main())
