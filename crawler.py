import time
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

class WosCrawler:
    def __init__(self, efficiency=1, once_want=None, headless=True):
        self.total_address = 0
        self.total_url = 0
        self.total_crawled = 0
        self.driver = self.init_driver(headless=headless)
        self.efficiency = efficiency # 控制爬取速度，sep_time = time / efficiency
        self.once_want = once_want # 每次想要爬取的数量，None表示全部爬取

    def init_driver(self, headless=True):
        options = webdriver.ChromeOptions()
        # 1) 无头 + 窗口大小
        if headless:
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
        return webdriver.Chrome(options=options)
    
    def restart_driver(self, headless=True):
        try:
            self.driver.quit()
        except:
            pass
        print("Restart driver")
        self.driver = self.init_driver(headless=headless)

    def fetch_info(self):
        """
        尝试获取所有需爬取机构的信息
        table: infos
        school | address | url | result_count | page_count | crawled_or_not
        1. school: 机构名称
        2. address: 机构地址
        3. url: 机构对应的 WOS 地址
        4. result_count: 该机构的结果总数
        5. page_count: 该机构的结果总页数
        6. crawled_or_not: 是否已爬取，0 未爬取，1 已爬取
        """
        if self.check_info():
            print("All institutions have been crawled.")
            return []
        else:
            try:
                conn = sqlite3.connect('data.db')
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT school, address, url, result_count, page_count 
                    FROM infos WHERE crawled_or_not = 0;
                ''')
                results = cursor.fetchall()
            except Exception as e:
                print("Error fetching info:", e)
                return []
            finally:
                conn.close()
            return results

    def check_info(self):
        """
        检查infos情况:
        各school的address数量，其中url存在占比，其中crawled_or_not=1占比
        汇总address数量，url存在数量，crawled_or_not=1数量
        """
        try:
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT school, COUNT(address) AS address_count,
                    SUM(CASE WHEN url IS NOT NULL THEN 1 ELSE 0 END) AS url_count,
                    SUM(CASE WHEN crawled_or_not = 1 THEN 1 ELSE 0 END) AS crawled_count
                FROM infos
                GROUP BY school
            ''')
            results = cursor.fetchall()
        except Exception as e:
            print("Error checking info:", e)
            return False
        finally:
            conn.close()

        for row in results:
            print(f"{row[0]}, Address: {row[1]}, URL: {row[2]}/{row[1]}, Crawled: {row[3]}/{row[1]}")
            self.total_address += row[1]
            self.total_url += row[2]
            self.total_crawled += row[3]
        print(f"Total, Address: {self.total_address}, URL: {self.total_url}, Crawled: {self.total_crawled}")

        return self.total_address == self.total_crawled

    def crawl_address(self, school, address):
        self.driver.get("https://webofscience.clarivate.cn/wos/woscc/advanced-search")
        self.accept_cookies()
        time.sleep(1 / self.efficiency)
        # 构建检索式
        AD = f"AD=({address})"
        search_box = self.driver.find_element(By.XPATH, "//textarea")
        search_box.clear()
        search_box.send_keys(AD)
        # 点击检索
        search_button = self.driver.find_element(By.XPATH, "//div[@class='upper-search-preview-holder']//div[@class='button-row adv ng-star-inserted']//button[@mat-ripple-loader-class-name='mat-mdc-button-ripple'][2]")
        search_button.click()
        time.sleep(1 / self.efficiency)
        # 获取基本数据
        result_count = int(self.driver.find_element(By.XPATH, "//span[@class='brand-blue']").text.replace(',', ''))
        page_count = int(self.driver.find_element(By.XPATH, "//span[@class='end-page ng-star-inserted']").text.replace(',', ''))
        base_url = str(self.driver.current_url)[:-1]
        time.sleep(0.5 / self.efficiency)
        
        crawled_count = 0
        crawled_page_count = self.continue_crawl(school, address)
        self.to_page(crawled_page_count + 1)
        # 开始翻页爬取
        for i in range(1, page_count + 1):
            if crawled_page_count and i <= crawled_page_count:
                crawled_count += 50
                print(f"{address}:\t{i}/{page_count}-{crawled_count}/{result_count} (continued)")
            else:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//app-records-list")
                    )
                )
                # crawl
                crawled_count += self.crawl_page(school, address)
                print(f"{address}:\t{i}/{page_count}-{crawled_count}/{result_count}")
                self.next_page_b()
        if result_count <= page_count * 50:
            self.set_crawled(address, url=base_url, result_count=result_count, page_count=page_count)
            print(f"{address} Successed")
            return True
        else:
            print(f"{address} Failed")
            return False
        
    def set_crawled(self, address, url=None, result_count=None, page_count=None):
        try:
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE infos SET crawled_or_not = 1, url = ?, result_count = ?, page_count = ? WHERE address = ?;
            ''', (url, result_count, page_count, address))
            conn.commit()
        except Exception as e:
            print("Error setting crawled:", e)
        finally:
            conn.close()

    def crawl_page(self, school, address):
        # Extract data from the page
        crawled_count = 0
        data = []  # Placeholder for extracted data
        base_xpath = "//app-records-list/app-record"
        page_length = len(self.driver.find_elements(By.XPATH, base_xpath))

        for i in range(page_length):
            item_xpath = f"{base_xpath}[{i + 1}]"
            btn_xpath = f"{item_xpath}//button[contains(@class,'show-more')]"
            title_xpath = f"{item_xpath}//a[contains(@class, 'title')]"
            wos_id_xpath = title_xpath
            author_xpath = f"{item_xpath}//a[@class='mat-mdc-tooltip-trigger authors ng-star-inserted']"
            sep_xpath = f"{item_xpath}//app-summary-authors/div/span"
            pub_date_xpath = [
                f"{item_xpath}//span[@class='source-info-piece ng-star-inserted']/span",
                f"{item_xpath}//span[@name='pubdate']"
            ]
            conference_xpath = f"{item_xpath}//span[@name='conf_title']"
            source_xpath = [
                f"{item_xpath}//app-jcr-sidenav//span[@class='summary-source-title noLink ng-star-inserted']",
                f"{item_xpath}//app-jcr-sidenav//a[@cdxanalyticscategory='wos-recordCard_Journal_Info']//span"
            ]
            citations_xpath = f"{item_xpath}//div[@class='no-bottom-border citations ng-star-inserted']//a"
            refs_xpath = f"{item_xpath}//div[@class='link-container ng-star-inserted']//a"
            abstract_xpath = f"{item_xpath}//div[contains(@class,'abstract')]//p"

            try:
                btn = self.driver.find_element(By.XPATH, btn_xpath)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, btn_xpath)
                    )
                )
                self.driver.execute_script("arguments[0].scrollIntoView();", btn)
                time.sleep(0.4 / self.efficiency)
                btn.click()
            except:
                pass
            # 开始爬取各字段
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, title_xpath)
                )
            )
            title = self.driver.find_element(By.XPATH, title_xpath).text
            wos_id = self.driver.find_element(By.XPATH, wos_id_xpath).get_attribute('href').split('WOS:')[-1]
            # //app-records-list/app-record//a[@class='mat-mdc-tooltip-trigger authors ng-star-inserted']//span
            # //app-records-list/app-record//app-summary-authors/div/span
            authors = []
            authors_length = len(self.driver.find_elements(By.XPATH, author_xpath))
            # if authors_length == 0:
            #     authors = None
            # elif authors_length == 1:
            #     authors = self.driver.find_element(By.XPATH, author_xpath).text
            # else:
            for j in range(authors_length):
                author = self.driver.find_element(By.XPATH, f"{author_xpath}[{j + 1}]//span").text
                authors.append(author)
            sep_length = len(self.driver.find_elements(By.XPATH, sep_xpath))
            for j in range(sep_length):
                sep = self.driver.find_element(By.XPATH, f"{sep_xpath}[{j + 1}]").text.strip()
                if sep == '(...);':
                    authors.insert(2, '...')
            authors = '; '.join(authors)
            # //app-records-list/app-record//span[@class="source-info-piece ng-star-inserted"]/span
            try:
                pub_date = self.driver.find_element(By.XPATH, pub_date_xpath[1]).text
            except:
                try:
                    pub_date = self.driver.find_element(By.XPATH, pub_date_xpath[0]).text
                except:
                    pub_date = None
            # //app-records-list/app-record//span[@name="conf_title"]
            try:
                conference = self.driver.find_element(By.XPATH, conference_xpath).text
            except:
                conference = None
            # //app-records-list/app-record//app-jcr-sidenav//span[@class="summary-source-title noLink ng-star-inserted"]
            # //app-records-list/app-record//app-jcr-sidenav//a[@cdxanalyticscategory="wos-recordCard_Journal_Info"]//span
            try:
                source = self.driver.find_element(By.XPATH, source_xpath[0]).text
            except:
                try:
                    source = self.driver.find_element(By.XPATH, source_xpath[1]).text
                except:
                    source = None
            # //app-records-list/app-record//div[@class="no-bottom-border citations ng-star-inserted"]//a
            try:
                citations = int(self.driver.find_element(By.XPATH, citations_xpath).text)
            except:
                citations = 0
            # //app-records-list/app-record//div[@class="link-container ng-star-inserted"]//a
            try:
                refs = int(self.driver.find_element(By.XPATH, refs_xpath).text)
            except:
                refs = 0
            # //app-records-list/app-record[45]//div[contains(@class,"abstract")]//p
            try:
                self.driver.find_element(By.XPATH, abstract_xpath)
                abs_length = len(self.driver.find_elements(By.XPATH, abstract_xpath))
                if abs_length == 0:
                    abstract = None
                else:
                    for j in range(abs_length):
                        para = self.driver.find_element(By.XPATH, f"{abstract_xpath}[{j + 1}]").text
                        if j == 0:
                            abstract = para
                        else:
                            abstract += '\n' + para
            except:
                abstract = None

            data.append((address, title, authors, pub_date, conference, source, citations, refs, wos_id, abstract))
            crawled_count += 1
        self.save_data(data, school)
        # 释放data
        data.clear()
        return crawled_count

    def save_data(self, data, school):
        try:
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.executemany('''
                INSERT INTO {} (address, title, authors, pub_date, conference, source, citations, refs, wos_id, abstract) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            '''.format(school), data)
            conn.commit()
        except Exception as e:
            print("Error saving data:", e)
        finally:
            conn.close()

    def next_page_t(self):
        # //button[@aria-label="Top Next Page"]
        next_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Top Next Page']")
        try:
            self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
            time.sleep(0.2 / self.efficiency)
            next_button.click()
        except Exception as e:
            self.driver.execute_script("arguments[0].click();", next_button)

    def next_page_b(self):
        # //button[@aria-label="Bottom Next Page"]
        next_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Bottom Next Page']")
        try:
            self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
            time.sleep(0.2 / self.efficiency)
            next_button.click()
        except Exception as e:
            self.driver.execute_script("arguments[0].click();", next_button)
    
    def to_page(self, page_num):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@id='snNextPageTop']")
            )
        )
        page_input = self.driver.find_element(By.XPATH, "//input[@id='snNextPageTop']")
        page_input.clear()
        page_input.send_keys(str(page_num))
        time.sleep(1 / self.efficiency)

    def accept_cookies(self):
        try:
            accept_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@id='onetrust-accept-btn-handler']"))
            )
            accept_button.click()
            time.sleep(1 / self.efficiency)
        except Exception as e:
            print("No cookies prompt")

    def continue_crawl(self, school, address):
        """断点续爬"""
        # 统计已有数据量
        try:
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM {} WHERE address = ?;
            '''.format(school), (address,))
            existing_count = cursor.fetchone()[0]
        except Exception as e:
            print("Error fetching existing count:", e)
        finally:
            conn.close()
            if existing_count:
                return existing_count // 50

    def crawl(self):
        # 主爬取逻辑
        infos = self.fetch_info()
        print(f"Remain to crawl: {len(infos)}")
        print(f"once_want: {self.once_want}")
        if not infos:
            print("---Finished---")
            return
        count = 0
        for info in infos:
            school, address, _, _, _ = info
            success = self.crawl_address(school, address)
            # try:
            #     success = self.crawl_address(school, address)
            # except Exception as e:
            #     print(f"{address} Failed Totally:\n{e}")
            #     continue
            if success:
                count += 1
            if self.once_want and count >= self.once_want:
                break
        self.driver.quit()

if __name__ == "__main__":
    crawler = WosCrawler(efficiency=1, once_want=None, headless=False)
    crawler.crawl()