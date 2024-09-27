import os
import json
import time
import requests
from bs4 import BeautifulSoup
from googletrans import Translator
from flask import Flask, render_template

app = Flask(__name__)

CACHE_FILE = 'reviews_cache.json'
CACHE_DURATION = 6 * 60 * 60  # 6 ชั่วโมง

def get_reviews_data(total_reviews_needed=50):

    if os.path.exists(CACHE_FILE):
        cache_mtime = os.path.getmtime(CACHE_FILE)
        if time.time() - cache_mtime < CACHE_DURATION:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                all_reviews = json.load(f)
                return all_reviews[:total_reviews_needed]

 
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    base_url = "https://www.google.com/async/reviewDialog?hl=th&async=feature_id:0x311d5fa69a587ff5:0xefa974585c012565,next_page_token:{},sort_by:qualityScore,start_index:{},associated_topic:,_fmt:pc"

    token = ""
    start_index = 0
    all_reviews = []
    translator = Translator()

    
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)

    while len(all_reviews) < total_reviews_needed:
        url = base_url.format(token, start_index)
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

      
        token_element = soup.select_one('.gws-localreviews__general-reviews-block')
        if token_element:
            token = token_element.get('data-next-page-token', '')

       
        reviews_elements = soup.select('.gws-localreviews__google-review')
        if not reviews_elements:
            break

        reviews_texts = []
        user_data_list = []

        for el in reviews_elements:
            review_text = el.select_one('.Jtu6Td').text.strip() if el.select_one('.Jtu6Td') else ''
            reviews_texts.append(review_text)

         
            time_element = el.select_one('.ODSEW-ShBeI-RgZmSc-date')  # ปรับคลาสตามโครงสร้าง HTML ปัจจุบัน
            if not time_element:
                time_element = el.select_one('.rsqaWe')
            if not time_element:
                time_element = el.select_one('.dehysf')
            if not time_element:
                time_element = el.select_one('.DZSIDd')
            review_time = time_element.text.strip() if time_element else ''

        
            print(f"Review time: {review_time}")

            user_data = {
                'name': el.select_one('.TSUbDb').text.strip() if el.select_one('.TSUbDb') else '',
                'link': el.select_one('.TSUbDb a')['href'] if el.select_one('.TSUbDb a') else '',
                'thumbnail': el.select_one('.lDY1rd')['src'] if el.select_one('.lDY1rd') else '',
                'numOfreviews': el.select_one('.Msppse').text.strip() if el.select_one('.Msppse') else '',
                'rating': el.select_one('.EBe2gf')['aria-label'] if el.select_one('.EBe2gf') else '',
                'time': review_time, 
            }
            user_data_list.append(user_data)

   
        try:
            translations = translator.translate(reviews_texts, dest='th')
            if not isinstance(translations, list):
                translations = [translations]
        except Exception:
            translations = reviews_texts 

        for idx, user_data in enumerate(user_data_list):
            user_data['review'] = translations[idx].text if hasattr(translations[idx], 'text') else translations[idx]
            all_reviews.append(user_data)
            if len(all_reviews) >= total_reviews_needed:
                break

        
        if not token:
            break

  
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_reviews, f, ensure_ascii=False)

    return all_reviews[:total_reviews_needed]


@app.route('/')
def index():
    reviews = get_reviews_data(total_reviews_needed=50)
    return render_template('index.html', reviews=reviews)

if __name__ == '__main__':
    app.run(debug=True)
