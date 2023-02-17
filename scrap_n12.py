import json
import math
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from selenium import webdriver
from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

# Use ChromeDriver as the web driver
driver = webdriver.Chrome()
# driver.implicitly_wait(12)

# Navigate to the category
category_url_map = {
    "military": "https://www.mako.co.il/news-military",
    #"world": "https://www.mako.co.il/news-world",
    "entertainment": "https://www.mako.co.il/news-entertainment",
    "economy": "https://www.mako.co.il/news-money",
    "politics": "https://www.mako.co.il/news-politics",
    "law": "https://www.mako.co.il/news-law"
}

# will contain all articles and their data
all_articles = {
    # "[name]":[data]
}

skip_count = 0
scrap_count = 0


def scrap_article_page(element: WebElement, data):
    # use the keyboard shortcut "Ctrl + click" to open the link in a new tab
    element.send_keys(Keys.CONTROL + Keys.RETURN)

    # switch to the new tab
    driver.switch_to.window(driver.window_handles[-1])

    print(f"Scraping article: {data['title']}")
    global scrap_count
    scrap_count += 1

    article_full_body = driver.find_element(By.XPATH, "//div[@id='article-wrap']/article")
    header_top = article_full_body.find_element(By.XPATH, ".//section[contains(@class,'article-header')]")
    header_container = header_top.find_element(By.XPATH, "./header")
    data['long_title'] = header_container.find_element(By.XPATH, "./h1").text
    data['short_description'] = header_container.find_element(By.XPATH, "./h2").text
    header_writer_container = header_container.find_element(By.XPATH, ".//div[@class='writer-data']")
    all_reporters_elements = header_writer_container.find_elements(By.XPATH, "./span[@itemprop='author']")
    all_reporters = [driver.execute_script("return arguments[0].getAttribute('content');", elem) for elem in
                     all_reporters_elements]
    data['all_reporters'] = all_reporters
    data['num_of_reporters'] = len(all_reporters)

    display_date_elem = header_container.find_element(By.XPATH, ".//span[@class='display-date']")
    display_date_text = display_date_elem.text
    dates = display_date_text.strip().split('|')[1:]
    dates_clean = [date.strip('פורסםעודכן ') for date in dates]
    data['publish_timedate'] = dates_clean[0]
    if len(dates_clean) > 1:
        data['last_update_timedate'] = dates_clean[1]
    data['views'] = int(header_top.find_element(By.XPATH, ".//li[@class='views']").text.replace(',', ''))
    try:
        data['category'] = article_full_body.find_element(By.XPATH, ".//nav/span/ul/li[@class=' here']").text
    except NoSuchElementException:
        print(f'No category for article: {data["title"]}')
        data['category'] = None

    content_body_elem = article_full_body.find_element(By.XPATH, ".//section[@class='article-body']")
    p_elements = content_body_elem.find_elements(By.XPATH, "./p")
    data['content'] = '\n\n'.join([p.text for p in p_elements])
    data['url'] = driver.current_url

    # try to get the article interest (interested/not interested)
    try:
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
    except NoSuchElementException:
        print(f'No article interest for article: {data["title"]}')
        pass



    # close the window the article
    driver.close()
    driver.switch_to.window(driver.window_handles[0])


# scrap the data from list of articles and save the data to a json file
def scrap_articles_list(
        skip_existing=True,  # skip articles that already exist in the json file
        pages='all',  # number of pages to scrap, 'all' for all pages
        page_start=1  # the page to start scraping from
):
    if pages == 'all':
        pages = math.inf

    page_count = 0
    while True:
        if page_count >= pages:
            break
        ####### make sure that in the desired page ########
        # get the url of current page
        current_url = driver.current_url
        # parse 'page' query param from url(if exists)
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)
        if 'page' not in query_params:
            # if there is no 'page' query param, add it to the url
            driver.get(current_url + '?page=1')
            continue

        pagination_elem = driver.find_element(By.XPATH, "//section[@class='pagination-lobby']")
        current_page_btn = pagination_elem.find_element(By.XPATH, ".//a[@class='currentPage']")
        current_page = int(current_page_btn.text)

        page_from_url = int(query_params['page'][0])
        # check if the current page is the wanted one, if not, move to the wanted page
        if current_page != page_from_url:
            # get the url of the wanted page
            wanted_url = current_url.replace(f'page={current_page}', f'page={page_start}')
            driver.get(wanted_url)
            continue

        try:
            next_page_elem = current_page_btn.find_element(By.XPATH, "./preceding-sibling::a[1]")
            next_page = int(next_page_elem.text)
        except NoSuchElementException:
            print('Last page reached')
            break

        ####### scrap article data ########
        print(f"Scraping page {current_page} of {pages}")

        if current_page == 1:
            articles = driver.find_elements(By.XPATH, "//html/body/div[6]/main/section[1]/section[6]/ul/li")
        else:
            articles = driver.find_elements(By.XPATH, "//html/body/div[6]/main/section[1]/section[1]/ul/li | //html/body/div[6]/main/section[1]/section[3]/ul/li")

        for article in articles:
            # create a new article data(with default empty values)
            article_data = {
                "title": "",
                "long_title": "",
                "short_description": "",
                "category": "",
                "main_reporter": "",
                "all_reporters": "",
                "num_of_reporters": "",
                "publish_timedate": "",
                "last_update_timedate": "",
                "content": "",
                "views": "",
                "article_interest": {
                    "interested": None,
                    "not_interested": None,
                },
                "url": "",
            }

            try:
                article_link = article.find_element(By.XPATH, ".//strong/a")
            except Exception as e:
                print(f"Error in article {article_name}: {e}")
                article_data = 'error!' + str(e)
                continue

            article_name = article_link.text
            article_data['title'] = article_name

            # skip if already exists
            if skip_existing and article_data['title'] in all_articles:
                print(f"skipping article: {article_data['title']}")
                global skip_count
                skip_count += 1
                continue

            # scrap the articles data and add to the list
            article_data['main_reporter'] = article.find_element(By.XPATH, ".//small/span").text
            try:
                scrap_article_page(article_link, article_data)
            except Exception as e:
                print(f"Error in article {article_name}: {e}")
                article_data = 'error!' + str(e)
                continue

            # add to all articles
            all_articles[article_data['title']] = article_data

            save_articles()

        # go to next page
        try:
            next_page_elem.click()
            page_count += 1
        except StaleElementReferenceException:
            continue


def run_scraping(skip_existing=True):
    print('started scraping...')
    for category in category_url_map:
        print(f"scraping category: {category}")
        driver.get(category_url_map[category])

        # iterate over all pages and scrap the articles
        scrap_articles_list(skip_existing=skip_existing, pages=80)


def save_articles():
    scraping_metedata = {
        # save the last scraping update(according to local time)
        "last_scraping_update": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "total_articles": len(all_articles),
    }
    j = {'scraping_metedata': scraping_metedata, 'data': all_articles}
    with open('articles.json', 'w', encoding='utf-8') as f:
        f.write(
            json.dumps(j, ensure_ascii=False, indent=2), )


def load_articles():
    # if articles.json doe not exists, create it(with utf-8 encoding to support hebrew
    if not os.path.exists('articles.json'):
        with open('articles.json', 'w', encoding='utf-8') as f:
            f.write('{"scraping_metedata": {}, "data": {}}')

    with open('articles.json', encoding='utf-8') as f:
        all_articles = json.load(f)
    return all_articles['data']


if __name__ == '__main__':
    # load all articles
    all_articles = load_articles()

    # run the scraping (will update the articles.json file as the scraping goes)
    run_scraping()

    print(f"skipped articles(in this run): {skip_count}")
    print(f"new scraped articles(in this run): {scrap_count}")
    print(f"total articles: {len(all_articles)}")
    print('finished scraping...')

# Close the web driver
driver.quit()
