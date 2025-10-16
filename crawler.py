import time
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

class WosCrawler:
    def __init__(self, efficiency=1):
        options = webdriver.ChromeOptions()
        # 1) 无头 + 窗口大小
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        # 2) UA 与反检测
        ua = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/138.0.0.0 Safari/537.36')
        options.add_argument(f'--user-agent={ua}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        # 3) 资源禁用
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheet": 2,
        }
        options.add_experimental_option("prefs", prefs)
        # 4) 系统级减负
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--enable-unsafe-swiftshader')
        # 5) 只创建一次 driver
        self.driver = webdriver.Chrome(options=options)
        self.efficiency = efficiency # 控制爬取速度，sep_time = time / efficiency

def get_info():
    """
    尝试获取所有需爬取机构的信息
    table: all_info
    school | address | url | result_count | page_count | crawled_or_not
    """

def set_crawled(institution):
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE infos SET crawled_or_not = 1 WHERE institution = ?;
        ''', (institution,))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error setting crawled:", e)

def page_extract_data(institution):
    # Extract data from the page
    count = 0
    pass
    save_data(data)

    return count

def show_ye():
    try:
        show = driver.find_elements(By.XPATH, "//dd[@field='YE']//a[@class='btn']")
        if not show:
            print("No year button found")
        else:
            show = show[0]
            show.click()
    except Exception as e:
        print("Error showing year:", e)

def click_ye():
    try:
        els = driver.find_elements(By.XPATH, "//dd[@field='YE']//li")
        if not els:
            YE = driver.find_element(By.XPATH, "//dt[@groupid='YE']//b")
            YE.click()
            return False
        else:
            return True
    except Exception as e:
        print("Error examining year:", e)
        return False

def crawl_data(institution, url, result_count, page_count):
    driver.get(url)
    time.sleep(2)
    driver.refresh()
    time.sleep(1)
    suc_ = switch_to_50_per_page()
    time.sleep(1)
    page_count = result_count // 20 + (1 if result_count % 20 > 0 else 0) if not suc_ else page_count
    time.sleep(0.5)
    count = 0

    for i in range(1, page_count + 1):
        count += page_extract_data(institution)
        print(f"{institution}:{i}/{page_count}-{count}/{result_count}")

        if i < page_count:
            try:
                next_page = driver.find_element(By.XPATH, "//a[@class='pagesnums']")
                driver.execute_script("arguments[0].click();", next_page)
            except Exception as e:
                print("Error clicking next page:", e)
            time.sleep(1)
    
    set_crawled(institution)

def save_data(data):
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                institution TEXT,
                name TEXT NOT NULL,
                author TEXT,
                source TEXT,
                date TEXT,
                data TEXT,
                quote TEXT,
                download TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, author, source, date, data, quote, download)
            );
        ''')
        cursor.execute("INSERT OR IGNORE INTO papers (institution, name, author, source, date, data, quote, download) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (data['institution'],
                    data['name'],
                    data['author'],
                    data['source'],
                    data['date'],
                    data['data'],
                    data['quote'],
                    data['download']
                    ))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error saving data:", e)


