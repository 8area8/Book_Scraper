# imports of stdlib
from multiprocessing import Pool
import urllib.request as urllib
import pathlib
import string

# imports of application related
from application.src.book_scraper import BookScraper
from application.config import Config

# Other libs
from pandas import DataFrame
import unicodedata
import tqdm

class Application(object):
    def __init__(self):
        self.config = Config
        self.create_folder()
        self.books_scraper = BookScraper(Config)

    def create_folder(self):
        """
        The method creates the build folders
        """
        self.config.csv_path.mkdir(parents=True, exist_ok=True)
        self.config.images_path.mkdir(parents=True, exist_ok=True)

    def export_csv(self, df, filename):
        """
        Export dataframe to csv
        """
        df.to_csv(str(pathlib.PurePosixPath(self.config.csv_path, filename)) , sep=";")
    
    def export_book_images(self, obj):
        """
        Export a choosen url to an image
        """
        img_name = obj["name"]
        img_ext = obj["url"].split("/")[7:][0].split(".")[1]
        img_url = obj["url"]

        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        valid_img_name = ''.join(c for c in img_name if c in valid_chars) + "." + img_ext # get the extention of the file

        urllib.urlretrieve(img_url, str(pathlib.PurePosixPath(self.config.images_path, valid_img_name)))

    def run(self):
        """
        Run the bookscraper
        """
        dataframe = self.books_scraper.prepare_dataframe()
        all_categorys = list(dict.fromkeys([cat for cat in dataframe["category"]]))

        print("Exporting the images...")
        with Pool(processes=10) as pool, tqdm.tqdm(total=len(dataframe['image_url'].index)) as pbar:
            for data in pool.map(self.export_book_images, [{"name" : x, "url": y } for x, y in zip(dataframe["title"], dataframe["image_url"])] , chunksize=4):
                pbar.update()
            
            pool.terminate()
            pool.join()
        pbar.close()

        print("Getting all the categories, and exporting...")
        pbar = tqdm.tqdm(total=len(all_categorys))
        for categ in all_categorys:
            self.export_csv(dataframe.loc[dataframe['category'] == categ], f"{categ}_books.csv")
            pbar.update()
        pbar.close()

        self.export_csv(dataframe, "all_books.csv")
