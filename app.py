import requests
from bs4 import BeautifulSoup
import random
import time
import openai
import os
from flask import Flask, request
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

openai.api_key = os.getenv('OPENAI_API_KEY')    
get_url = os.getenv('SCRAPE_URL')
post_url = os.getenv('POST_URL')
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

def scrape_specific(url, tag, tag_class):    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        target = soup.find(tag, class_=tag_class)
        
        if target:
            return target.get_text()
        else:
            print(f"Failed to find the <div> element with class '{tag_class}' on the page.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {url}. Error: {e}")
        return None        

def random_delay():
    delay = random.uniform(1, 3)
    time.sleep(delay)

def paraphrase_text(text_to_paraphrase):
    prompt = f"Paraphrase the following text: \"{text_to_paraphrase}\""
    
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",  # Choose the GPT-3 engine
            prompt=prompt,
            max_tokens=500,
            temperature=1.0, 
            stop=['\n', '\n\n']
        )
        
        if 'choices' in response and len(response['choices']) > 0:
            paraphrased_text = response['choices'][0]['text'].strip()
            return paraphrased_text
        else:
            print("Paraphrasing failed. No response received from OpenAI.")
            return None

    except Exception as e:
        print(f"Paraphrasing failed. Error: {e}")
        return None

def create_wordpress_post(post_url, username, password, title, number, content, status="publish"):
    post_data = {
        "title": title,
        "content": content,
        "status": status
    }

    response = requests.post(post_url, auth=(username, password), json=post_data)

    if response.status_code == 201:
        print("Post created successfully!")
        return True
    else:
        print("Failed to create post. Status code:", response.status_code)
        print("Error:", response.json())
        return False        

def handle_request(get_url):
    div_class_to_scrape = 'zoogle-content'
    tag1 = 'div'

    span_class_to_scrape = 'subtitle'
    tag2 = 'span'

    newsletter_number = 'font_large'

    scraped_title = scrape_specific(get_url, tag2, span_class_to_scrape)
    scraped_newsletter_number = scrape_specific(get_url, tag2, newsletter_number)
    scraped_text = scrape_specific(get_url, tag1, div_class_to_scrape)
    paraphrased_text = paraphrase_text(scraped_text)

    create_wordpress_post(post_url, username, password, scraped_title, scraped_newsletter_number, paraphrased_text)
    
    return 'Post created successfully!'        

@app.route('/', methods=['GET'])
@cross_origin() 
def button_scraping():
    button_tag = 'a'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    try:
        response = requests.get(get_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        div_tags = soup.find_all('div', class_='zoogle-feature block layout_full')

        hrefs = []

        for div_tag in div_tags:
            figure_tags = div_tag.find_all('figure', class_='image custom left')
            div_hrefs = [a.get('href') for figure_tag in figure_tags for a in figure_tag.find_all('a')]
            div_hrefs = [href for href in div_hrefs if href is not None]
            hrefs.extend(div_hrefs)
        
        for href in hrefs:
            handle_request('https://maxrichmusic.com' + href)
        
        return 'Posts created successfully!'

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {url}. Error: {e}")
        return None       

if __name__ == '__main__':
    app.run()
