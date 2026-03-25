import telebot
import requests
import hashlib
import base64
import json
import time
import random
import string
import threading
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- SOZLAMALAR ---
API_TOKEN = '8734482130:AAG6C1YqD05xhWxtguonTeqaYVZ6cXTTrm0'
bot = telebot.TeleBot(API_TOKEN)

HOST = "https://smmlox.com"
ALTCHA_KEY = "key_1jhlt1fhm00b2s721es"

# Xizmatlar (Reaksiya va Ko'rishlar)
SERVICES = {
    'reactions': {'i': '11043', 'c': '35892', 'q': '10'}, # Har safar 10 ta
    'views': {'i': '10871', 'c': '35892', 'q': '10'}
}

# Proksilarni yuklash
PROXIES = []
try:
    with open('prox100k.txt', 'r') as f:
        for line in f:
            p = line.strip()
            if p: PROXIES.append(f"http://{p}" if "://" not in p else p)
    print(f"Sizning bazangizdan {len(PROXIES)} ta proksi yuklandi.")
except FileNotFoundError:
    print("Xato: prox100k.txt topilmadi!")

def get_random_proxy():
    if not PROXIES: return None
    p = random.choice(PROXIES)
    return {'http': p, 'https': p}

# --- ASOSIY LOGIKA (Siz bergan kod asosida) ---

def solve_challenge(challenge):
    salt = challenge['salt']
    chall = challenge['challenge']
    maxnum = challenge['maxnumber']
    
    # Renderda CPUni qiynamaslik uchun soddalashtirilgan solve
    found = None
    for n in range(maxnum + 1):
        if hashlib.sha256(f"{salt}{n}".encode()).hexdigest() == chall:
            found = n
            break
    
    if found is None: return None
    payload = {
        "algorithm": challenge['algorithm'], "challenge": chall,
        "number": found, "salt": salt, "signature": challenge['signature'],
        "took": random.randint(100, 300)
    }
    return base64.b64encode(json.dumps(payload).encode()).decode()

def nakrutka_urish(link, type='reactions'):
    service = SERVICES[type]
    sess = requests.Session()
    px = get_random_proxy()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0 Safari/537.36'}

    try:
        # 1. Signup sahifasidan CSRF olish
        resp = sess.get(f"{HOST}/signup", headers=headers, proxies=px, timeout=10)
        token = BeautifulSoup(resp.text, 'html.parser').find('input', {'name': '_csrf'})['value']

        # 2. Altcha Challenge yechish
        challenge = sess.get('https://altcha.mypanel.link/v1/challenge', params={'apiKey': ALTCHA_KEY}, headers=headers, timeout=10).json()
        solved = solve_challenge(challenge)
        
        verified = sess.post('https://altcha.mypanel.link/v1/verify', params={'apiKey': ALTCHA_KEY}, json={'payload': solved}, timeout=10).json()
        altcha = base64.b64encode(json.dumps(verified).encode()).decode()

        # 3. Ro'yxatdan o'tish
        user = "u_" + "".join(random.choices(string.ascii_lowercase, k=7))
        sess.post(f"{HOST}/signup", data={
            'RegistrationForm[login]': user, 'RegistrationForm[email]': f"{user}@gmail.com",
            'RegistrationForm[password]': 'Pass123!', 'RegistrationForm[password_again]': 'Pass123!',
            '_csrf': token, 'altcha': altcha
        }, proxies=px, timeout=10)

        # 4. Buyurtma berish
        order_resp = sess.post(f"{HOST}/order/create", data={
            'OrderForm[category]': service['c'], 'OrderForm[service]': service['i'],
            'OrderForm[link]': link, 'OrderForm[quantity]': service['q'], '_csrf': token
        }, proxies=px, timeout=10)
        
        return order_resp.status_code == 200
    except:
        return False

# --- TELEGRAM BOT QISMI ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Salom! Meni guruh yoki kanalingizga admin qilib hamma funksiysni yoqib qo'shing. Har bir yangi postga avtomatik reaksiya va ko'rishlar yuboraman. 🚀Bizning kanal @vsf_lvl")

@bot.channel_post_handler(content_types=['text', 'photo', 'video'])
def auto_nakrutka(message):
    # Kanalga post tashlanganda ishlaydi
    link = f"https://t.me/{message.chat.username}/{message.message_id}"
    if not message.chat.username: return # Faqat public kanallar uchun

    def process():
        # Kam-kamdan 3-4 marta urish (jami 30-40 ta reaksiya/view uchun)
        for _ in range(3):
            nakrutka_urish(link, 'reactions')
            nakrutka_urish(link, 'views')
            time.sleep(random.randint(30, 60)) # Renderda bloklanmaslik uchun tanaffus

    threading.Thread(target=process).start()

@bot.message_handler(content_types=['new_chat_members'])
def on_join(message):
    for user in message.new_chat_members:
        if user.id == bot.get_me().id:
            bot.send_message(message.chat.id, "Rahmat! Endi bu guruhdagi postlarga ham xizmat ko'rsataman.  ✅ siz bizning premium obunamizni sotib olmoqchi boʻlsangiz @vsf911 ga murojat qilishingiz mumkin. Bu bot faqat ochiq kanallar uchun ishlaydi!")

# Botni 24/7 o'chmasdan ishlashi uchun (Render uchun)
bot.infinity_polling()
