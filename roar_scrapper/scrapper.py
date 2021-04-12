from flask import Flask
from flask import render_template, request
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import pymongo
import os

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # save json file to mongodb cloud
        user = os.environ['MONGO_USER']
        password = os.environ['MONGO_PASSWORD']

        url = f'mongodb+srv://{user}:{password}@cluster0.hvo9b.mongodb.net/myFirstDatabase?retryWrites=true&w=majority'
        client = pymongo.MongoClient(url)

        # database
        db = client["test_db"]
        Collection = db["data_roarmedia"]

        # Collect data using selenium and bs4
        options = Options()
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(options=options)

        site_url = 'https://roar.media/english/life/travel'

        driver.get(site_url)
        show_more_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "showMore"))
        )
        show_more_button.click()

        page_html = driver.page_source
        soup = BeautifulSoup(page_html, 'html.parser')

        articles_list = soup.find_all(
            'div', class_='ArticlesGrid__Tile-ch6kkd-1 kGsTtk withGrid withSideMargin')

        articles_info = []
        for article in articles_list:
            article_info = {}
            article_details = article.find(
                'div', class_='ArticleCard__Details-sc-8n55be-1 kLkTUH')

            pre_data = article_details.find('div', class_='pre-data')
            category = pre_data.find('div', class_='category').text

            meta_data = article_details.find('div', class_='meta-data')
            title = article_details.find('div', class_='title').text
            meta_data = article_details.find('div', class_='meta-data')

            published = meta_data.contents[0].text

            try:
                view = meta_data.contents[2].text.split(' ')[0]
            except IndexError:
                view = 'Not Specified'

            # print(title, category, published, view, sep="\n")
            article_info['title'] = title
            article_info['category'] = category
            article_info['published_date'] = published
            article_info['total_views'] = view

            articles_info.append(article_info)

        driver.quit()

        with open('article_list_data.json', 'w', encoding='utf8') as f:
            f.write(json.dumps(articles_info, ensure_ascii=False, indent=4))

        # restore json file data in mongodb cloud
        # Loading or Opening the json file
        with open('article_list_data.json') as file:
            file_data = json.load(file)

        if isinstance(file_data, list):
            Collection.insert_many(file_data)
        else:
            Collection.insert_one(file_data)
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
