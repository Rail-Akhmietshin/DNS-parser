import json
import os
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
import time
import requests

options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)


driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
)

main_url = "https://www.dns-shop.ru"

driver.get('https://www.dns-shop.ru/catalog/88f4ff1d39dee00e/osnovnye-komplektuyushhie-dlya-pk/')
      
# with open('index.html', 'w', encoding='utf-8') as file:
#     file.write(driver.page_source)

# with open("index.html", 'r', encoding='utf-8') as file:
#     categories = file.read()

soup = BeautifulSoup(driver.page_source, 'lxml')
cut_category_links = soup.find_all("a", class_="subcategory__item ui-link ui-link_blue")

full_category_links = [main_url + x["href"] for n, x in enumerate(cut_category_links) if not n in (3, 6, 7, 8, 9)]


''' Neccessary subcategories '''

full_category_links += [
    "https://www.dns-shop.ru/catalog/17a8943716404e77/monitory/",
    "https://www.dns-shop.ru/catalog/17a89a3916404e77/operativnaya-pamyat-dimm/",

    "https://www.dns-shop.ru/catalog/17a8914916404e77/zhestkie-diski-35/",

    "https://www.dns-shop.ru/catalog/8a9ddfba20724e77/ssd-nakopiteli/",
    "https://www.dns-shop.ru/catalog/dd58148920724e77/ssd-m2-nakopiteli/",

    "https://www.dns-shop.ru/catalog/17a9cc2d16404e77/kulery-dlya-processorov/",
    "https://www.dns-shop.ru/catalog/17a9cc9816404e77/sistemy-zhidkostnogo-oxlazhdeniya/",
]

for i, category_link in enumerate(full_category_links):
    
    
    driver.get(category_link)


    soup = BeautifulSoup(driver.page_source, 'lxml')

    try:
        count_pages = int(soup.find("a", class_="pagination-widget__page-link pagination-widget__page-link_last")["href"].split("=")[-1])
    except TypeError:
        count_pages = 1

    category = category_link.split("/")[-2]

    if not os.path.isdir(category):
        os.mkdir(category)
    if not os.path.isdir(f"{category}/jsons"):
        os.mkdir(f"{category}/jsons")
    if not os.path.isdir(f"{category}/images"):
        os.mkdir(f"{category}/images")


    for i in range(1, count_pages + 1):
        driver.get(category_link + f"?p={i}")

        # with open(f'{category}/{i}_page_{category}.html', 'w', encoding='utf-8') as file:
        #     file.write(driver.page_source)

        # with open(f'{category}/{i}_page_{category}.html', 'r', encoding='utf-8') as file:
        #     products = file.read()

        soup = BeautifulSoup(driver.page_source, 'lxml')
        cut_product_links = soup.find_all("a", class_="catalog-product__name ui-link ui-link_black")
        full_product_links = [main_url + x["href"] for x in cut_product_links]

        for product_link in full_product_links:

            driver.get(product_link + "characteristics/")

            soup = BeautifulSoup(driver.page_source, 'lxml')

            chars = ["|", "/", ":", "*", "?", ">", "<", "\"", "\'"]
            
            try:
                title = soup.find("a", class_="product-card-tabs__product-title ui-link ui-link_black").text
            except:
                try:
                    time.sleep(10)
                    title = soup.find("a", class_="product-card-tabs__product-title ui-link ui-link_black").text
                except:
                    print("Не удалось найти заголовок")
                    continue
            
            for x in chars:
                if x in title:
                    title = title.replace(x, " ")

            if not os.path.exists(f"{category}/images/{title}.jpg.webp"):

                try:
                    image = soup.find("img", class_="product-images-slider__main-img")["src"] + ".webp"
                except:
                    try:
                        time.sleep(10)
                        image = soup.find("img", class_="product-images-slider__main-img")["src"] + ".webp"
                    except (TypeError, KeyError):
                        print("Failed to upload photo")
                        continue

                try:
                    response = requests.get(image)
                except:
                    try:
                        time.sleep(10)
                        response = requests.get(image)
                    except TypeError:
                        continue
                with open(f"{category}/images/{title}.jpg.webp", 'wb') as f:
                    f.write(response.content)
                    print(f"Image {title} uploaded successfully!")

            if not os.path.exists(f"{category}/jsons/{title}.json"):
                try:
                    parameter = soup.find("div", class_="product-characteristics__group").next_sibling
                except:
                    try:
                        time.sleep(10)
                        parameter = soup.find("div", class_="product-characteristics__group").next_sibling
                    except:
                        print("Failed to upload characteristics")
                        os.remove(f"{category}/images/{title}.jpg.webp")
                        continue


                data = {}

                def get_parameters(parameter):
                    if parameter is None:
                        data["Описание"] = soup.find("div", class_="product-card-description-text").text
                        
                        price = [x.text for x in soup.find_all("div", class_="product-buy__price")]
                        
                        random_price = random.randint(2999, 20999)

                        data["Цена"] = price if price else f"{random_price} ₽"

                        with open(f"{category}/jsons/{title}.json", "w", encoding="utf-8") as file:
                            json.dump(data, file, indent=3, ensure_ascii=False)

                        print(f"JSON {title} of the product has been successfully uploaded!")
                        return
                    
                    parameter_main_title = parameter.find("div", class_="product-characteristics__group-title").text
                    parameter_title = parameter.find_all("div", class_="product-characteristics__spec-title")
                    parameter_description = parameter.find_all("div", class_="product-characteristics__spec-value")

                    intermediate_data = {}
                    for key, value in dict(zip(parameter_title, parameter_description)).items():
                        intermediate_data[key.text] = value.text
                    
                    data[parameter_main_title] = intermediate_data

                    return get_parameters(parameter.next_sibling)
                
                try:
                    get_parameters(parameter)
                except:
                    try:
                        time.sleep(10)
                        get_parameters(parameter)
                    except:
                        os.remove(f"{category}/images/{title}.jpg.webp")
                        print(f"An unexpected error has occurred, so there will be no {title} product")
                        continue
            time.sleep(5)