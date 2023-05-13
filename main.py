import requests
from bs4 import BeautifulSoup
import json
from pathvalidate import sanitize_filename


url = "https://eldorado.ua/uk/"
url_short = "https://eldorado.ua"


class ReviewParser:

    def __init__(self, eldorado_url, eldorado_url_short):
        self.eldorado_url = eldorado_url
        self.url_short = eldorado_url_short

    def save_reviews(self, data, product_name, product_url):
        print(product_name)
        reviews = []

        for element in data:
            review = {
                "title": 'kek',
                "author_name": element['user_name'],
                "url": product_url,
                "grade": element["rating"]["rating_value"],
                "date": element['created_at'],
                "text": element['comment']
            }
            reviews.append(review)

        data = {
            "reviews": reviews
        }

        sanitized = sanitize_filename(product_name)
        with open(f"reviews/{sanitized}.json", "w", encoding='utf8') as fp:
            json.dump(data, fp, indent=4, ensure_ascii=False)

    def get_reviews(self, product_url):
        response = requests.get(url=product_url)
        html_page = response.text
        soup = BeautifulSoup(html_page, "html.parser")

        product_name_obj = soup.find(name="div", class_="product-name")
        product_name = product_name_obj.getText()

        code_obj = soup.find(name="span", itemprop="sku")
        code = code_obj.getText()

        url_id_from_code_template = "https://api.eldorado.ua/v1/goods_catalog?extIds={page_found_code}"
        url_json = url_id_from_code_template.format(page_found_code=code)
        response = requests.get(url=url_json)

        good_id = json.loads(response.text)["data"][0]["id"]

        url_comments_template = (
            "https://api.eldorado.ua/v1/comments?goods_id={good_id}&type=%27r%27&returnCommentsList&lang=ua"
        )

        url_comments = url_comments_template.format(good_id=good_id)
        response = requests.get(url=url_comments)
        data = json.loads(response.text)["data"]

        self.save_reviews(data, product_name, product_url)

    def process_final_category(self, url_subcategory):
        response = requests.get(url=url_subcategory)
        html_page = response.text
        soup = BeautifulSoup(html_page, "html.parser")

        pages_button = soup.find_all(name="a", class_="ui-library-pageLink-d009")
        if pages_button:
            max_pages = int(pages_button[-1].getText())
            for num in range(1, max_pages):
                url_page = url_subcategory + f"/page={num}/"
                response_next = requests.get(url=url_page)
                html_page_text = response_next.text
                soup = BeautifulSoup(html_page_text, 'html.parser')
                products = soup.find_all(
                    name="a",
                    class_="GoodsDescriptionstyled__StyledLinkWrapper-sc-1c1eyhs-0 gbyxYE"
                )
                for product in products:
                    self.get_reviews(url_short + product['href'])

        else:
            html_page_text = response.text
            soup = BeautifulSoup(html_page_text, 'html.parser')
            products = soup.find_all(name="a", class_="GoodsDescriptionstyled__StyledLinkWrapper-sc-1c1eyhs-0 gbyxYE")

            for product in products:
                self.get_reviews(url_short + product['href'])

    def get_subcategory(self, url_category):
        response = requests.get(url=url_category)
        html_page = response.text
        soup = BeautifulSoup(html_page, "html.parser")
        subcategories = soup.find_all(name="div", class_="node-item")

        for subcategory in subcategories:


            a_element = subcategory.find("a", class_=False)
            url_subcategory = url_short + a_element['href']

            if 'node' in a_element['href']:
                self.get_subcategory(url_subcategory)
            else:
                self.process_final_category(url_subcategory)

    def get_categories(self, url):
        response = requests.get(url=url)
        html_page = response.text
        soup = BeautifulSoup(html_page, "html.parser")
        categories = soup.find_all(name="a", class_="MenuItemstyled__StyledMegaMenuLink-sc-gkys1m-0")

        for category in categories:
            url_category = url_short + category['href']
            self.get_subcategory(url_category)



ReviewParser(url, url_short).get_categories(url)
