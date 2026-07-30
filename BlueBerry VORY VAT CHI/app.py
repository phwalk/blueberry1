import os
import sqlite3
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, abort

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'blueberry-elite-2026'

DB_PATH = os.path.join(os.path.dirname(__file__), 'store.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            email TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ru TEXT NOT NULL,
            name_en TEXT NOT NULL,
            name_hy TEXT NOT NULL,
            category_key TEXT NOT NULL,
            category_ru TEXT NOT NULL,
            category_en TEXT NOT NULL,
            category_hy TEXT NOT NULL,
            price_value INTEGER NOT NULL,
            image TEXT NOT NULL,
            description_ru TEXT,
            description_en TEXT,
            description_hy TEXT,
            featured INTEGER DEFAULT 0,
            stock INTEGER DEFAULT 10
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            user_agent TEXT,
            path TEXT NOT NULL,
            lang TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    ensure_product_columns()


def ensure_product_columns():
    conn = get_db()
    columns = {row[1] for row in conn.execute('PRAGMA table_info(products)').fetchall()}
    if 'featured' not in columns:
        conn.execute('ALTER TABLE products ADD COLUMN featured INTEGER DEFAULT 0')
    if 'stock' not in columns:
        conn.execute('ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 10')
    conn.commit()
    conn.close()


def seed_products():
    conn = get_db()
    existing_names = {row['name_ru'] for row in conn.execute('SELECT name_ru FROM products').fetchall()}
    sample_products = [
        ('iPhone 17 Pro Max', 'iPhone 17 Pro Max', 'iPhone 17 Pro Max', 'phones', 'Телефоны', 'Phones', 'Հեռախոսներ', 749000, 'https://cdsassets.apple.com/live/7WUAS350/images/tech-specs/iphone-17-pro-17-pro-max-hero.png', 'Флагман Apple: A19 Pro, 6,9-дюймовый дисплей ProMotion и система камер 48 Мп.', 'Apple flagship with A19 Pro, 6.9-inch ProMotion display and a 48MP camera system.', 'Apple-ի ֆլագման՝ A19 Pro-ով, 6.9-դյույմանոց ProMotion էկրանով և 48 ՄՊ տեսախցիկների համակարգով։', 1, 6),
        ('iPhone 16 Pro', 'iPhone 16 Pro', 'iPhone 16 Pro', 'phones', 'Телефоны', 'Phones', 'Հեռախոսներ', 599000, 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=900&q=80', 'Премиум смартфон', 'Premium smartphone', 'Պրեմիում սմարթֆոն', 1, 24),
        ('Samsung Galaxy S26 Ultra', 'Samsung Galaxy S26 Ultra', 'Samsung Galaxy S26 Ultra', 'phones', 'Телефоны', 'Phones', 'Հեռախոսներ', 520000, 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=900&q=80', 'Флагманский экран', 'Flagship display', 'Ֆլագման էկրան', 1, 12),
        ('Google Pixel 9 Pro', 'Google Pixel 9 Pro', 'Google Pixel 9 Pro', 'phones', 'Телефоны', 'Phones', 'Հեռախոսներ', 460000, 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?auto=format&fit=crop&w=900&q=80', 'Премиум камера', 'Premium camera', 'Պրեմիում տեսախցիկ', 0, 9),
        ('OnePlus 13', 'OnePlus 13', 'OnePlus 13', 'phones', 'Телефоны', 'Phones', 'Հեռախոսներ', 410000, 'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?auto=format&fit=crop&w=900&q=80', 'Суперскорость', 'Ultra-fast performance', 'Գերարագ աշխատանք', 0, 7),
        ('MacBook Pro M5', 'MacBook Pro M5', 'MacBook Pro M5', 'pcs', 'ПК и ноутбуки', 'PCs and laptops', 'Համակարգիչներ եւ նոութբուք', 1250000, 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80', 'Мощный ноутбук', 'Powerful laptop', 'Հզոր նոութբուք', 1, 8),
        ('Dell XPS 15', 'Dell XPS 15', 'Dell XPS 15', 'pcs', 'ПК и ноутбуки', 'PCs and laptops', 'Համակարգիչներ եւ նոութբուք', 980000, 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=900&q=80', 'Премиальный ультрабук', 'Premium ultrabook', 'Պրեմիում ուլտրա-բուք', 0, 10),
        ('ASUS ROG Strix', 'ASUS ROG Strix', 'ASUS ROG Strix', 'pcs', 'ПК и ноутбуки', 'PCs and laptops', 'Համակարգիչներ եւ նոութբուք', 880000, 'https://images.unsplash.com/photo-1591799265444-d66432b91588?auto=format&fit=crop&w=900&q=80', 'Игровой ноутбук', 'Gaming laptop', 'Խաղային նոութբուք', 0, 6),
        ('iMac 2026', 'iMac 2026', 'iMac 2026', 'pcs', 'ПК и ноутбуки', 'PCs and laptops', 'Համակարգիչներ եւ նոութբուք', 1450000, 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=900&q=80', 'Премиальный iMac', 'Premium iMac', 'Պրեմիում iMac', 1, 5),
        ('PlayStation 5 Pro', 'PlayStation 5 Pro', 'PlayStation 5 Pro', 'gaming', 'Игры', 'Gaming', 'Խաղեր', 420000, 'https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?auto=format&fit=crop&w=900&q=80', 'Игровая консоль', 'Gaming console', 'Խաղային համակարգ', 0, 11),
        ('Xbox Series X', 'Xbox Series X', 'Xbox Series X', 'gaming', 'Игры', 'Gaming', 'Խաղեր', 390000, 'https://images.unsplash.com/photo-1606813907291-d86efa9b94db?auto=format&fit=crop&w=900&q=80', 'Мощная консоль', 'Powerful console', 'Հզոր հարթակ', 0, 9),
        ('Nintendo Switch OLED', 'Nintendo Switch OLED', 'Nintendo Switch OLED', 'gaming', 'Игры', 'Gaming', 'Խաղեր', 270000, 'https://images.unsplash.com/photo-1578303512597-81e6cc155b3e?auto=format&fit=crop&w=900&q=80', 'Портативная консоль', 'Portable console', 'Պորտատիվ համակարգ', 0, 8),
        ('AirPods Pro', 'AirPods Pro', 'AirPods Pro', 'accessories', 'Аксессуары', 'Accessories', 'Աքսեսուարներ', 99000, 'https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?auto=format&fit=crop&w=900&q=80', 'Беспроводные наушники', 'Wireless earbuds', 'Անլար ականջակալներ', 0, 17),
        ('Sony WH-1000XM5', 'Sony WH-1000XM5', 'Sony WH-1000XM5', 'accessories', 'Аксессуары', 'Accessories', 'Աքսեսուարներ', 260000, 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80', 'Тихий звук', 'Noise-cancelling audio', 'Անկյունային ձայն', 0, 15),
        ('Logitech MX Master 3S', 'Logitech MX Master 3S', 'Logitech MX Master 3S', 'accessories', 'Аксессуары', 'Accessories', 'Աքսեսուարներ', 170000, 'https://images.unsplash.com/photo-1527814050087-3793815479db?auto=format&fit=crop&w=900&q=80', 'Премиальная мышь', 'Premium mouse', 'Պրեմիում մկնիկ', 0, 14),
        ('Apple Watch Ultra 2', 'Apple Watch Ultra 2', 'Apple Watch Ultra 2', 'accessories', 'Аксессуары', 'Accessories', 'Աքսեսուարներ', 330000, 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=900&q=80', 'Умные часы', 'Smart watch', 'Խելացի ժամացույց', 0, 22),
        ('Samsung QLED 4K', 'Samsung QLED 4K', 'Samsung QLED 4K', 'pcs', 'ПК и ноутбуки', 'PCs and laptops', 'Համակարգիչներ եւ նոութբուք', 780000, 'https://images.unsplash.com/photo-1593305841991-05c297ba1b6f?auto=format&fit=crop&w=900&q=80', 'Телевизор 4K', '4K TV', '4K հեռուստացույց', 0, 4),
        ('Garmin Fenix 7', 'Garmin Fenix 7', 'Garmin Fenix 7', 'accessories', 'Аксессуары', 'Accessories', 'Աքսեսուարներ', 320000, 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=900&q=80', 'Премиальные умные часы', 'Premium smartwatch', 'Պրեմիում սմարթ ժամացույց', 1, 13),
        ('Beats Studio Pro', 'Beats Studio Pro', 'Beats Studio Pro', 'accessories', 'Аксессуары', 'Accessories', 'Աքսեսուարներ', 220000, 'https://images.unsplash.com/photo-1518444065439-e933c06ce9cd?auto=format&fit=crop&w=900&q=80', 'Профессиональные наушники', 'Professional headphones', 'Պրոֆեսионալ ականջակալներ', 0, 12),
        ('Sony Alpha a7 IV', 'Sony Alpha a7 IV', 'Sony Alpha a7 IV', 'pcs', 'ПК и ноутбуки', 'PCs and laptops', 'Համակարգիչներ եւ նոութբուք', 1650000, 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=80', 'Профессиональная камера', 'Professional camera', 'Պրոֆեսիոնալ տեսախցիկ', 0, 3),
        ('DJI Mini 4 Pro', 'DJI Mini 4 Pro', 'DJI Mini 4 Pro', 'gaming', 'Игры', 'Gaming', 'Խաղեր', 760000, 'https://images.unsplash.com/photo-1509695507497-903c5b7d7c1a?auto=format&fit=crop&w=900&q=80', 'Квадрокоптер для съемки', 'Camera drone', 'Տեսախցիկի դերոժամ', 0, 6),
        ('Tesla Model 3 Charger', 'Tesla Model 3 Charger', 'Tesla Model 3 Charger', 'accessories', 'Аксессуары', 'Accessories', 'Աքսեսուարներ', 180000, 'https://images.unsplash.com/photo-1593941707882-a5bac6861d75?auto=format&fit=crop&w=900&q=80', 'Зарядка для электромобиля', 'EV charging station', 'Էլեկտրամոբիլի լիցքավորում', 0, 16),
        ('Canon EOS R10', 'Canon EOS R10', 'Canon EOS R10', 'pcs', 'ПК и ноутбуки', 'PCs and laptops', 'Համակարգիչներ եւ նոուտբուք', 1180000, 'https://images.unsplash.com/photo-1495707902642-75cac588d2e9?auto=format&fit=crop&w=900&q=80', 'Камера для контента', 'Content camera', 'Բովանդակության տեսախցիկ', 0, 5),
        ('Bose SoundLink Flex', 'Bose SoundLink Flex', 'Bose SoundLink Flex', 'accessories', 'Аксессуары', 'Accessories', 'Աքսեսուարներ', 140000, 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=900&q=80', 'Портативная акустика', 'Portable speaker', 'Պորտատիվ խոսնակ', 0, 11)
    ]
    to_insert = [product for product in sample_products if product[0] not in existing_names]
    if to_insert:
        conn.executemany('''
            INSERT INTO products (name_ru, name_en, name_hy, category_key, category_ru, category_en, category_hy, price_value, image, description_ru, description_en, description_hy, featured, stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', to_insert)
    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def seed_admin_user():
    conn = get_db()
    existing = conn.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
    if not existing:
        conn.execute('INSERT INTO users (username, password_hash, email, is_admin) VALUES (?, ?, ?, 1)', ('admin', hash_password('admin123'), 'admin@blueberry.store'))
        conn.commit()
    conn.close()

def check_and_migrate_users():
    conn = get_db()
    columns = {row[1] for row in conn.execute('PRAGMA table_info(users)').fetchall()}
    if 'password_hash' in columns and 'password' in columns:
        conn.execute("ALTER TABLE users RENAME COLUMN password TO password_old")
        conn.commit()
    elif 'password_hash' not in columns:
        conn.execute('ALTER TABLE users ADD COLUMN password_hash TEXT')
        conn.commit()
        rows = conn.execute('SELECT id, password FROM users WHERE password IS NOT NULL').fetchall()
        for row in rows:
            conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', (hash_password(row['password']), row['id']))
        conn.commit()
    conn.close()

@app.route('/profile')
def profile():
    if not session.get('user'):
        return redirect(url_for('home', lang=session.get('lang', 'ru')))
    lang = request.args.get('lang', session.get('lang', 'ru')).lower()
    if lang not in translations:
        lang = 'ru'
    session['lang'] = lang
    conn = get_db()
    user = conn.execute('SELECT username, email, is_admin FROM users WHERE username = ?', (session['user']['username'],)).fetchone()
    conn.close()
    return render_template(
        'profile.html',
        lang=lang,
        t=translations[lang],
        user=dict(user) if user else None,
        cart_count=sum(session.get('cart', {}).values()),
        message=session.pop('message', None),
    )

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if not session.get('user'):
        return redirect(url_for('home'))
    email = request.form.get('email', '').strip()
    if email:
        conn = get_db()
        conn.execute('UPDATE users SET email = ? WHERE username = ?', (email, session['user']['username']))
        conn.commit()
        conn.close()
        session['message'] = 'Profile updated'
    return redirect(url_for('profile', lang=session.get('lang', 'ru')))

@app.route('/change_password', methods=['POST'])
def change_password():
    if not session.get('user'):
        return redirect(url_for('home'))
    old_pw = request.form.get('old_password', '')
    new_pw = request.form.get('new_password', '')
    conn = get_db()
    user = conn.execute('SELECT password_hash FROM users WHERE username = ?', (session['user']['username'],)).fetchone()
    if user and user['password_hash'] == hash_password(old_pw):
        conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', (hash_password(new_pw), session['user']['username']))
        conn.commit()
        session['message'] = 'Password changed'
    else:
        session['message'] = 'Wrong current password'
    conn.close()
    return redirect(url_for('profile', lang=session.get('lang', 'ru')))


init_db()
check_and_migrate_users()
seed_products()
seed_admin_user()


def format_price(value):
    return f'{value:,.0f}'.replace(',', ' ') + ' ֏'


# Характеристики в каталоге отделены от цен и остатков: цены демонстрационные,
# а параметры устройств взяты из спецификаций производителей.
PRODUCT_FACTS = {
    'iPhone 17 Pro Max': {
        'summary': 'Флагманский iPhone с большой 6,9-дюймовой панелью, чипом A19 Pro и профессиональной системой из трёх 48‑Мп камер.',
        'specs': [
            ('Дисплей', '6,9″ Super Retina XDR OLED, 2868×1320, ProMotion до 120 Гц'),
            ('Процессор', 'Apple A19 Pro: 6-ядерный CPU, 6-ядерный GPU, 16-ядерный Neural Engine'),
            ('Камеры', '48 Мп основная + 48 Мп сверхширокоугольная + 48 Мп телефото 4×; оптический зум до 8×'),
            ('Память', '256 ГБ, 512 ГБ, 1 ТБ или 2 ТБ'),
            ('Зарядка', 'USB‑C (USB 3 до 10 Гбит/с), MagSafe и Qi2 до 25 Вт'),
            ('Защита', 'IP68: погружение до 6 м на срок до 30 минут'),
            ('Корпус', 'Алюминиевый unibody, Ceramic Shield 2 спереди; 78 × 163,4 × 8,75 мм, 231 г'),
        ],
        'highlights': [('6,9″', 'Super Retina XDR'), ('A19 Pro', 'чип профессионального уровня'), ('48 Мп', 'три камеры Fusion')],
        'tags': {'камера', 'флагман', 'oled', '5g'},
        'alternatives': ['iPhone 16 Pro', 'Samsung Galaxy S26 Ultra', 'Google Pixel 9 Pro', 'OnePlus 13'],
        'source_url': 'https://support.apple.com/en-euro/125091',
        'source_name': 'Apple — технические характеристики',
    },
    'iPhone 16 Pro': {
        'summary': 'Компактный профессиональный iPhone с 6,3-дюймовым дисплеем, A18 Pro и системой камер 48 Мп.',
        'specs': [('Дисплей', '6,3″ Super Retina XDR OLED, ProMotion до 120 Гц'), ('Процессор', 'Apple A18 Pro'), ('Камеры', '48 Мп основная, 48 Мп сверхширокоугольная, 12 Мп телефото 5×'), ('Память', '128 ГБ, 256 ГБ, 512 ГБ или 1 ТБ'), ('Защита', 'IP68'), ('Разъём', 'USB‑C с поддержкой USB 3')],
        'highlights': [('A18 Pro', 'быстрый и энергоэффективный'), ('5×', 'оптический телефото'), ('Titanium', 'титановый корпус')],
        'tags': {'камера', 'флагман', 'oled', '5g'},
        'alternatives': ['iPhone 17 Pro Max', 'Google Pixel 9 Pro', 'Samsung Galaxy S26 Ultra'],
    },
    'Samsung Galaxy S26 Ultra': {
        'summary': 'Большой Android-флагман для мобильной фотографии, стилуса S Pen и работы на 6,9‑дюймовом экране.',
        'specs': [('Дисплей', '6,9″ Dynamic AMOLED 2X, адаптивная частота до 120 Гц'), ('Камера', 'Основной сенсор 200 Мп и система телефото-камер'), ('Производительность', 'Флагманская платформа Snapdragon для Galaxy'), ('Перо', 'Встроенный S Pen'), ('Связь', '5G, Wi‑Fi и Bluetooth последнего поколения'), ('Защита', 'Влагозащита IP68')],
        'highlights': [('200 Мп', 'детализированная основная камера'), ('S Pen', 'заметки и точное управление'), ('6,9″', 'большой AMOLED‑экран')],
        'tags': {'камера', 'флагман', 'oled', '5g'},
        'alternatives': ['iPhone 17 Pro Max', 'Google Pixel 9 Pro', 'OnePlus 13'],
    },
    'Google Pixel 9 Pro': {
        'summary': 'Флагман Pixel с чистым Android, вычислительной фотографией Google и компактным профессиональным корпусом.',
        'specs': [('Дисплей', '6,3″ LTPO OLED, 1–120 Гц'), ('Процессор', 'Google Tensor G4'), ('Камеры', '50 Мп широкоугольная, 48 Мп сверхширокоугольная и 48 Мп телефото 5×'), ('Память', '16 ГБ RAM; накопитель до 1 ТБ'), ('Защита', 'IP68'), ('Связь', '5G, Wi‑Fi 7, NFC')],
        'highlights': [('Tensor G4', 'функции Google AI на устройстве'), ('5×', 'оптическое приближение'), ('16 ГБ', 'оперативной памяти')],
        'tags': {'камера', 'флагман', 'oled', '5g'},
        'alternatives': ['iPhone 17 Pro Max', 'Samsung Galaxy S26 Ultra', 'OnePlus 13'],
    },
    'OnePlus 13': {
        'summary': 'Скоростной смартфон с большим LTPO-экраном, тройной камерой и ёмкой батареей.',
        'specs': [('Дисплей', '6,82″ LTPO AMOLED, адаптивная частота 1–120 Гц'), ('Процессор', 'Snapdragon 8 Elite'), ('Камеры', 'Три 50‑Мп камеры, включая перископический телефото-модуль 3×'), ('Батарея', '6000 мА·ч'), ('Зарядка', 'Проводная 100 Вт и беспроводная 50 Вт'), ('Защита', 'IP68/IP69')],
        'highlights': [('6000 мА·ч', 'двухэлементная батарея'), ('100 Вт', 'быстрая зарядка'), ('3×', 'перископический зум')],
        'tags': {'камера', 'флагман', 'oled', '5g'},
        'alternatives': ['Samsung Galaxy S26 Ultra', 'Google Pixel 9 Pro', 'iPhone 17 Pro Max'],
    },
    'MacBook Pro M5': {
        'summary': 'Профессиональный ноутбук Apple для разработки, монтажа, графики и повседневной работы.',
        'specs': [('Дисплей', 'Liquid Retina XDR с широкой цветовой гаммой P3 и ProMotion'), ('Платформа', 'Apple silicon семейства M5'), ('Память', 'Унифицированная память и SSD в зависимости от конфигурации'), ('Порты', 'Thunderbolt, HDMI, SDXC и MagSafe'), ('Камера', '12 Мп Center Stage'), ('Автономность', 'До 24 часов в зависимости от конфигурации и сценария')],
        'highlights': [('M5', 'Apple silicon'), ('XDR', 'контрастный дисплей'), ('Pro', 'набор профессиональных портов')],
        'tags': {'ноутбук', 'производительность', 'контент'},
        'alternatives': ['Dell XPS 15', 'ASUS ROG Strix', 'iMac 2026'],
    },
    'Dell XPS 15': {
        'summary': '15-дюймовый премиальный Windows-ноутбук: производительность, компактный корпус и качественный экран.',
        'specs': [('Дисплей', '15,6″, варианты FHD+ или 3,5K OLED'), ('Процессор', 'Intel Core 13-го поколения в зависимости от конфигурации'), ('Графика', 'Дискретная NVIDIA GeForce RTX 40-й серии в старших конфигурациях'), ('Память', 'До 64 ГБ DDR5'), ('Накопитель', 'PCIe SSD'), ('Порты', 'Thunderbolt 4, USB‑C, SD-картридер')],
        'highlights': [('15,6″', 'рабочее пространство'), ('OLED', 'опциональная панель'), ('RTX', 'ускорение графики')],
        'tags': {'ноутбук', 'производительность', 'контент'},
        'alternatives': ['MacBook Pro M5', 'ASUS ROG Strix', 'iMac 2026'],
    },
    'ASUS ROG Strix': {
        'summary': 'Игровой ноутбук ROG Strix для высоких частот кадров, стриминга и тяжёлых задач.',
        'specs': [('Дисплей', '16″ IPS, варианты до 2560×1600 и 240 Гц'), ('Процессор', 'Intel Core HX в зависимости от конфигурации'), ('Графика', 'NVIDIA GeForce RTX 40-й серии'), ('Охлаждение', 'Многовентиляторная система ROG'), ('Память', 'DDR5, расширяемая'), ('Связь', 'Wi‑Fi 6E / Bluetooth')],
        'highlights': [('240 Гц', 'плавный геймплей'), ('RTX', 'дискретная графика'), ('ROG', 'эффективное охлаждение')],
        'tags': {'ноутбук', 'игры', 'производительность'},
        'alternatives': ['Dell XPS 15', 'MacBook Pro M5', 'PlayStation 5 Pro'],
    },
    'iMac 2026': {
        'summary': 'Моноблок Apple с большим 4,5K-дисплеем и минималистичным рабочим местом без лишних проводов.',
        'specs': [('Дисплей', '24″ Retina 4,5K с поддержкой P3'), ('Платформа', 'Apple silicon'), ('Камера', '12 Мп Center Stage'), ('Аудио', 'Шесть динамиков и поддержка Spatial Audio'), ('Связь', 'Wi‑Fi 6E и Bluetooth 5.3'), ('Комплектация', 'Клавиатура и мышь или трекпад')],
        'highlights': [('4,5K', 'Retina-дисплей'), ('24″', 'просторный экран'), ('All‑in‑one', 'минимум проводов')],
        'tags': {'компьютер', 'контент', 'дизайн'},
        'alternatives': ['MacBook Pro M5', 'Dell XPS 15', 'Sony Alpha a7 IV'],
    },
    'PlayStation 5 Pro': {
        'summary': 'Продвинутая консоль PlayStation с усиленной графикой, трассировкой лучей и SSD 2 ТБ.',
        'specs': [('Графика', 'Улучшенный GPU AMD с продвинутой трассировкой лучей'), ('Хранилище', 'Встроенный SSD 2 ТБ'), ('Изображение', 'Поддержка 4K, VRR, HDR и вывода до 120 Гц в совместимых играх'), ('Сеть', 'Wi‑Fi 7, Ethernet, Bluetooth'), ('Оптика', 'Привод приобретается отдельно'), ('Совместимость', 'Большинство игр для PS4 и PS5')],
        'highlights': [('2 ТБ', 'встроенный SSD'), ('4K', 'высокое разрешение'), ('Ray tracing', 'улучшенное освещение')],
        'tags': {'игры', 'консоль', '4k'},
        'alternatives': ['Xbox Series X', 'Nintendo Switch OLED', 'ASUS ROG Strix'],
    },
    'Xbox Series X': {
        'summary': 'Мощная консоль Xbox для 4K-игр, Game Pass и обратной совместимости.',
        'specs': [('Процессор', '8-ядерный AMD Zen 2'), ('Графика', 'AMD RDNA 2, до 12 TFLOPS'), ('Хранилище', 'Скоростной NVMe SSD 1 ТБ'), ('Изображение', 'До 4K и 120 кадров/с в совместимых играх'), ('Оптика', 'Дисковод Blu‑ray 4K'), ('Совместимость', 'Игры Xbox One, Xbox 360 и оригинального Xbox')],
        'highlights': [('12 TFLOPS', 'графическая мощность'), ('4K 120', 'в совместимых играх'), ('Game Pass', 'библиотека игр')],
        'tags': {'игры', 'консоль', '4k'},
        'alternatives': ['PlayStation 5 Pro', 'Nintendo Switch OLED', 'ASUS ROG Strix'],
    },
    'Nintendo Switch OLED': {
        'summary': 'Гибридная консоль с ярким OLED-экраном — играйте дома на телевизоре и в дороге.',
        'specs': [('Дисплей', '7″ OLED, 1280×720'), ('Режимы', 'Портативный, настольный и телевизионный'), ('Хранилище', '64 ГБ, поддержка microSD'), ('Автономность', 'Около 4,5–9 часов в зависимости от игры'), ('Подключение', 'Wi‑Fi, Bluetooth; LAN‑порт в док-станции'), ('Контроллеры', 'Пара Joy‑Con в комплекте')],
        'highlights': [('OLED', 'контрастный 7″ экран'), ('3 режима', 'игра где удобно'), ('64 ГБ', 'внутренняя память')],
        'tags': {'игры', 'консоль', 'портативный'},
        'alternatives': ['PlayStation 5 Pro', 'Xbox Series X', 'ASUS ROG Strix'],
    },
    'AirPods Pro': {
        'summary': 'Компактные беспроводные наушники Apple с активным шумоподавлением и пространственным аудио.',
        'specs': [('Шумоподавление', 'Адаптивное активное шумоподавление и режим прозрачности'), ('Чип', 'Apple H2'), ('Звук', 'Персонализированное пространственное аудио'), ('Корпус', 'Защита от пыли, пота и воды IP54'), ('Зарядка', 'MagSafe, Qi или USB‑C в зависимости от кейса'), ('Совместимость', 'iPhone, iPad, Mac, Apple Watch и другие Bluetooth-устройства')],
        'highlights': [('H2', 'адаптивная обработка звука'), ('ANC', 'активное шумоподавление'), ('IP54', 'защита для тренировок')],
        'tags': {'аудио', 'портативный', 'шумоподавление'},
        'alternatives': ['Sony WH-1000XM5', 'Beats Studio Pro', 'Bose SoundLink Flex'],
    },
    'Sony WH-1000XM5': {
        'summary': 'Полноразмерные наушники Sony с одним из лучших активных шумоподавлений и комфортной посадкой.',
        'specs': [('Динамики', '30‑мм драйверы'), ('Шумоподавление', 'Процессоры Integrated Processor V1 и HD Noise Canceling Processor QN1'), ('Автономность', 'До 30 часов с ANC'), ('Подключение', 'Bluetooth 5.2, LDAC, 3,5‑мм аудиокабель'), ('Микрофоны', 'Восемь микрофонов для звонков и ANC'), ('Вес', 'Около 250 г')],
        'highlights': [('30 ч', 'работы с ANC'), ('LDAC', 'аудио высокого разрешения'), ('8 микрофонов', 'для звонков и ANC')],
        'tags': {'аудио', 'шумоподавление', 'портативный'},
        'alternatives': ['AirPods Pro', 'Beats Studio Pro', 'Bose SoundLink Flex'],
    },
    'Logitech MX Master 3S': {
        'summary': 'Эргономичная мышь для работы с несколькими компьютерами и точной прокрутки больших документов.',
        'specs': [('Сенсор', 'Darkfield 8000 DPI'), ('Кнопки', 'Тихие клики Quiet Clicks'), ('Прокрутка', 'Электромагнитное колесо MagSpeed'), ('Подключение', 'Bluetooth Low Energy или Logi Bolt'), ('Автономность', 'До 70 дней от одного заряда'), ('Совместимость', 'Windows, macOS, Linux, ChromeOS, iPadOS')],
        'highlights': [('8000 DPI', 'работа даже на стекле'), ('70 дней', 'до следующей зарядки'), ('MagSpeed', 'быстрая прокрутка')],
        'tags': {'работа', 'компьютер', 'портативный'},
        'alternatives': ['MacBook Pro M5', 'Dell XPS 15', 'iMac 2026'],
    },
    'Apple Watch Ultra 2': {
        'summary': 'Прочные 49‑мм часы Apple для спорта, путешествий, воды и точной навигации.',
        'specs': [('Корпус', '49 мм, титан'), ('Дисплей', 'Always‑On Retina, яркость до 3000 нит'), ('Процессор', 'S9 SiP'), ('Автономность', 'До 36 часов в обычном режиме'), ('Защита', 'Водонепроницаемость до 100 м, пылезащита IP6X'), ('Навигация', 'Двухчастотный GPS')],
        'highlights': [('49 мм', 'прочный титановый корпус'), ('100 м', 'водозащита'), ('3000 нит', 'яркий экран')],
        'tags': {'спорт', 'носимый', 'gps'},
        'alternatives': ['Garmin Fenix 7', 'iPhone 17 Pro Max', 'AirPods Pro'],
    },
    'Samsung QLED 4K': {
        'summary': 'Телевизор Samsung QLED 4K для фильмов, спорта и игр на большом экране.',
        'specs': [('Панель', 'QLED 4K с квантовыми точками'), ('Изображение', '4K‑апскейлинг и HDR в зависимости от серии'), ('Игры', 'Автоматический игровой режим и HDMI для консолей'), ('Смарт-платформа', 'Samsung Tizen OS'), ('Звук', 'Поддержка Q‑Symphony с совместимыми саундбарами'), ('Примечание', 'Точные диагональ, частота и набор портов зависят от выбранной версии')],
        'highlights': [('QLED', 'яркие насыщенные цвета'), ('4K', 'детализированная картинка'), ('Tizen', 'стриминговые приложения')],
        'tags': {'тв', '4k', 'игры'},
        'alternatives': ['PlayStation 5 Pro', 'Xbox Series X', 'Bose SoundLink Flex'],
    },
    'Garmin Fenix 7': {
        'summary': 'Мультиспортивные GPS‑часы для тренировок, туризма и контроля восстановления.',
        'specs': [('Дисплей', '1,3″ transflective MIP'), ('Корпус', '47 мм; варианты из нержавеющей стали или титана'), ('Автономность', 'До 18 дней в режиме часов'), ('Защита', 'Водонепроницаемость 10 ATM'), ('Навигация', 'Мультиспутниковый GPS и карты'), ('Датчики', 'Пульс, Pulse Ox, компас, альтиметр, барометр')],
        'highlights': [('18 дней', 'автономности'), ('10 ATM', 'для плавания'), ('GPS', 'маршруты и треки')],
        'tags': {'спорт', 'носимый', 'gps'},
        'alternatives': ['Apple Watch Ultra 2', 'iPhone 17 Pro Max', 'AirPods Pro'],
    },
    'Beats Studio Pro': {
        'summary': 'Полноразмерные Bluetooth-наушники Beats с адаптивным шумоподавлением и USB‑C-аудио.',
        'specs': [('Шумоподавление', 'Активное ANC и режим прозрачности'), ('Автономность', 'До 40 часов без ANC; до 24 часов с ANC'), ('Подключение', 'Bluetooth, 3,5‑мм аудио и USB‑C'), ('Звук', 'Персонализированное пространственное аудио'), ('Микрофоны', 'Улучшенные микрофоны для звонков'), ('Вес', 'Около 260 г')],
        'highlights': [('40 ч', 'без ANC'), ('USB‑C', 'аудио и зарядка'), ('ANC', 'адаптивное шумоподавление')],
        'tags': {'аудио', 'шумоподавление', 'портативный'},
        'alternatives': ['Sony WH-1000XM5', 'AirPods Pro', 'Bose SoundLink Flex'],
    },
    'Sony Alpha a7 IV': {
        'summary': 'Полнокадровая беззеркальная камера Sony для фото, видеосъёмки и гибридных проектов.',
        'specs': [('Сенсор', 'Полнокадровый Exmor R CMOS 33 Мп'), ('Видео', '4K до 60p; 10‑бит 4:2:2'), ('Автофокус', '759 фазовых точек, Real‑time Eye AF'), ('Стабилизация', '5‑осевая IBIS до 5,5 ступеней'), ('Серийная съёмка', 'До 10 кадров/с'), ('Носители', 'Два слота SD/CFexpress Type A')],
        'highlights': [('33 Мп', 'полнокадровый сенсор'), ('4K 60p', 'видеосъёмка'), ('759 точек', 'фазовый автофокус')],
        'tags': {'камера', 'контент', 'профессиональный'},
        'alternatives': ['Canon EOS R10', 'DJI Mini 4 Pro', 'MacBook Pro M5'],
    },
    'DJI Mini 4 Pro': {
        'summary': 'Складной дрон DJI массой менее 249 г с 4K-видео, всенаправленным обнаружением препятствий и вертикальной съёмкой.',
        'specs': [('Вес', 'Менее 249 г со стандартной батареей'), ('Камера', '1/1,3″ CMOS, 48 Мп'), ('Видео', '4K до 100 кадров/с, D‑Log M и HLG'), ('Безопасность', 'Всенаправленное обнаружение препятствий'), ('Время полёта', 'До 34 минут со стандартной батареей'), ('Связь', 'O4, передача видео до 20 км при идеальных условиях')],
        'highlights': [('<249 г', 'небольшой и складной'), ('4K 100', 'замедленное видео'), ('360°', 'обнаружение препятствий')],
        'tags': {'камера', 'контент', 'портативный'},
        'alternatives': ['Sony Alpha a7 IV', 'Canon EOS R10', 'MacBook Pro M5'],
    },
    'Tesla Model 3 Charger': {
        'summary': 'Настенная зарядная станция для электромобиля Tesla и совместимых автомобилей (зависит от версии коннектора).',
        'specs': [('Мощность', 'До 48 А при жёстком подключении, в зависимости от электросети'), ('Подключение', 'Wi‑Fi для обновлений и управления'), ('Установка', 'Настенная, для дома или коммерческого объекта'), ('Совместимость', 'Зависит от выбранной версии Wall Connector'), ('Условия', 'Подходит для установки в помещении и на улице'), ('Важно', 'Монтаж должен выполнять квалифицированный электрик')],
        'highlights': [('48 А', 'до при жёстком подключении'), ('Wi‑Fi', 'обновления по сети'), ('Wallbox', 'стационарная установка')],
        'tags': {'дом', 'электромобиль', 'зарядка'},
        'alternatives': ['iPhone 17 Pro Max', 'Samsung QLED 4K', 'Bose SoundLink Flex'],
    },
    'Canon EOS R10': {
        'summary': 'Лёгкая APS‑C беззеркальная камера Canon для фото, видео и динамичных сюжетов.',
        'specs': [('Сенсор', 'APS‑C CMOS 24,2 Мп'), ('Видео', '4K 60p с кропом; 4K 30p с передискретизацией'), ('Автофокус', 'Dual Pixel CMOS AF II с распознаванием объектов'), ('Серийная съёмка', 'До 15 кадров/с с механическим затвором; до 23 кадров/с электронно'), ('Экран', 'Поворотный сенсорный 3″'), ('Вес', 'Около 429 г с картой и батареей')],
        'highlights': [('24,2 Мп', 'детализированные кадры'), ('4K 60p', 'видео'), ('23 кадр/с', 'электронный затвор')],
        'tags': {'камера', 'контент', 'портативный'},
        'alternatives': ['Sony Alpha a7 IV', 'DJI Mini 4 Pro', 'MacBook Pro M5'],
    },
    'Bose SoundLink Flex': {
        'summary': 'Компактная Bluetooth-колонка Bose с прочным влагозащищённым корпусом для дома и поездок.',
        'specs': [('Защита', 'IP67: защита от воды и пыли'), ('Автономность', 'До 12 часов воспроизведения'), ('Связь', 'Bluetooth с приложением Bose'), ('Звук', 'PositionIQ подстраивает звук под положение колонки'), ('Корпус', 'Компактный, с петлёй для переноски'), ('Вес', 'Около 0,6 кг')],
        'highlights': [('IP67', 'вода и пыль'), ('12 ч', 'работы'), ('PositionIQ', 'автоподстройка звука')],
        'tags': {'аудио', 'портативный', 'дом'},
        'alternatives': ['AirPods Pro', 'Sony WH-1000XM5', 'Beats Studio Pro'],
    },
}


def get_product_facts(product):
    facts = PRODUCT_FACTS.get(product['name_en'])
    if facts:
        return facts
    return {
        'summary': product.get('description_ru') or 'Подробные характеристики добавляются менеджером магазина.',
        'specs': [('Категория', product.get('category_ru', '—')), ('Наличие', f"{product.get('stock', 0)} шт."), ('Артикул', f"BB-{product.get('id', '—'):04}")],
        'highlights': [('BlueBerry', 'проверка перед выдачей'), ('Демо‑цена', 'уточняется менеджером'), ('Самовывоз', 'по согласованию')],
        'tags': {product.get('category_key', 'other')},
        'alternatives': [],
    }


def enrich_product(product):
    product = dict(product)
    facts = PRODUCT_FACTS.get(product['name_en'])
    if facts:
        product['description_ru'] = facts['summary']
    product['price_text'] = format_price(product['price_value'])
    return product


def get_products_from_db():
    conn = get_db()
    rows = conn.execute('SELECT * FROM products ORDER BY featured DESC, id DESC').fetchall()
    conn.close()
    return [enrich_product(row) for row in rows]


def get_product_by_id(product_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    return enrich_product(row) if row else None


def get_recommendations(product):
    products = get_products_from_db()
    candidates = [item for item in products if item['id'] != product['id']]
    current_facts = get_product_facts(product)
    current_tags = set(current_facts.get('tags', set()))

    similar = sorted(
        candidates,
        key=lambda item: (
            item['category_key'] != product['category_key'],
            abs(item['price_value'] - product['price_value']),
        ),
    )[:4]

    names = current_facts.get('alternatives', [])
    by_name = {item['name_en']: item for item in candidates}
    alternatives = [by_name[name] for name in names if name in by_name]
    if len(alternatives) < 4:
        for item in candidates:
            tags = set(get_product_facts(item).get('tags', set()))
            if item not in alternatives and current_tags.intersection(tags):
                alternatives.append(item)
            if len(alternatives) == 4:
                break
    return similar, alternatives[:4]


def save_product(data):
    conn = get_db()
    conn.execute('''
        INSERT INTO products (name_ru, name_en, name_hy, category_key, category_ru, category_en, category_hy, price_value, image, description_ru, description_en, description_hy, featured, stock)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['name_ru'], data['name_en'], data['name_hy'], data['category_key'],
        data['category_ru'], data['category_en'], data['category_hy'], int(data['price_value']), data['image'],
        data.get('description_ru', ''), data.get('description_en', ''), data.get('description_hy', ''),
        int(data.get('featured', 0)), int(data.get('stock', 10))
    ))
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_db()
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()


def get_analytics():
    conn = get_db()
    total_visits = conn.execute('SELECT COUNT(*) as c FROM visits').fetchone()['c']
    unique_ips = conn.execute('SELECT COUNT(DISTINCT ip) as c FROM visits').fetchone()['c']
    today_visits = conn.execute("SELECT COUNT(*) as c FROM visits WHERE date(created_at) = date('now')").fetchone()['c']
    recent = conn.execute('SELECT * FROM visits ORDER BY id DESC LIMIT 8').fetchall()
    top_ips = conn.execute('SELECT ip, COUNT(*) as count FROM visits GROUP BY ip ORDER BY count DESC LIMIT 8').fetchall()
    conn.close()
    return {
        'total_visits': total_visits,
        'unique_ips': unique_ips,
        'today_visits': today_visits,
        'recent': [dict(row) for row in recent],
        'top_ips': [dict(row) for row in top_ips],
    }


def register_user(username, password, email):
    conn = get_db()
    try:
        conn.execute('INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)', (username, hash_password(password), email))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def authenticate_user(username, password):
    conn = get_db()
    row = conn.execute('SELECT * FROM users WHERE username = ? AND password_hash = ?', (username, hash_password(password))).fetchone()
    conn.close()
    return dict(row) if row else None


@app.after_request
def no_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.before_request
def track_visit():
    if request.path.startswith('/static') or request.path == '/favicon.ico':
        return
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown').split(',')[0].strip()
    conn = get_db()
    conn.execute(
        'INSERT INTO visits (ip, user_agent, path, lang, created_at) VALUES (?, ?, ?, ?, ?)',
        (ip, request.headers.get('User-Agent', 'unknown'), request.path, session.get('lang', 'ru'), datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()


translations = {
    'ru': {
        'title': 'BlueBerry — премиум магазин электроники',
        'subtitle': 'Вход, регистрация, корзина, избранное, поиск и админка — всё в одном магазине.',
        'welcome': 'Добро пожаловать в BlueBerry',
        'search_placeholder': 'Поиск по товарам',
        'all': 'Все',
        'phones': 'Телефоны',
        'pcs': 'ПК',
        'gaming': 'Игры',
        'accessories': 'Аксессуары',
        'cart': 'Корзина',
        'favorites': 'Избранное',
        'reviews': 'Отзывы',
        'payment': 'Оплата',
        'delivery': 'Доставка',
        'login': 'Вход',
        'register': 'Регистрация',
        'logout': 'Выход',
        'admin': 'Админка',
        'hero_button': 'Открыть каталог',
        'empty_cart': 'Корзина пока пуста',
        'empty_favorites': 'Список избранного пуст',
        'order': 'Добавить',
        'submit': 'Оформить заказ',
        'add_product': 'Добавить товар',
        'name': 'Имя',
        'phone': 'Телефон',
        'address': 'Адрес',
        'note': 'Комментарий',
        'success': 'Заказ успешно отправлен',
        'fill_form': 'Введите имя и телефон',
        'added_to_cart': 'Товар добавлен в корзину',
        'total': 'Итого',
        'payments': 'Онлайн-оплата: Idream, Telcell, Visa/MasterCard',
        'delivery_text': 'Доставка по всей Армении 1–2 дня',
        'reviews_text': 'Реальные отзывы и рейтинг по каждому товару',
        'mobile': 'Адаптация под телефон и тёмная тема',
        'auth_title': 'Вход и регистрация',
        'search_title': 'Поиск товаров',
        'category_title': 'Категории с фильтрами',
        'database_title': 'SQLite база данных',
        'admin_title': 'Панель администратора',
        'copyright': 'Все права защищены',
        'username': 'Логин',
        'password': 'Пароль',
        'email': 'Email',
        'lang_switch': 'Язык',
        'catalog': 'Каталог',
        'store_intro': 'Премиальные технологии, реализованные с точностью и стилем.',
        'hero_title': 'Техника без визуального шума.',
        'hero_description': 'Смартфоны, компьютеры, игры и аксессуары. У каждого товара — отдельная страница с характеристиками и подходящими альтернативами.',
        'new_in_catalog': 'Новинка каталога',
        'view_specs': 'Смотреть характеристики',
        'search_button': 'Найти',
        'details': 'Подробнее',
        'demo_price': 'демо-цена',
        'add_to_cart_button': 'Добавить в корзину',
        'add_to_favorites': 'В избранное',
        'in_favorites': 'В избранном',
        'nothing_found': 'По этому запросу ничего не найдено. Попробуйте изменить поиск или категорию.',
        'breadcrumb_nav': 'Навигация',
        'product_image': 'Изображение товара',
        'specifications': 'Характеристики',
        'product_info': 'Информация о товаре',
        'similar_products': 'Похожие товары',
        'compare_products': 'Товары с похожими функциями',
        'compare_before_buy': 'Сравнить перед покупкой',
        'blueberry_picks': 'Подборка BlueBerry',
        'in_stock': 'В наличии',
        'out_of_stock': 'Нет в наличии',
        'pcs_unit': 'шт.',
        'disclaimer': 'Перед покупкой менеджер подтвердит точную конфигурацию, цвет, цену и наличие.',
        'source': 'Источник',
        'personal_account': 'Личный кабинет',
        'change_password': 'Изменить пароль',
        'current_password': 'Текущий пароль',
        'new_password': 'Новый пароль',
        'save': 'Сохранить',
        'role': 'Роль',
        'administrator': 'Администратор',
        'buyer': 'Покупатель',
        'nav_catalog': 'Каталог',
        'nav_management': 'Управление',
        'cart_items': 'Товаров в корзине',
        'theme_label': 'Оформление сайта',
        'theme_light': 'Светлая',
        'theme_graphite': 'Графит',
        'sign_in': 'Войти',
        'sign_out': 'Выйти',
        'no_account': 'Нет аккаунта?',
        'create_account': 'Создать аккаунт',
        'has_account': 'Уже есть аккаунт?',
        'register_link': 'Зарегистрироваться',
        'footer_demo': 'Демонстрационный каталог · цены требуют уточнения',
        'close': 'Закрыть',
        'chat_support': 'Поддержка',
        'chat_online': 'Онлайн',
        'chat_placeholder': 'Написать сообщение...',
        'chat_empty': 'Напишите нам, и мы ответим!',
    },
    'en': {
        'title': 'BlueBerry — premium electronics store',
        'subtitle': 'Login, registration, cart, favorites, search and admin panel — all in one store.',
        'welcome': 'Welcome to BlueBerry',
        'search_placeholder': 'Search products',
        'all': 'All',
        'phones': 'Phones',
        'pcs': 'PCs',
        'gaming': 'Gaming',
        'accessories': 'Accessories',
        'cart': 'Cart',
        'favorites': 'Favorites',
        'reviews': 'Reviews',
        'payment': 'Payment',
        'delivery': 'Delivery',
        'login': 'Login',
        'register': 'Register',
        'logout': 'Logout',
        'admin': 'Admin',
        'hero_button': 'Open catalog',
        'empty_cart': 'Cart is empty',
        'empty_favorites': 'Favorites list is empty',
        'order': 'Add',
        'submit': 'Place order',
        'add_product': 'Add product',
        'name': 'Name',
        'phone': 'Phone',
        'address': 'Address',
        'note': 'Comment',
        'success': 'Order sent successfully',
        'fill_form': 'Please enter your name and phone',
        'added_to_cart': 'Item added to cart',
        'total': 'Total',
        'payments': 'Online payment: Idram, Telcell, Visa/MasterCard',
        'delivery_text': 'Delivery across Armenia in 1–2 days',
        'reviews_text': 'Real reviews and ratings for every item',
        'mobile': 'Mobile-friendly layout with dark theme',
        'auth_title': 'Login and registration',
        'search_title': 'Product search',
        'category_title': 'Categories with filters',
        'database_title': 'SQLite database',
        'admin_title': 'Admin panel',
        'copyright': 'All rights reserved',
        'username': 'Username',
        'password': 'Password',
        'email': 'Email',
        'lang_switch': 'Language',
        'catalog': 'Catalog',
        'store_intro': 'Premium technology delivered with precision and style.',
        'hero_title': 'Tech without visual noise.',
        'hero_description': 'Smartphones, computers, gaming and accessories. Each product has a dedicated page with specs and suitable alternatives.',
        'new_in_catalog': 'New in catalog',
        'view_specs': 'View specifications',
        'search_button': 'Search',
        'details': 'Details',
        'demo_price': 'demo price',
        'add_to_cart_button': 'Add to cart',
        'add_to_favorites': 'Add to favorites',
        'in_favorites': 'In favorites',
        'nothing_found': 'Nothing found for this query. Try changing your search or category.',
        'breadcrumb_nav': 'Navigation',
        'product_image': 'Product image',
        'specifications': 'Specifications',
        'product_info': 'Product information',
        'similar_products': 'Similar products',
        'compare_products': 'Products with similar features',
        'compare_before_buy': 'Compare before buying',
        'blueberry_picks': 'BlueBerry picks',
        'in_stock': 'In stock',
        'out_of_stock': 'Out of stock',
        'pcs_unit': 'pcs',
        'disclaimer': 'Before purchase, a manager will confirm the exact configuration, color, price and availability.',
        'source': 'Source',
        'personal_account': 'My Account',
        'change_password': 'Change password',
        'current_password': 'Current password',
        'new_password': 'New password',
        'save': 'Save',
        'role': 'Role',
        'administrator': 'Administrator',
        'buyer': 'Customer',
        'nav_catalog': 'Catalog',
        'nav_management': 'Management',
        'cart_items': 'Items in cart',
        'theme_label': 'Site theme',
        'theme_light': 'Light',
        'theme_graphite': 'Graphite',
        'sign_in': 'Sign in',
        'sign_out': 'Sign out',
        'no_account': 'No account?',
        'create_account': 'Create account',
        'has_account': 'Already have an account?',
        'register_link': 'Register',
        'footer_demo': 'Demo catalog · prices require confirmation',
        'close': 'Close',
        'chat_support': 'Support',
        'chat_online': 'Online',
        'chat_placeholder': 'Type a message...',
        'chat_empty': 'Send us a message and we will reply!',
    },
    'hy': {
        'title': 'BlueBerry — պրեմիում էլեկտրոնիկայի խանութ',
        'subtitle': 'Մուտք, գրանցում, զամբյուղ, սիրածներ, որոնում եւ ադմին պանել — ամենը մեկ խանութում։',
        'welcome': 'Բարի գալուստ BlueBerry',
        'search_placeholder': 'Որոնել ապրանքներ',
        'all': 'Բոլորը',
        'phones': 'Հեռախոսներ',
        'pcs': 'Համակարգիչներ',
        'gaming': 'Խաղեր',
        'accessories': 'Աքսեսուարներ',
        'cart': 'Զամբյուղ',
        'favorites': 'Սիրածներ',
        'reviews': 'Կարծիքներ',
        'payment': 'Վճարում',
        'delivery': 'Առաքում',
        'login': 'Մուտք',
        'register': 'Գրանցում',
        'logout': 'Ելք',
        'admin': 'Ադմին',
        'hero_button': 'Բացել կատալոգը',
        'empty_cart': 'Զամբյուղը դատարկ է',
        'empty_favorites': 'Սիրածների ցանկը դատարկ է',
        'order': 'Ավելացնել',
        'submit': 'Պատվիրել',
        'add_product': 'Ավելացնել ապրանք',
        'name': 'Անուն',
        'phone': 'Հեռախոս',
        'address': 'Հասցե',
        'note': 'Մեկնարկ',
        'success': 'Պատվերը հաջողությամբ ուղարկվեց',
        'fill_form': 'Խնդրում ենք մուտքագրել անուն եւ հեռախոս',
        'added_to_cart': 'Ապրանքը ավելացվել է զամբյուղ',
        'total': 'Ընդհանուր',
        'payments': 'Առցանց վճարում: Idram, Telcell, Visa/MasterCard',
        'delivery_text': 'Առաքում ողջ Հայաստանում 1–2 օրում',
        'reviews_text': 'Իրական կարծիքներ եւ գնահատականներ յուրաքանչյուր ապրանքի համար',
        'mobile': 'Հարմարեցված մոբայլի համար եւ մութ թեմա',
        'auth_title': 'Մուտք եւ գրանցում',
        'search_title': 'Ապրանքների որոնում',
        'category_title': 'Կատեգորիաներ ֆիլտրով',
        'database_title': 'SQLite տվյալների բազա',
        'admin_title': 'Ադմին պանել',
        'copyright': 'Բոլոր իրավունքները պաշտպանված են',
        'username': 'Օգտատեր',
        'password': 'Գաղտնաբառ',
        'email': 'Email',
        'lang_switch': 'Լեզու',
        'catalog': 'Կատալոգ',
        'store_intro': 'Պրեմիում տեխնոլոգիաներ՝ ճշգրտությամբ եւ ոճով:'
    }
}


@app.route('/', methods=['GET', 'POST'])
def home():
    lang = request.args.get('lang', session.get('lang', 'ru')).lower()
    if lang not in translations:
        lang = 'ru'
    session['lang'] = lang

    search = request.args.get('search', '').strip()
    category = request.args.get('category', 'all')

    products = get_products_from_db()
    if search:
        s = search.lower()
        products = [p for p in products if s in p['name_ru'].lower() or s in p['name_en'].lower() or s in p['name_hy'].lower() or s in (p.get('description_ru') or '').lower() or s in (p.get('description_en') or '').lower() or s in (p.get('description_hy') or '').lower()]
    if category != 'all':
        products = [p for p in products if p['category_key'] == category]

    cart = session.get('cart', {})
    cart_items = []
    cart_total = 0
    for product_id, qty in cart.items():
        product = get_product_by_id(int(product_id))
        if product:
            cart_items.append((product, qty))
            cart_total += product['price_value'] * qty

    favorites = session.get('favorites', [])
    favorite_products = [get_product_by_id(int(pid)) for pid in favorites if get_product_by_id(int(pid))]

    return render_template(
        'catalog.html',
        products=products,
        lang=lang,
        t=translations[lang],
        translations=translations,
        cart_items=cart_items,
        cart_total_text=format_price(cart_total),
        cart_count=sum(cart.values()),
        favorites=favorite_products,
        search=search,
        category=category,
        user=session.get('user'),
        message=session.pop('message', None)
    )


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    lang = request.args.get('lang', session.get('lang', 'ru')).lower()
    if lang not in translations:
        lang = 'ru'
    session['lang'] = lang
    product = get_product_by_id(product_id)
    if not product:
        abort(404)
    favorites = session.get('favorites', [])
    similar, alternatives = get_recommendations(product)
    cart_count = sum(session.get('cart', {}).values())
    return render_template(
        'product.html',
        product=product,
        facts=get_product_facts(product),
        similar=similar,
        alternatives=alternatives,
        lang=lang,
        t=translations[lang],
        user=session.get('user'),
        favorites=favorites,
        cart_count=cart_count,
        message=session.pop('message', None),
    )


@app.route('/iphone')
def iphone():
    product = next((item for item in get_products_from_db() if item['name_en'] == 'iPhone 17 Pro Max'), None)
    if not product:
        return redirect(url_for('home'))
    return redirect(url_for('product_detail', product_id=product['id'], lang=session.get('lang', 'ru')))


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    email = request.form.get('email', '').strip()
    if username and password and email:
        if register_user(username, password, email):
            session['message'] = 'User created'
        else:
            session['message'] = 'Username taken'
    else:
        session['message'] = 'Fill all fields'
    return redirect(url_for('home', lang=session.get('lang', 'ru')))


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    user = authenticate_user(username, password)
    if user:
        session['user'] = {'username': user['username'], 'is_admin': bool(user['is_admin'])}
        session['message'] = 'Welcome'
    else:
        session['message'] = 'Invalid login'
    return redirect(url_for('home', lang=session.get('lang', 'ru')))


@app.route('/logout')
def logout():
    session.pop('user', None)
    session['message'] = 'Logged out'
    return redirect(url_for('home', lang=session.get('lang', 'ru')))


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    lang = request.form.get('lang', 'ru')
    product_id = request.form.get('product_id')
    next_url = request.form.get('next', '')
    product = get_product_by_id(int(product_id)) if product_id else None
    if product:
        cart = session.get('cart', {})
        cart[product_id] = cart.get(product_id, 0) + 1
        session['cart'] = cart
        session['message'] = translations[lang].get('added_to_cart', 'Added')
    if next_url.startswith('/') and not next_url.startswith('//'):
        return redirect(next_url)
    return redirect(url_for('home', lang=lang))


@app.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    product_id = request.form.get('product_id')
    next_url = request.form.get('next', '')
    favorites = session.get('favorites', [])
    if product_id in favorites:
        favorites.remove(product_id)
    else:
        favorites.append(product_id)
    session['favorites'] = favorites
    if next_url.startswith('/') and not next_url.startswith('//'):
        return redirect(next_url)
    return redirect(url_for('home', lang=session.get('lang', 'ru')))


@app.route('/submit_order', methods=['POST'])
def submit_order():
    lang = request.form.get('lang', 'ru')
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    note = request.form.get('note', '').strip()

    if not session.get('cart'):
        session['message'] = translations[lang].get('empty_cart', 'Cart is empty')
        return redirect(url_for('home', lang=lang))

    if not name or not phone:
        session['message'] = translations[lang].get('fill_form', 'Please fill in your name and phone')
        return redirect(url_for('home', lang=lang))

    session['message'] = translations[lang].get('success', 'Order sent successfully')
    session['cart'] = {}
    return redirect(url_for('home', lang=lang))


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('user', {}).get('is_admin'):
        session['message'] = 'Access denied'
        return redirect(url_for('home', lang=session.get('lang', 'ru')))

    lang = (request.args.get('lang') or session.get('lang') or 'ru').lower()
    if lang not in translations:
        lang = 'ru'
    session['lang'] = lang

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            save_product({
                'name_ru': request.form.get('name_ru', ''),
                'name_en': request.form.get('name_en', ''),
                'name_hy': request.form.get('name_hy', ''),
                'category_key': request.form.get('category_key', 'phones'),
                'category_ru': request.form.get('category_ru', 'Телефоны'),
                'category_en': request.form.get('category_en', 'Phones'),
                'category_hy': request.form.get('category_hy', 'Հեռախոսներ'),
                'price_value': request.form.get('price_value', 0),
                'image': request.form.get('image', ''),
                'description_ru': request.form.get('description_ru', ''),
                'description_en': request.form.get('description_en', ''),
                'description_hy': request.form.get('description_hy', ''),
                'featured': request.form.get('featured', 0),
                'stock': request.form.get('stock', 10),
            })
            session['message'] = 'Product added successfully'
        elif action == 'delete':
            delete_product(request.form.get('product_id'))
            session['message'] = 'Product removed'
        elif action == 'clear_visits':
            conn = get_db()
            conn.execute('DELETE FROM visits')
            conn.commit()
            conn.close()
            session['message'] = 'Analytics cleared'
        return redirect(url_for('admin', lang=lang))

    products = get_products_from_db()
    stats = get_analytics()
    return render_template(
        'admin.html', products=products, lang=lang, user=session.get('user'), stats=stats,
        t=translations[lang], message=session.pop('message', None),
        cart_count=sum(session.get('cart', {}).values()),
    )


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
