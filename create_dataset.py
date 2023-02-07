# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
#
# # Initialize the webdriver
# driver = webdriver.Chrome()
#
# # Navigate to the Fox News website
# driver.get("https://www.foxnews.com/")
#
# # Wait until the articles are loaded
# wait = WebDriverWait(driver, 10)
# articles = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//section[@class='collection collection-article-list")))
#
# # //h1[@class='headline']
# # //section[@class='collection collection-article-list']
# # //section[@class='collection collection-article-list has-load-more']
#
#
# # Extract the article name and category for each article
# for article in articles:
#     title_element = article.find_element_by_xpath(".//h2[@class='title']/a")
#     title = title_element.text
#     category_element = article.find_element_by_xpath(".//span[@class='primary-category']/a")
#     category = category_element.text
#     print("Title:", title)
#     print("Category:", category)
#
# # Close the webdriver
# driver.quit()

from selenium import webdriver
from selenium.common import StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize the webdriver
options = webdriver.ChromeOptions()
options.add_argument("--disable-extensions")
driver = webdriver.Chrome(options=options)

# Navigate to the Fox News website and category
driver.get("https://www.foxnews.com/politics")

# Wait until the article section is loaded
wait = WebDriverWait(driver, 200)

data = [
    # {
    #   title
    # }
]


# def extract_articles_from_article_section(section):
#     # Extract the article name and category for each article
#     articles = section.find_elements(By.XPATH, ".//article")
#     for article in articles:
#         title_element = article.find_element(By.XPATH, ".//h4[@class='title']/a")
#         title = title_element.text
#         category_element = article.find_element(By.XPATH, ".//span[@class='eyebrow']/a")
#         category_name = category_element.text
#         # skip video articles
#         if category_name == 'VIDEO':
#             continue
#         data.append({"title": title})
#
#
# # first sections block
# article_section = wait.until(
#     EC.presence_of_element_located((By.XPATH, "//section[@class='collection collection-article-list']")))
#
# extract_articles_from_article_section(article_section)
#
# actions = ActionChains(driver)


def extract_articles_from_article_section_with_load_more(section, number_of_articles=100):
    # Extract the article name and category for each article
    articles = section.find_elements(By.XPATH, ".//article")

    load_more_button = section.find_elements(By.XPATH, ".//div[@class='button load-more js-load-more']/a")[0]

    i = 0
    articles_read = 0
    # for i in range(number_of_articles):
    while articles_read < number_of_articles:
        while i >= len(articles) - 1:
            driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
            load_more_button.click()
            articles = section.find_elements(By.XPATH, ".//article")

        title_element = articles[i].find_element(By.XPATH, ".//h4[@class='title']/a")
        title = title_element.text
        category_element = articles[i].find_element(By.XPATH, ".//span[@class='eyebrow']/a")
        category_name = category_element.text
        i += 1
        # skip video articles
        if category_name == 'VIDEO':
            continue
        articles_read += 1
        data.append({"title": title})



# second section block (with load more button)
article_section = wait.until(
    EC.presence_of_element_located((By.XPATH, "//section[@class='collection collection-article-list has-load-more']")))

extract_articles_from_article_section_with_load_more(article_section)

print(data)
# Close the webdriver
driver.quit()
