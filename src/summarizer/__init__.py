import asyncio
from pyppeteer import launch
from random import uniform
import time

async def type_like_human(page, selector, text):
    await page.focus(selector)
    for char in text:
        await page.keyboard.type(char)
        await asyncio.sleep(uniform(0.1, 0.4)) # Simulate random typing speed

async def main():
    browser = await launch(headless=False)
    page = await browser.newPage()

    # Set user agent to make it look like a human
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    await page.setUserAgent(user_agent)

    await page.setViewport({'width': 1280, 'height': 800})

    await page.goto('https://chat.openai.com')
    time.sleep(1)

    # Fill out a form or interact with elements like a human
    await page.click('/html/body/div[1]/div[1]/div[1]/div[4]/button[1]')
    await type_like_human(page, '#username', 'my_username')
    await type_like_human(page, '#password', 'my_password')
    await asyncio.sleep(uniform(0.5, 1)) # Random pause before clicking

    # Click the login button
    await page.click('#login-btn')

    # Wait for the navigation to complete
    await page.waitForNavigation()

    # Do other tasks after logging in...

    await asyncio.sleep(10)
    await browser.close()

asyncio.run(main())
