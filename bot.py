import os
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
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- RENDER PORT MUAMMOSINI YECHISH ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot ishlamoqda...")

def run_fake_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# Serverni alohida oqimda ishga tushirish (Render to'xtab qolmasligi uchun)
threading.Thread(target=run_fake_server, daemon=True).start()

# --- SOZLAMALAR ---
API_TOKEN = '8734482130:AAG6C1YqD05xhWxtguonTeqaYVZ6cXTTrm0'
bot = telebot.TeleBot(API_TOKEN)

HOST = "https://smmlox.com"
ALTCHA_KEY = "key_1jhlt1fhm00b2s721es"

SERVICES = {
    'reactions': {'i': '11043', 'c': '35892', 'q': '10'},
    'views': {'i': '10871', 'c': '35892', 'q': '10'}
}

# Proksilarni yuklash
PROXIES = []
try:
    with open('prox100k.txt', 'r') as f:
        for line in f:
            p = line.strip()
            if p: PROXIES.append(f"http://{p}" if "://" not in p else p)
    print(f"Bazada {len(PROXIES)} ta proksi bor.")
except FileNotFoundError:
    print("Xato: prox100k.txt topilmadi!")

def get_random_proxy():
    if not PROXIES: return None
    p = random.choice(PROXIES)
    return {'http': p, 'https': p}

def solve_challenge(challenge):
    salt, chall, maxnum = challenge['salt'], challenge['challenge'], challenge['maxnumber']
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
        resp = sess.get(f"{HOST}/signup", headers=headers, proxies=px, timeout=10)
        token = BeautifulSoup(resp.text, 'html.parser').find('input', {'name': '_csrf'})['value']
        challenge = sess.get('https://altcha.mypanel.link/v1/challenge', params={'apiKey': ALTCHA_KEY}, headers=headers, timeout=10).json()
        solved = solve_challenge(challenge)
        verified = sess.post('https://altcha.mypanel.link/v1/verify', params={'apiKey': ALTCHA_KEY}, json={'payload': solved}, timeout=10).json()
        altcha = base64.b64encode(json.dumps(verified).encode()).decode()
        user = "u_" + "".join(random.choices(string.ascii_lowercase, k=7))
        sess.post(f"{HOST}/signup", data={
            'RegistrationForm[login]': user, 'RegistrationForm[email]': f"{user}@gmail.com",
            'RegistrationForm[password]': 'Pass123!', 'RegistrationForm[password_again]': 'Pass123!',
            '_csrf': token, 'altcha': altcha
        }, proxies=px, timeout=10)
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
    markup = telebot.types.InlineKeyboardMarkup()
    # Botni kanalga yoki guruhga qo'shish tugmalari
    btn_channel = telebot.types.InlineKeyboardButton("📢 Kanalga qo'shish", url=f"https://t.me/{bot.get_me().username}?startchannel=true")
    btn_group = telebot.types.InlineKeyboardButton("👥 Guruhga qo'shish", url=f"https://t.me/{bot.get_me().username}?startgroup=true")
    markup.add(btn_channel, btn_group)
    
    msg = ("Salom! Meni guruh yoki kanalingizga admin qilib hamma funksiyani yoqib qo'shing. "
           "Har bir yangi postga avtomatik reaksiya va ko'rishlar yuboraman. 🚀\n\n"
           "Bizning kanal: @vsf_lvl")
    bot.reply_to(message, msg, reply_markup=markup)

@bot.channel_post_handler(content_types=['text', 'photo', 'video'])
def auto_nakrutka(message):
    if not message.chat.username: return 
    link = f"https://t.me/{message.chat.username}/{message.message_id}"
    
    def process():
        for _ in range(3):
            nakrutka_urish(link, 'reactions')
            nakrutka_urish(link, 'views')
            time.sleep(random.randint(45, 90))
    threading.Thread(target=process).start()

@bot.message_handler(content_types=['new_chat_members'])
def on_join(message):
    for user in message.new_chat_members:
        if user.id == bot.get_me().id:
            info = ("Rahmat! Endi bu guruhdagi postlarga ham xizmat ko'rsataman. ✅\n\n"
                    "Siz bizning premium obunamizni sotib olmoqchi bo'lsangiz @vsf911 ga murojat qilishingiz mumkin. "
                    "Bu bot faqat ochiq kanallar uchun ishlaydi!")
            bot.send_message(message.chat.id, info)

bot.infinity_polling()
        
