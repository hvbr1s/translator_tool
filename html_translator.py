import asyncio
import os
import openai
from bs4 import BeautifulSoup
from doctran import Doctran
from dotenv import load_dotenv
from tqdm import tqdm
import re

load_dotenv()

env_vars = ['OPENAI_API_KEY', ]
os.environ.update({key: os.getenv(key) for key in env_vars})
openai.api_key = os.getenv('OPENAI_API_KEY')

doctran = Doctran(openai_api_key=openai.api_key)


def translate_html_content(html_content):
    soup = BeautifulSoup(html_content, features="html.parser")

    async def translate_text(text):
        document = doctran.parse(content=text)
        translated = await document.translate(language="french").execute()
        return translated.transformed_content

    for text_element in tqdm(soup.body.find_all(string=lambda text: text.strip()), desc="Translating", ncols=100):
        new_text = asyncio.run(translate_text(text_element))
        text_element.replace_with(new_text)

    html_doc = str(soup.body)
    
    # Remove phrases
    html_doc = re.sub(re.compile("Bonjour, comment ça va?", re.IGNORECASE), "", html_doc)
    html_doc = re.sub(re.compile("Bonjour, comment puis-je vous aider aujourd'hui?", re.IGNORECASE), "", html_doc)
    
    # Replace "Mon Livre" with "Ledger"
    html_doc = re.sub(re.compile("Mon Livre", re.IGNORECASE), "Ledger", html_doc)

    return html_doc


def translate_html_files(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in tqdm(os.listdir(input_dir), desc="Processing files", ncols=100):
        if filename.endswith('.html'):
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, filename)

            with open(input_file, "r", encoding="utf-8") as f:
                html_content = f.read()

            translated_html_content = translate_html_content(html_content)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(translated_html_content)


translate_html_files("/home/dan/doctran_text/files", "/home/dan/doctran_text/translated")
