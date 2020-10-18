# imports of stdlib
import re
import time
import math

from multiprocessing import Pool, cpu_count

# imports of application related

# Other libs
from bs4 import BeautifulSoup
import pandas as waifu
import requests
import tqdm

class BookScraper:
    def __init__(self, config):
        self.config = config

        self.dataframe = {
            "title" : [],
            "category" : [],
            "universal_product_code" : [],
            "price_including_tax" : [],
            "price_excluding_tax" : [],
            "number_available" : [],
            "review_rating" : [],
            "product_description" : [],
            "image_url" : [],
            "product_page_url" : [],
        }

    def get_soup(self, url):
        """
        Returns
        -------
            BeautifulSoup Object

        """
        result = requests.get(url)
        soup = BeautifulSoup(result.text, 'html.parser')
        return(soup)

    def get_all_books(self, url):
        """
        Returns
        -------
            List
                contains all the books URLs inside a single page
        """

        soup = self.get_soup(url)
        base_url = "/".join(url.split("/")[:-1]) + "/" 
        all_books_on_page = [base_url + x.div.a.get('href') for x in soup.findAll("article", class_ = "product_pod")]
        
        return all_books_on_page
    
    def get_all_valid_pages(self, start_url):
        """
        Returns
        -------
            List
                contains all the valid URLs
        """
        valid_urls = []
        new_page = start_url

        more_soup = self.get_soup(start_url)

        get_total_pages = more_soup.find("ul", class_= "pager")   
        total_pages = get_total_pages.li.string.split()[-1]
        page_num = start_url.split("-")[1].split(".")[0]

        while int(page_num) < int(total_pages):
            valid_urls.append(new_page)
            base_url = valid_urls[-1].split("-")[0]
            page_num = valid_urls[-1].split("-")[1].split(".")[0]
            new_page = base_url + "-" + str(int(page_num) + 1) + ".html"

        return valid_urls

        # valid_pages = []
        # valid_pages.append(start_url)

        # more_soup = self.get_soup(start_url)

        # get_total_pages = more_soup.find("ul", class_= "pager")
        # total_pages = get_total_pages.li.string.split()[-1]
        # page_num = 0

        # next_page = start_url

        # print(page_num)

        # while int(page_num) < int(total_pages):
        #     base_url = valid_pages[-1].split("-")[0]
        #     page_num = valid_pages[-1].split("-")[1].split(".")[0]

        #     next_page = base_url + "-" + str(int(page_num) + 1) + ".html"
        #     valid_pages.append(next_page)

        # return valid_pages

     
    def get_book_meta(self, book_url):
        """
        Returns
        -------
            Object
                contains all the book's metadata
        """
        # .string causes pool to thorw a recursion error

        base_url = '/'.join(book_url.split("/")[:3])

        more_soup = self.get_soup(book_url)
        soup_product = more_soup.find("article", class_ = "product_page")

        book_category = more_soup.find("ul", class_ = "breadcrumb").findChildren('li')[2].a.get_text()
        book_rating = soup_product.find('p', class_ = "star-rating").get("class")[1]
        book_title = soup_product.h1.get_text()
        book_desc = soup_product.findChildren("p")[3].get_text() # because the desc is the 3rd elem on the product page
        book_img = f'{base_url}/' + '/'.join(soup_product.find('img').get("src").split("/")[2:])

        soup_table = soup_product.findChildren("table", class_ = "table table-striped")[0]
        soup_rows = soup_table.findChildren(['th', 'tr'])                              
        
        upc = soup_rows[0].td.get_text()
        price_with_tax = soup_rows[4].td.get_text()[2:]
        price_without_tax = soup_rows[6].td.get_text()[2:]
        item_in_stock = int(re.findall(r'\d+', soup_rows[10].td.get_text())[0])
        # prod_type = soup_rows[2].td.get_text()
        # tax = soup_rows[8].td.get_text()[2:]
        # num_of_reviews = soup_rows[12].td.get_text()

        book = {
            "product_page_url" : book_url,
            "universal_product_code" : upc,
            "title" : book_title,
            "price_including_tax" : price_with_tax,
            "price_excluding_tax" : price_without_tax,
            "number_available" : item_in_stock,
            "product_description" : book_desc,
            "category" : book_category,
            "review_rating" : book_rating,
            "image_url" : book_img,
        }
        
        return book

    
    def prepare_dataframe(self):
        """
        Returns
        -------
            Panda Dataframe
                containing all the book scraped from the website
        
        """
        startURL = self.config.web_url
        df = waifu.DataFrame(self.dataframe, columns=[n for n in self.dataframe])

        print("Getting the available pages to scrape...")
        all_pages = self.get_all_valid_pages(startURL)
        all_books_URLs = []

        # kurumi_past = time.perf_counter()

        chunky_size = 4

        print("Getting all the books from each page...")
        with Pool(processes=8) as pool, tqdm.tqdm(total=len(all_pages)) as pbar:
            for data in pool.map(self.get_all_books, all_pages , chunksize=chunky_size):
                all_books_URLs.extend(data)
                pbar.update()

            pool.terminate()
            pool.join()
        pbar.close()

        print("Getting each book's data")
        with Pool(processes=10) as pool, tqdm.tqdm(total=len(all_books_URLs)) as pbar:
            for book in pool.map(self.get_book_meta, all_books_URLs, chunksize=chunky_size):
                df = df.append(book, ignore_index=True)
                pbar.update()

            pool.terminate()
            pool.join()
        pbar.close()

        # print(df.head())
        return df
        # pbar = tqdm.tqdm(total=len(all_books_URLs))
        # for URL in all_books_URLs:
        #     all_books_data.extend(self.get_book_meta(URL))
        #     pbar.update()

        # with Pool(processes=4) as pool, tqdm.tqdm(total=len(all_books_URLs)) as pbar:
        #     for data in pool.map(self.get_book_meta, all_books_URLs, chunksize=chunky_size):
        #         print(data)

        #         all_books_data.extend(data)
        #         pbar.update()

        #     pool.terminate()
        #     pool.join()


            
                
        
            

        # kurumi_now = time.perf_counter()
        # print(f"Finished at {kurumi_now - kurumi_past:0.4f}s")


            # kurumi_now = time.perf_counter()
            # print(f"Took {kurumi_now - kurumi_past:0.4f}s")

        # for page in all_pages:
        #     list_of_books = self.get_all_books(page)
        #     print(len(list_of_books))

            # return
            # for book_url in list_of_books:
            #     book = self.get_book_meta(book_url)
                
            #     print(book["title"])

            #     for key, item in book.items():
            #         self.dataframe[key].append(book[key])

                    # test = p.map(self.get_book_meta, all_links)
            # for book_url in chunk:
            #     book = self.get_book_meta.(book_url)
            
            # df = df.append(book, ignore_index=True)


        

        
