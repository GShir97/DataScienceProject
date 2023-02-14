from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# Use ChromeDriver as the web driver
driver = webdriver.Chrome()
# driver.implicitly_wait(12)

# Navigate to the category
category_url_map = {
    "military": "https://www.mako.co.il/news-military",
    "politics": "https://www.mako.co.il/news-politics",
    "law": "https://www.mako.co.il/news-law",
    "world": "https://www.mako.co.il/news-world",
    "economy": "https://www.mako.co.il/news-money",
    "entertainment": "https://www.mako.co.il/news-entertainment"
}

category_data = {
}


def extract_data_from_article(element: WebElement, data):
    # use the keyboard shortcut "Ctrl + click" to open the link in a new tab
    element.send_keys(Keys.CONTROL + Keys.RETURN)

    # switch to the new tab
    driver.switch_to.window(driver.window_handles[-1])

    article_full_body = driver.find_element(By.XPATH, "//div[@id='article-wrap']/article")
    header_top = article_full_body.find_element(By.XPATH, ".//section[@class='article-header']")
    header_container = header_top.find_element(By.XPATH, "./header")
    data['long_title'] = header_container.find_element(By.XPATH, "./h1").text
    data['short_description'] = header_container.find_element(By.XPATH, "./h2").text
    header_writer_container = header_container.find_element(By.XPATH, ".//div[@class='writer-data']")
    all_reporters_elements = header_writer_container.find_elements(By.XPATH, "./span[@itemprop='author']")
    all_reporters = [driver.execute_script("return arguments[0].getAttribute('content');", elem) for elem in
                     all_reporters_elements]
    data['all_reporters'] = all_reporters

    display_date_elem = header_container.find_element(By.XPATH, ".//span[@class='display-date']")
    display_date_text = display_date_elem.text
    dates = display_date_text.strip().split('|')[1:]
    data['publish_timedate'], data['last_update_timedate'] = [date.strip('פורסםעודכן ') for date in dates]
    data['views'] = int(header_top.find_element(By.XPATH, ".//li[@class='views']").text.replace(',', ''))
    data['category'] = article_full_body.find_element(By.XPATH, ".//nav/span/ul/li[@class=' here']").text
    content_body_elem = article_full_body.find_element(By.XPATH, ".//section[@class='article-body']")
    p_elements = content_body_elem.find_elements(By.XPATH, "./p")
    data['content'] = '\n\n'.join([p.text for p in p_elements])
    vote_elem = driver.find_element(By.XPATH, "//div[@id='feelingsWrapper']")
    tags_elem = content_body_elem.find_element(By.XPATH, ".//ul[@class='tags']")
    # need to scroll into view so interest would load
    driver.execute_script("arguments[0].scrollIntoView();", tags_elem)
    vote_elem_interested = vote_elem.find_element(By.XPATH, ".//a[@data-index='0']")
    vote_elem_not_interested = vote_elem.find_element(By.XPATH, ".//a[@data-index='1']")
    data['article_interest']['interested'] = driver.execute_script(
        "return arguments[0].getAttribute('data-display');", vote_elem_interested)
    data['article_interest']['not_interested'] = driver.execute_script(
        "return arguments[0].getAttribute('data-display');", vote_elem_not_interested)

    # close the window the article
    driver.close()
    driver.switch_to.window(driver.window_handles[0])


def run_scraping():
    for category in category_url_map:
        driver.get(category_url_map[category])

        article_data = {
            "title": "",
            "long_title": "",
            "short_description": "",
            "publish_timedate": "",
            "last_update_timedate": "",
            "main_reporter": "",
            "all_reporters": "",
            "views": "",
            "category": "",
            "article_content": "",
            "article_interest": {
                "interested": None,
                "not_interested": None,
            }
            # "article_type": "",  # podcast,article
        }

        # receives a link element, open it in new tab and scrap the data(from n12 category page format)

        articles_container = driver.find_element(By.XPATH, "//section[@class='regular content colx2']/ul")
        articles = articles_container.find_elements(By.XPATH, ".//li")
        articles_data = []
        for article in articles:
            article_link = article.find_element(By.XPATH, ".//strong/a")
            article_data['title'] = article_link.text
            article_data['main_reporter'] = article.find_element(By.XPATH, ".//small/span").text

            extract_data_from_article(article_link, article_data)
            articles_data.append(article_data)
            pass
        category_data[category] = articles_data


if __name__ == '__main__':
    run_scraping()


    # driver.get('https://www.mako.co.il/news-military?partner=NewsNavBar')
    # article_link = driver.find_element(By.XPATH, "//section[@class='regular content colx2']/ul")
    # test extract_data_from_article
    # extract_data_from_article()


# Close the web driver
driver.quit()
