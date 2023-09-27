import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import shutil

load_dotenv()
ZD_USER = os.getenv("ZD_USER")
ZD_PASSWORD = os.getenv("ZD_PASSWORD")
assert ZD_USER and ZD_PASSWORD, "Make sure your environment variables are populated in .env"

def create_metadata_string(metadata: dict):
    metadata_string = ''
    for key, value in metadata.items():
        metadata_string += f'<meta name="{key}" content="{value}"/>'
    return metadata_string

def clean_and_save_html(article_url, output_folder):
    response = requests.get(article_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    article_tag = soup.find('article')
    tokenized_url = article_url.split('/')
    article_title = ''
    for token in tokenized_url[::-1]:
        if token:
            article_title = token
            break
    if not article_tag:
        print(f"No <article> tag found in {article_url}")
        return
    article_locale = soup.find('html').get('lang', 'unknown')
    metadata = {
        'source': article_url,
        'source-type': 'academy',
        'locale': article_locale,
        'zd-article-id': 'N/A',
        'title': article_title.replace('-', ' '),
        'classification': 'public'
    }
    cleaned_soup = BeautifulSoup('<html><head></head><body></body></html>', 'html.parser')
    cleaned_soup.head.append(BeautifulSoup(create_metadata_string(metadata), 'html.parser'))
    cleaned_soup.body.append(article_tag)
    output_filename = article_title.replace('-', '_')
    filename = os.path.join(output_folder, f'{output_filename}_{article_locale}.html')
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(str(cleaned_soup.prettify()))

def scrape_zendesk(output_folder: str, article_ids_to_skip: list = None, zendesk_base_url: str = 'https://ledger.zendesk.com', locales: list = None, scrape_these_article_ids: list = None):
    if not locales:
        locales = ['en-us']  
    if not article_ids_to_skip:
        article_ids_to_skip = []
    endpoints = [(locale, f'{zendesk_base_url}/api/v2/help_center/{locale.lower()}/articles.json') for locale in locales]
    for locale, endpoint in endpoints:
        while endpoint:
            response = requests.get(endpoint, auth=(ZD_USER, ZD_PASSWORD))
            assert response.status_code == 200, f'Failed to retrieve articles with error {response.status_code}'
            data = response.json()
            for article in data['articles']:
                if scrape_these_article_ids and article['id'] not in scrape_these_article_ids:
                    continue
                if not article['body'] or article['draft'] or article['id'] in article_ids_to_skip:
                    continue
                title = '<h1>' + article['title'] + '</h1>'
                url = article['html_url']
                metadata = {
                    'source': url,
                    'source-type': 'zendesk',
                    'locale': locale,
                    'zd-article-id': article['id'],
                    'title': article['title'],
                    'classification': 'public'
                }
                filename = f"zd_{article['id']}_{locale}.html"
                with open(os.path.join(output_folder, filename), mode='w', encoding='utf-8') as f:
                    f.write(f'<!DOCTYPE html><html><head>{create_metadata_string(metadata)}</head><body>{title}\n{article["body"]}</body></html>')
                print(f"{article['id']} copied!")
            endpoint = data['next_page']

def run_scraper(output_directory_path: str = None):
    if not output_directory_path:
        output_directory_path = os.path.join(os.path.dirname(__file__), 'input_files')
    scraper_output_folder = os.path.join(output_directory_path, 'articles')

    if os.path.exists(scraper_output_folder):
        shutil.rmtree(scraper_output_folder)
    os.makedirs(scraper_output_folder, exist_ok=True)
    
    scrape_zendesk(scraper_output_folder, locales=['en-us'])  

if __name__ == "__main__":
    run_scraper()
