# import csv
import json
import logging
import re
import time

import pandas
from bs4 import BeautifulSoup
# import lxml.html
import requests
from settings import HEADERS

log = logging.getLogger(__name__)
log_format = '%(asctime)s; %(levelname)s: %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)


# Метод для отправки http-запросов (возвращает html-код и код ответа)
def get_page(url: str) -> str:
    try:
        log.info(f'Try to fetch page: {url}')
        response = requests.get(url, headers=HEADERS)
    except requests.exceptions.ConnectionError as con_error:
        log.warning(f'URL: {url} not downloaded || Ошибка соединения: {con_error}')
    else:
        log.info(f'URL: {url} downloaded || Код ответа: {response.status_code}')
        return response.text


# Метод для приготовления супа
def cook_soup(html_code: str) -> object:
    try:
        soup = BeautifulSoup(html_code, 'lxml')  # готовим супчик
    except TypeError as excpt:
        log.warning('Невозможно распарсить код')
        log.warning(f'Ошибка: {excpt}')
    else:
        return soup


# Метод для получения всех страниц категорий с товарами (учитывая пагинацию)
def get_list_of_all_of_categories_pages(list_of_categories: list[str]) -> list[str]:
    list_of_all_of_categories_pages = []

    for category in list_of_categories:
        list_of_all_of_categories_pages.append(category)
        if check_pagination(category):
            additional_links = get_categories_pages(category)
            list_of_all_of_categories_pages += additional_links

    return list_of_all_of_categories_pages


# проверка наличия пагинации
def check_pagination(url: str) -> bool:
    soup = cook_soup(get_page(url))
    pagination_tag = soup.find('a', class_='action next')
    return bool(pagination_tag)


# получение страниц категорий с пагинацией
def get_categories_pages(url: str) -> list[str]:
    list_of_additional_links = []
    while True:
        soup = cook_soup(get_page(url))
        try:
            next_page_link = soup.find('a', class_='action next').get('href')
        except AttributeError:
            next_page_link = None
        if not next_page_link:
            break
        list_of_additional_links.append(next_page_link)
        url = next_page_link
    return list_of_additional_links


def read_csv_file(filename, header=None):
    dataframe = pandas.read_csv(filename, header=header)
    return dataframe


def write_csv_file(data, filename, header=None, index=None, mode='w'):
    dataframe = pandas.DataFrame(data)
    dataframe.to_csv(filename, header=header, index=index, mode=mode)


# Метод для поиска страниц товаров
def find_product_page_links(list_of_urls: list[str]) -> list[str]:
    final_list_of_product_links = []

    for url in list_of_urls:
        soup = cook_soup(get_page(url))
        product_items = soup.find('div', class_='products wrapper grid products-grid')\
            .find_all('div', class_='product-item-info')

        for item in product_items:
            link = item.a.get('href')
            final_list_of_product_links.append(link)

    return final_list_of_product_links


def parse_products(list_of_links, start_number, end_number):
    list_of_products = []
    for link in list_of_links[start_number:end_number]:
        soup = cook_soup(get_page(link))
        if soup.find('table', class_='table data grouped'):
            write_csv_file([link], 'output_files/multi_products.csv', mode='a')
            continue

        name = replace_many_whitespaces(soup.find('h1', class_='page-title').span.string.strip())
        price = int(soup.find('div', class_='product-info-price').find('span', class_='price-container').find('meta').get('content').strip())
        sku = int(soup.find('div', class_='product attribute sku').find('div', class_='value').string.strip())
        short_description = get_short_description(soup.find('div', class_='product attribute overview').div)
        list_of_image_links = get_image_links(soup.find('div', class_='product media').find_all('a', class_='mt-thumb-switcher'))
        specification = get_specification(soup.find('div', class_='data item content', id='additional').find('table').find_all('tr'))
        product_dict = {'link': link,
                        'name': name,
                        'price': price,
                        'sku': sku,
                        'short_description': short_description,
                        'specification': specification,
                        'list_of_image_links': list_of_image_links}
        list_of_products.append(product_dict)

    return list_of_products


def get_short_description(tag):
    return replace_many_whitespaces(tag.get_text())


def replace_many_whitespaces(string):
    string_without_nbsp = string.strip().replace('\xa0', ' ')
    search_pattern = r'((\n)+)(\s*)((\n)*)'
    clear_string = re.sub(search_pattern, '\n', string_without_nbsp)
    return clear_string


def get_image_links(tags_list):
    list_of_image_links = []
    for tag in tags_list:
        link = tag.get('href')
        list_of_image_links.append(link)
    return list_of_image_links


def get_specification(tags_list):
    list_of_spec = {}

    def get_spec_value(value_tag):
        value_list = []
        if value_tag.ul:
            for item in value_tag.ul.find_all('li'):
                try:
                    value_list.append(item.string.strip())
                except AttributeError:
                    continue
        else:
            value_list.append(value_tag.string.strip())
        return value_list

    for tag in tags_list:
        key = tag.th.string.strip()
        value = get_spec_value(tag.td)
        list_of_spec[key] = value

    return list_of_spec


def check_multi_product(soup):
    is_multiproduct = soup.find('table', class_='table data grouped')
    return is_multiproduct


if __name__ == '__main__':
    start_time = time.time()

    # Формирование списка категорий
    # list_of_categories = list(read_csv_file('output_files/list_of_category.csv')[0])
    # list_of_all_of_categories_pages = get_list_of_all_of_categories_pages(list_of_categories)
    # write_csv_file(list_of_all_of_categories_pages, 'output_files/list_of_all_of_categories_pages.csv')

    # Формирование списка товаров
    # list_of_category_pages = list(read_csv_file('output_files/list_of_all_of_categories_pages.csv')[0])
    # list_of_product_pages = find_product_page_links(list_of_category_pages)
    # write_csv_file(list_of_product_pages, 'output_files/list_of_product_pages.csv')

    # Парсинг товаров
    list_of_product_links = list(read_csv_file('output_files/list_of_product_pages.csv')[0])
    list_of_products_dict = parse_products(list_of_product_links, 200, 300)
    write_csv_file(list_of_products_dict, 'output_files/products.csv', header=True, mode='a')
    print(json.dumps(list_of_products_dict, ensure_ascii=False, indent=4))

    log.info('Время работы: %s', time.time() - start_time)
