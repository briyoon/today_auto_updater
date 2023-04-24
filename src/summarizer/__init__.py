import time
from playwright.sync_api import sync_playwright
from random import uniform

def type_like_human(page, selector, text):
    element = page.locator(selector)
    element.click()
    for char in text:
        element.type(char)
        time.sleep(uniform(0.1, 0.4)) # Simulate random typing speed

def cognitive_delay():
    time.sleep(uniform(0.5, 1.5))

def main():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)

        # Set user agent to make it look like a human
        # user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'

        # Create a new page with the specified user agent
        page = browser.new_page()

        page.set_viewport_size({'width': 1280, 'height': 800})

        page.goto('https://chat.openai.com')

        page.wait_for_load_state('networkidle')

        cognitive_delay()
        # Click sign in


        # enter username then press continue

        # enter password then press continue



        time.sleep(10)
        browser.close()

main()
