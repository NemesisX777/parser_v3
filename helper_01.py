import csv
import logging
import time

import requests
from bs4 import BeautifulSoup

from settings import categories_file
from parser_v3 import get_page, cook_soup, write_csv_file, read_csv_file

log = logging.getLogger(__name__)
log_format = '%(asctime)s; %(levelname)s: %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)


# Функция парсит категории товаров, записывает их структуру в файл и возвращает список УРЛов начальных страниц категорий
def get_categories(url):
    content_of_response = get_page(url)
    soup = cook_soup(content_of_response)

    # находим все пункты меню топ-уровня
    menu_items = soup.find('ul', class_='megamenu').find_all('a', class_='level-top')

    with open(categories_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_headers = ['Cat_ID', 'Parent_Cat_ID', 'Category_Name', 'URL']  # заголовки полей файла
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()  # записываем строку заголовков

        # Объявляем начальные значения переменных для категорий
        category_id = 1
        parent_category_id = 0

        for item in menu_items:
            name = item.find('span').string.strip()
            link = item.get('href')
            writer.writerow({'Cat_ID': category_id,
                             'Parent_Cat_ID': parent_category_id,
                             'Category_Name': name,
                             'URL': link})
            category_id += 1


# Проверка на наличие дочерних категорий
def check_child_category(url):
    content_of_response = get_page(url)
    soup = cook_soup(content_of_response)
    return not bool(soup.find('div', class_='products'))  # div с этим классом отсутствует на страницах с подкатегориями


def get_cat_for_me(url):
    soup = cook_soup(get_page(url))
    cat_items = soup.find('div', class_='columns').find_all('div', class_='pagebuilder-column')

    cat_dict = {}
    for item in cat_items:
        try:
            link = item.a.get('href')
            name = item.div.p.string.strip()
            cat_dict[link] = name
        except AttributeError:
            continue

    return cat_dict


# Парсинг страниц с категориями товаров
def get_list_of_category() -> None:
    links = ['https://aquapolis.ru/oborudovanie-for-pool',
             'https://aquapolis.ru/zakladnye-dlja-bassejny',
             'https://aquapolis.ru/otdelochnye-materialy',
             'https://aquapolis.ru/truby-i-fitingi',
             'https://aquapolis.ru/aksessuary-dlja-bassejna',
             'https://aquapolis.ru/detskie-tovary',
             'https://aquapolis.ru/nakrytija-na-bassejny',
             'https://aquapolis.ru/oborudovanie-dlja-saun',
             'https://aquapolis.ru/zapchasti-i-rashodnye-materialy.html',
             'https://aquapolis.ru/fontany',
             ]
    final_dict = {}

    for link in links:
        current_dict = get_cat_for_me(link)
        final_dict = final_dict | current_dict

    print(final_dict)

    with open('output_files/category_tmp.csv', 'w', newline='', encoding='utf-8') as csvfile:
        csv_headers = ['URL', 'Category_Name']  # заголовки полей файла
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()  # записываем строку заголовков
        for k, v in final_dict.items():
            writer.writerow({'URL': k, 'Category_Name': v})


if __name__ == '__main__':
    start_time = time.time()

    # get_categories('https://aquapolis.ru/')
    # get_list_of_category()

    tmp_list = list(read_csv_file('output_files/list_of_category.csv')[0])
    write_csv_file(tmp_list, 'output_files/list_of_all_of_categories_pages.csv')

    log.info('Время работы: %s', time.time() - start_time)
