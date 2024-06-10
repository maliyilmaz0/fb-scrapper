import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import time
from bs4 import BeautifulSoup
import re
import sys

if __name__ == "__main__":
    sys.path.append('..')

from db.db import get_cursor
from db.sql import GET_SETTINGS, START_PROCCES, GET_PROCESS_BY_ID

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
    """
    Inserts a colon and a space between the last lowercase letter and the first uppercase letter.
    Args:
    text (str): The input string.

    Returns:
    str: The modified string with a colon and a space inserted.
    """
    return re.sub(r"([a-z])([A-Z])", r"\1: \2", text)


# Initialize an empty list to store the post data
all_posts = []


class Selenium:
    def __init__(self, process_id: int):
        self.post_count = None
        self.process_id = process_id
        self.db = get_cursor(True)
        self.uname = None
        self.passwd = None
        self.logged_in = False
        self.fails: list = []
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
            wait = WebDriverWait(driver, 4)
            try:
                print("Closing popup...")
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Close"]')))
                element.click()
            except Exception as ex:
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Kapat"]')))
                element.click()
            self.is_popup_closed = True


    def login(self, driver):

        if self.uname is not None and self.passwd is not None and not self.logged_in:
            print("Logging in...")
            username_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']")))
            password_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass']")))
            username_element.clear()
            username_element.send_keys(str(self.uname))
            password_element.clear()
            password_element.send_keys(str(self.passwd))
            try:
                WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='Accessible login button']"))).click()
            except TimeoutException:
                WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button"))).click()
            self.logged_in = True

    def start_process(self):
        self.get_settings()
        process = self.get_process()
        items = process.get("items")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.scrape_item, item): item for item in items}
            for future in as_completed(futures):
                item = futures[future]
                try:
                    result = future.result()
                    all_posts.extend(result)
                except Exception as e:
                    print(f"Error processing item {item}: {e}")
                    self.fails.append(item)

        if self.fails:
            print(f"Failed to scrape posts for: {self.fails}")
            items = [f"groups/{group}" if group is not None else None for group in self.fails]
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(self.scrape_item, item): item for item in items}
                for future in as_completed(futures):
                    item = futures[future]
                    try:
                        result = future.result()
                        all_posts.extend(result)
                    except Exception as e:
                        print(f"Error processing item {item}: {e}")

        return True

    def scrape_item(self, item):
        # Set up GeckoDriver service
        service = Service(GeckoDriverManager().install())

        # Create a WebDriver instance
        driver = webdriver.Firefox(service=service)

        try:
            driver.get(f"https://www.facebook.com/{item}")
            try:
                self.close_popup(driver)
                self.login(driver)
            except Exception as e:
                print(f"Error logging in: {e}")
                pass
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
        result = {
            "about_overview": [],
            "about_work_and_education": [],
            "about_places": [],
            "about_contact_and_basic_info": [],
            "about_family_and_relationships": [],
            "about_details": [],
            "about_life_events": [],
            "about_profile_transparency": [],

        }
        for page in about_pages:
            try:
                driver.get(f"https://www.facebook.com/{search}/{page}")
                time.sleep(5)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                details = soup.find_all('div', class_='x1hq5gj4')
                for detail in details:
                    if len(detail.get_text(separator=' ', strip=True)) > 0:
                        result[page].append(detail.get_text(separator=' ', strip=True))

            except:
                try:
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    details = soup.find_all('div', class_='x13faqbe x78zum5 xdt5ytf')
                    for detail in details:
                        if len(detail.get_text(separator=' ', strip=True)) > 0:
                            result[page].append(detail.get_text(separator=' ', strip=True))
                except Exception as e:
                    print(f"Error getting about: {e}")
                    pass
        return result

    def extract_posts(self, driver, search):
        print("Extracting posts...")

        response = []
        try:
            last_height = driver.execute_script(
                "return document.body.scrollHeight"
            )
            results = {"posts": [], "key": "", "about": {}, "user_id": None}

            if search is None:
                return results
            print(f"Scraping posts for {search}")
            try:
                driver.get(f"https://www.facebook.com/{search}")
                try:
                    self.close_popup(driver)
                    self.login(driver)
                except Exception as e:
                    print(f"Error logging in: {e}")
                    pass
                results["about"] = self.get_about(driver, search)
                try:
                    driver.get(f"https://mbasic.facebook.com/{search}")
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    res = soup.find_all("span", class_="de dm ba")
                    for element in res:
                        link = element.find('a')
                        if link:
                            href = link.get('href')
                            if href:
                                parts = href.split('/')
                                if len(parts) > 1:
                                    results["user_id"] = parts[1]
                except Exception as e:
                    print(f"Error getting user id: {e}")
                    pass
                driver.get(f"https://www.facebook.com/{search}")
                time.sleep(5)
                while True:
                    # Scroll down to bottom
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);"
                    )

                    # Wait to load page
                    time.sleep(3)
                    # Calculate new scroll height and compare with last scroll height
                    new_height = driver.execute_script(
                        "return document.body.scrollHeight"
                    )
                    if new_height == last_height:
                        print("Reached the end of the page. Trying Group Posts...")
                        self.fails.append(search if results["key"] != search and search not in self.fails else None)
                        break
                    last_height = new_height

                    # Extract posts and comments after the page has loaded
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    posts = soup.find_all("div", class_="x78zum5 x1n2onr6 xh8yej3")
                    for post in posts:
                        post_content = post.find(
                            "div", class_="x1iorvi4 x1pi30zi x1l90r2v x1swvt13"
                        )
                        if post_content and post_content.text not in results["posts"]:
                            results["posts"].append(post_content.text)
                            results["key"] = search
                    if len(results["posts"]) >= self.post_count:
                        response.append(results)
                        results = {"posts": [], "key": ""}
                        break
            except Exception as e:
                print(f"Error scraping posts: {e}")
                pass


        except Exception as e:
            print(f"Error scraping posts: {e}")
        driver.quit()
        return response

    def write_to_db(self, data):
        """
        Writes the data to the database.

        Args:
        data (list): The list of posts to write to the database.

        Returns:
        None
        """
        pass


if __name__ == "__main__":
    # Create an instance of Selenium
    selenium = Selenium(process_id=1)

    # Extract posts and comments
    results = selenium.start_process()

    # Write the list of posts to a JSON file
    with open("facebook_posts.json", "w", encoding="utf-8") as file:
        json.dump(all_posts, file, ensure_ascii=False, indent=4)
