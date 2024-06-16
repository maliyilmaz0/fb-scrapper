import asyncio
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import time
from bs4 import BeautifulSoup
import re
import sys

if __name__ == "__main__":
    sys.path.append('..')

from db.db import get_cursor
from db.sql import GET_SETTINGS, START_PROCCES, GET_PROCESS_BY_ID, INSERT_RESULTS, FINISH_PROCCES

about_pages = [
    "about_overview",
    "about_work_and_education",
    "about_places",
    "about_contact_and_basic_info",
    "about_family_and_relationships",
    "about_details",
    "about_life_events",
    "about_profile_transparency",
]


def add_colon_between_names(text):
    return re.sub(r"([a-z])([A-Z])", r"\1: \2", text)


class SeleniumScraper:
    def __init__(self, process_id: int):
        self.process_id = process_id
        self.db = get_cursor(True)
        self.post_count = 3
        self.uname = None
        self.passwd = None
        self.logged_in = False
        self.fails = []
        self.is_popup_closed = False

    def get_settings(self):
        self.db.execute(GET_SETTINGS)
        settings = self.db.fetchone()
        self.post_count = settings.get("post_count", 3)
        self.uname = settings.get("uname", None)
        self.passwd = settings.get("passwd", None)

    def get_process(self):
        self.db.execute(START_PROCCES, (datetime.now(), self.process_id))
        self.db.execute(GET_PROCESS_BY_ID, (self.process_id,))
        return self.db.fetchone()

    def close_popup(self, driver):
        if not self.is_popup_closed:
            wait = WebDriverWait(driver, 10)
            try:
                print("Closing popup...")
                element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[aria-label="Close"]')))
                element.click()
            except TimeoutException:
                try:
                    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[aria-label="Kapat"]')))
                    element.click()
                except TimeoutException:
                    print("Popup close button not found.")
            self.is_popup_closed = True

    def login(self, driver):
        if self.uname and self.passwd:
            print("Logging in...")
            try:
                username_element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']")))
                password_element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass']")))
                username_element.clear()
                username_element.send_keys(self.uname)
                password_element.clear()
                password_element.send_keys(self.passwd)
                login_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='Accessible login button'], button")))
                login_button.click()
            except TimeoutException as e:
                print(f"Error logging in: {e}")

    async def start_process(self):
        self.get_settings()
        process = self.get_process()
        items = process.get("items")
        all_posts = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            loop = asyncio.get_event_loop()
            tasks = [loop.run_in_executor(executor, self.scrape_item, item) for item in items]
            results = await asyncio.gather(*tasks)
            all_posts.extend(results)
        if self.fails:
            print(f"Retrying failed items: {self.fails}")
            with ThreadPoolExecutor(max_workers=3) as executor:
                retry_tasks = [loop.run_in_executor(executor, self.scrape_item, "groups/"+item) for item in self.fails]
                retry_results = await asyncio.gather(*retry_tasks)
                all_posts.extend(retry_results)

        self.write_to_db(all_posts)

    def scrape_item(self, item):
        options = Options()
        options.headless = False

        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        try:
            driver.get(f"https://www.facebook.com/{item}")
            try:
                time.sleep(5)
                self.close_popup(driver)
                time.sleep(2)
                self.login(driver)
                time.sleep(5)
            except Exception as e:
                print(f"Error: {e}")
                self.close_popup(driver)
            time.sleep(5)
            result = self.extract_posts(driver, item)
        except Exception as e:
            print(f"Error scraping posts: {e}")
            result = []
        finally:
            driver.quit()
        return result

    def get_about(self, driver, search):
        print("Getting about...")
        result = {page: [] for page in about_pages}
        for page in about_pages:
            try:
                driver.get(f"https://www.facebook.com/{search}/{page}")
                time.sleep(5)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                details = soup.find_all('div', class_='x1hq5gj4')
                for detail in details:
                    text = detail.get_text(separator=' ', strip=True)
                    if text:
                        result[page].append(text)
            except Exception as e:
                print(f"Error getting about: {e}")
        return result

    def extract_posts(self, driver, search):
        print("Extracting posts...")
        results = {"posts": [], "key": "", "about": {}, "user_id": None}

        try:
            results["key"] = search
            last_height = driver.execute_script("return document.body.scrollHeight")

            try:
                driver.get(f"https://mbasic.facebook.com/{search}")
                soup = BeautifulSoup(driver.page_source, "html.parser")
                res = soup.find_all("td", valign="top")
                for element in res:
                    link = element.find('a')
                    if link:
                        href = link.get('href')
                        if href:
                            parts = href.split('/')
                            if len(parts) > 1:
                                results["user_id"] = parts[1]
                                break
            except Exception as e:
                print(f"Error getting user id: {e}")

            driver.get(f"https://www.facebook.com/{search}")
            time.sleep(5)
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("Reached the end of the page.")
                    break
                last_height = new_height

                soup = BeautifulSoup(driver.page_source, "html.parser")
                posts = soup.find_all("div", class_="x78zum5 x1n2onr6 xh8yej3")
                if posts:
                    for post in posts:
                        post_content = post.find("div", class_="x1iorvi4 x1pi30zi x1l90r2v x1swvt13")
                        if post_content and post_content.text not in results["posts"]:
                            results["posts"].append(post_content.text)
                            results["key"] = search
                else:
                    print("No posts found.")
                    self.fails.append(search if results["key"] != search and search not in self.fails else None)
                    break
                if len(results["posts"]) >= self.post_count:
                    break
            results["about"] = self.get_about(driver, search)
        except Exception as e:
            print(f"Error scraping posts: {e}")
        return results

    def write_to_db(self, data):
        self.db.execute(INSERT_RESULTS, (self.process_id, json.dumps(data, default=str)))
        self.db.execute(FINISH_PROCCES, (datetime.now(), self.process_id))


if __name__ == "__main__":
    process_id = sys.argv[1]
    scraper = SeleniumScraper(process_id)
    asyncio.run(scraper.start_process())
