import pathlib

class Config:
    # BooksToScrape Url
    web_url = "http://books.toscrape.com/catalogue/page-1.html"

    # Path to the datas
    csv_path = pathlib.Path(pathlib.Path(__file__).resolve().parent.parent, '.data/csv_files')
    images_path = pathlib.Path(pathlib.Path(__file__).resolve().parent.parent, '.data/images')
