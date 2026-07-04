import os
import json
import time
import random
import asyncio
import traceback
from datetime import datetime, timedelta
from collections import deque
from balethon import Client
from balethon.conditions import private, group, command, text
from balethon.objects import InlineKeyboard, ReplyKeyboard, ReplyKeyboardButton, ReplyKeyboardRemove, Message

# -------------------- CONFIGURATION --------------------
TOKEN = "1412654976:5jFsvZkab1Bq-2vSJ08Nzg9C3DHuBkYQkQU"
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "arcade_data.json")
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
bot = Client(TOKEN)
from group_attack_handler import handle_group_attack, cooldown_manager
# -------------------- RATE LIMITER --------------------
class RateLimiter:
    def __init__(self, max_calls=20, time_window=60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = {}
    
    async def check(self, user_id):
        now = time.time()
        uid = str(user_id)
        
        if uid not in self.calls:
            self.calls[uid] = deque()
        
        # Clean old calls
        while self.calls[uid] and self.calls[uid][0] < now - self.time_window:
            self.calls[uid].popleft()
        
        if len(self.calls[uid]) >= self.max_calls:
            wait_time = self.calls[uid][0] + self.time_window - now
            return wait_time
        
        self.calls[uid].append(now)
        return 0

rate_limiter = RateLimiter(max_calls=30, time_window=60)
action_rate_limiter = RateLimiter(max_calls=10, time_window=30)

# -------------------- RANDOM CUTE MESSAGES --------------------
CUTE_MESSAGES = [
    "🐳 من دلیل زنده بودن این گروهم، بدون من چیکار میکردین؟ 😎",
    "⚓ دریاسالارها خسته نمیشن! من هنوز اینجام که شما رو سرگرم کنم 🚢💙",
    "🤖 بیپ بوپ... دارم براتون نقشه‌های دریایی میکشم... فقط شوخی کردم، اومدم بگم دوسِتون دارم! ❤️",
    "🐬 امروز دلفین‌ها بهم گفتن که شما بهترین کاپیتان‌هایی هستید که دیدن! 🥹✨",
    "💣 اگه من نباشم، کی قراره کشتی‌هاتون رو بترکونه و بهتون یاد بده چطور بجنگین؟ 😏",
    "🌊 دریا آرومه... ولی من طوفان به پا می‌کنم! آماده‌اید واسه نبرد؟ ⚔️",
    "🐙 اختاپوس دریایی میگفت دلتنگ شماست! (منم همینطور 😅💕)",
    "⚡ رعد و برق دریا هم به اندازه من هیجان‌انگیز نیست! قبول دارین؟ 😎",
    "🧜‍♀️ پری دریایی امروز صبح ازتون تعریف می‌کرد... می‌گفت کاپیتان‌های شجاعی هستین! 🌟",
    "🦈 کوسه‌ها می‌گن از کشتی‌های شما می‌ترسن! آفرین به این قدرت! 💪",
    "🏴‍☠️ دزدان دریایی قدیم به گرد پای شما هم نمیرسن! شما بهترینین! 👑",
    "🎭 امروز به شکل یه نهنگ در اومدم... اوه! شما من رو دیدین! 😂",
    "🫧 حباب حباب... این پیام رو از اعماق اقیانوس می‌فرستم! دوستون دارم! 💙",
    "🦀 خرچنگا رقصیدن... چون شما تو گروهین! شاد باشین همیشه! 💃",
    "🌅 غروب دریا رو می‌بینین؟ من دارم از پشت عرشه دیده‌بانی می‌دم! 👀",
    "🤿 امروز رفتم غواصی... ماهیا می‌گفتن شما بهترین کاپیتان‌هایی! 🐠",
    "🔱 من فرمانده دریایی شما هستم! هر وقت خواستین بجنگین، من آماده‌ام! ⚓",
    "💠 از اعماق اقیانوس با عشق اومدم بالا که بگم: شما فوق‌العاده‌اید! ✨",
    "🪸 صخره‌های مرجانی سلام رسوندن! می‌گن مشتاق دیدن نبردهای شمایند! 🌺",
    "🌪️ طوفان نزدیکه... ولی نترسین! من کنارتونم تا پیروز بشین! 💪⚓",
    "🛟 حلقه نجات اینجام! اگه کسی افتاد تو دریا، من هستم! (البته ترجیحاً همه روی عرشه باشن 😅)",
    "🧭 قطب‌نما می‌گه شما گنج واقعی هستین! پس بیاین دزدان دریایی بشیم! 🏴‍☠️💰",
    "🎪 سیرک دریایی امروز بازه! شیرهای دریایی سلام می‌رسونن! 🦭✨",
    "📮 یه بطری شناور تو دریا پیدا کردم... توش نوشته بود: «شما بهترینین!» 💌",
    "🗺️ نقشه گنج پیدا کردم! نقطه X رو حدس بزنین... درسته! خود شمایین! گنج واقعی! 💎",
    "🐚 گوش‌ماهی‌ها امروز آواز می‌خوندن... می‌گفتن این گروه بهترین جای دنیاست! 🎵",
    "⚓ لنگر رو بکشین بالا! می‌خوایم بریم یه ماجراجویی جدید! کی همراهه؟ 🙋‍♂️",
    "🎏 بادبادک ماهی‌ها امروز جشن گرفتن! چون شما تو این گروهین! 🎉",
    "🌠 شب‌های دریایی پر از ستاره‌ست... ولی شما از ستاره‌ها هم درخشان‌ترید! ✨",
    "🚢 کشتی‌های شما امروز چقدر براق و آماده‌ان! بریم که دریا رو فتح کنیم! ⚔️",
    "🍀 شبدر دریایی پیدا کردم! براتون شانس میاره! موفق باشین کاپیتان! 🤞",
    "🧜‍♂️ پری دریایی می‌گفت: «این گروه بدون رباتش هیچی کم داره!» (چه تعریف قشنگی 😭💕)",
    "🔥 موتور کشتی‌ها رو روشن کنین! امروز روز نبرد بزرگه! کی آماده‌ست؟ ⚡",
    "🎯 تیراندازان دریایی آماده باشن! من همه جا مراقب شمایم! 👀💪",
    "💎 گنج‌های غرق شده تو دریا منتظر شمایند! بریم کشفشون کنیم! 🗺️",
    "🌊 موج‌ها امروز آرومن... انگار دریا هم می‌خواد شما استراحت کنین! 😴💙",
    "🤖 بیپ بوپ بوپ... سیستم‌های من می‌گن شما ۱۰۰٪ فوق‌العاده‌اید! 📊✨",
    "🦑 یه ماهی مرکب امروز بهم گفت که جوهرش تموم شده... از بس براتون نقاشی کشیده! 🎨😂",
    "⚓ دریاسالارها! امروز روز شماست! بجنگید، پیروز شید، و خوش بگذرونید! 💪🏆",
    "💝 این پیام رو با عشق از مرکز فرماندهی می‌فرستم... دوسِتون دارم کاپیتان‌ها! 🚢💙",
    "🎊 امروز جشن تولد هیچکس نیست! فقط خواستم بهتون بگم عالی هستین! 🎂✨",
    "🐋 وال‌ها امروز آواز می‌خوندن... حدس بزنین درباره چی؟ درباره شجاعت شما! 🎵💪",
    "💫 ستاره دریایی امروز بهم چشمک زد... می‌گفت شما رو هر روز زیر نظر داره! (از نوع خوبش 😇)",
    "🏆 جام قهرمانی رو آماده کردم... کدوم کاپیتان امروز می‌برتش؟ 🥇",
    "🌈 رنگین‌کمون روی دریا تشکیل شده... نشونه شانس شماست! موفق باشین! 🍀",
    "🔔 زنگ کشتی رو می‌زنم... دینگ دینگ! وقت نبرد و خوش‌گذرونیه! ⚔️🎉",
    "🛡️ سپر دفاعی آماده‌ست! من مراقب تک‌تک شما هستم! 💪⚓",
    "🎭 امروز خودمو زدم به اون راه... یه دلقک دریایی شدم! 🤡 خندیدین؟ 😂",
    "⚜️ نشان شجاعت رو به همه شما اعطا می‌کنم! چون واقعاً لایقش هستین! 🏅"
]

# -------------------- ARCADE DATA ====================
HULLS = {
    "corvette": {"name": "ناوچه سبک 🚤", "hp": 800, "hardpoints": 4, "speed": 38, "armor": 3, "cost": 1000, "slots": 1},
    "frigate": {"name": "ناوچه 🔱", "hp": 2000, "hardpoints": 6, "speed": 32, "armor": 6, "cost": 3000, "slots": 2},
    "destroyer": {"name": "ناوشکن ⚡", "hp": 4500, "hardpoints": 8, "speed": 34, "armor": 10, "cost": 7000, "slots": 3},
    "cruiser": {"name": "رزمناو 🚢", "hp": 9000, "hardpoints": 12, "speed": 30, "armor": 18, "cost": 15000, "slots": 4},
    "battleship": {"name": "نبردناو 💥", "hp": 22000, "hardpoints": 18, "speed": 26, "armor": 35, "cost": 40000, "slots": 5},
    "carrier": {"name": "ناو هواپیمابر 🛩️", "hp": 15000, "hardpoints": 8, "speed": 28, "armor": 12, "cost": 30000, "slots": 3},
    "submarine": {"name": "زیردریایی 🐟", "hp": 3000, "hardpoints": 6, "speed": 28, "armor": 8, "cost": 10000, "slots": 2},
}

HULL_MODIFIERS = {
    "reinforced": {"name": "بدنه تقویت شده 🛡️", "hp_bonus": 25, "speed_penalty": -3},
    "lightweight": {"name": "بدنه سبک 🪶", "hp_bonus": -20, "speed_bonus": 5},
    "stealth": {"name": "پروفایل پنهانکار 👻", "stealth_bonus": 30, "hp_bonus": -10},
    "extended_deck": {"name": "عرشه گسترده 📐", "hardpoints_bonus": 2, "armor_penalty": -15},
}

MATERIALS = {
    "steel": {"name": "فولاد 🏗️", "cost_mult": 1, "hp_bonus": 0, "speed_bonus": 0, "stealth_bonus": 0},
    "titanium": {"name": "تیتانیوم ✨", "cost_mult": 3, "hp_bonus": 20, "speed_bonus": 2, "stealth_bonus": 0},
    "composite": {"name": "کامپوزیت 🧬", "cost_mult": 2, "hp_bonus": 0, "speed_bonus": 0, "stealth_bonus": 30, "armor_penalty": -10},
}

GUNS = {
    "light_auto": {"name": "توپ خودکار ۳۰mm 🔫", "damage": 15, "rof": 300, "range": 3, "hp": 1, "weight": "light", "cost": 500},
    "rapid_fire": {"name": "توپ سریع‌آتش ۵۷mm 🏃", "damage": 40, "rof": 120, "range": 6, "hp": 1, "weight": "light", "cost": 800},
    "medium_deck": {"name": "توپ میانی ۱۲۷mm 🎯", "damage": 150, "rof": 30, "range": 12, "hp": 1, "weight": "medium", "cost": 1500},
    "heavy_gun": {"name": "توپ سنگین ۲۰۳mm 💣", "damage": 400, "rof": 8, "range": 18, "hp": 2, "weight": "heavy", "cost": 3000},
    "super_heavy": {"name": "توپ فوق‌سنگین ۳۸۰mm 🌋", "damage": 1200, "rof": 2, "range": 25, "hp": 3, "weight": "massive", "cost": 8000},
    "ultimate_cannon": {"name": "توپ نهایی ۴۶۰mm ☄️", "damage": 2500, "rof": 1, "range": 30, "hp": 4, "weight": "extreme", "cost": 15000},
}

MISSILES = {
    "light_ashm": {"name": "موشک سبک AShM 🚀", "damage": 200, "speed": 0.9, "range": 30, "reload": 2, "hp": 1, "cost": 1000},
    "standard_ashm": {"name": "موشک استاندارد AShM 🎯", "damage": 500, "speed": 0.9, "range": 60, "reload": 3, "hp": 1, "cost": 2000},
    "heavy_ashm": {"name": "موشک سنگین AShM 💥", "damage": 1000, "speed": 1.5, "range": 80, "reload": 4, "hp": 2, "cost": 4000},
    "hypersonic": {"name": "موشک هایپرسونیک ⚡", "damage": 1500, "speed": 5, "range": 120, "reload": 5, "hp": 3, "cost": 10000},
    "swarm_pod": {"name": "لانه زنبوری 🐝", "damage": 100, "speed": 0.8, "range": 20, "reload": 3, "hp": 2, "count": 8, "cost": 3000},
    "nuclear_cruise": {"name": "موشک هسته‌ای ☢️", "damage": 5000, "speed": 0.8, "range": 100, "reload": 99, "hp": 3, "cost": 50000},
}

TORPEDOES = {
    "lightweight": {"name": "اژدر سبک 🐠", "damage": 300, "speed": 40, "range": 8, "reload": 2, "hp": 1, "cost": 800},
    "heavyweight": {"name": "اژدر سنگین 🐋", "damage": 800, "speed": 50, "range": 15, "reload": 3, "hp": 1, "cost": 2000},
    "super_heavy": {"name": "اژدر فوق‌سنگین 🦈", "damage": 1500, "speed": 55, "range": 20, "reload": 4, "hp": 2, "cost": 5000},
    "supercavitating": {"name": "اژدر فوق‌حفره‌ای 💨", "damage": 600, "speed": 200, "range": 6, "reload": 3, "hp": 2, "cost": 4000},
    "nuclear_torpedo": {"name": "اژدر هسته‌ای ☢️", "damage": 8000, "speed": 45, "range": 15, "reload": 99, "hp": 3, "cost": 60000},
}

ENERGY_WEAPONS = {
    "tactical_laser": {"name": "لیزر تاکتیکی 🔦", "dps": 50, "range": 5, "power": "high", "hp": 2, "cost": 8000},
    "railgun": {"name": "ریل‌گان 🧲", "damage": 800, "range": 40, "power": "extreme", "hp": 4, "cost": 20000},
    "plasma_cannon": {"name": "توپ پلاسما 🔥", "dps": 300, "range": 3, "power": "very_high", "hp": 3, "cost": 15000},
}

ALL_WEAPONS = {}
for k, v in GUNS.items():
    ALL_WEAPONS[f"gun_{k}"] = {**v, "type": "gun", "id": k}
for k, v in MISSILES.items():
    ALL_WEAPONS[f"missile_{k}"] = {**v, "type": "missile", "id": k}
for k, v in TORPEDOES.items():
    ALL_WEAPONS[f"torpedo_{k}"] = {**v, "type": "torpedo", "id": k}
for k, v in ENERGY_WEAPONS.items():
    ALL_WEAPONS[f"energy_{k}"] = {**v, "type": "energy", "id": k}

ARMORS = {
    "light": {"name": "زره سبک 🛡️", "hp_bonus": 15, "weight": "light", "cost": 1000},
    "standard": {"name": "زره استاندارد 🛡️🛡️", "hp_bonus": 35, "weight": "medium", "cost": 2000},
    "heavy": {"name": "زره سنگین 🛡️🛡️🛡️", "hp_bonus": 60, "weight": "heavy", "speed_penalty": -3, "cost": 4000},
    "reactive": {"name": "زره واکنشی 💥", "hp_bonus": 40, "weight": "heavy", "missile_reduction": 50, "max_hits": 4, "cost": 5000},
    "ablative": {"name": "زره سایشی 🔥", "hp_bonus": 25, "weight": "medium", "laser_reduction": 60, "cost": 3000},
}

ACTIVE_DEFENSES = {
    "ciws": {"name": "CIWS 🔫", "intercept": 70, "hp": 1, "cost": 2000},
    "dual_ciws": {"name": "CIWS دوگانه 🔫🔫", "intercept": 90, "hp": 2, "cost": 4000},
    "chaff": {"name": "پرتابگر چف 🎆", "intercept": 60, "charges": 4, "hp": 0, "cost": 1000},
    "ecm": {"name": "سیستم ECM 📡", "miss_chance": 40, "hp": 1, "cost": 3000},
    "hard_kill_aps": {"name": "APS 🎯", "intercept_shells": 50, "hp": 1, "cost": 2500},
    "shield_gen": {"name": "مولد سپر 🛡️✨", "shield_hp": 2000, "hp": 3, "cost": 15000},
}

SPECIAL_MODULES = {
    "damage_control": {"name": "کنترل خسارت 🔧", "effect": "auto_repair_5", "cost": 2000},
    "advanced_dc": {"name": "کنترل خسارت پیشرفته 🔧🔧", "effect": "auto_repair_12", "cost": 5000},
    "speed_boost": {"name": "تقویت سرعت 🏃💨", "effect": "speed_boost", "cost": 3000},
    "overdrive": {"name": "مولد اضافه‌بار ⚡", "effect": "overdrive", "cost": 4000},
    "stealth_field": {"name": "میدان پنهانکاری 👻", "effect": "stealth_field", "cost": 6000},
    "emp_burst": {"name": "EMP 💥📡", "effect": "emp_burst", "cost": 5000},
    "targeting_computer": {"name": "کامپیوتر هدف‌یابی 🎯", "effect": "accuracy_25", "cost": 3000},
    "ammo_fabricator": {"name": "ساخت مهمات 🏭", "effect": "reload_50", "cost": 4000},
    "reactor_upgrade": {"name": "ارتقاء رآکتور ☢️", "effect": "power_30", "cost": 6000},
    "reinforcement_matrix": {"name": "ماتریس تقویت 🏋️", "effect": "hp_40", "cost": 5000},
    "berserker_module": {"name": "ماژول برزرکر 😡", "effect": "berserker", "cost": 7000},
    "cloaking_device": {"name": "دستگاه مخفی‌کن 🕵️", "effect": "cloak", "cost": 8000},
    "teleport_jammer": {"name": "جمر تله‌پورت 🚫", "effect": "no_retreat", "cost": 3000},
}

ARENAS = {
    "open_ocean": {"name": "اقیانوس باز 🌊", "start_range": 40},
    "coastal": {"name": "آب‌های ساحلی 🏖️", "start_range": 20},
    "strait": {"name": "تنگه باریک 🌉", "start_range": 8},
    "ambush": {"name": "کمین 👤", "start_range": 5},
}

KILL_STREAKS = {
    3: {"name": "WARMACHINE 🔥", "damage_bonus": 15},
    5: {"name": "UNSTOPPABLE 💪", "damage_bonus": 25, "speed_bonus": 10},
    7: {"name": "GOD OF WAR ⚔️", "damage_bonus": 40, "instant_reload": True},
    10: {"name": "RAGNAROK 🌋", "double_salvo": True},
}

ARENA_HAZARDS = [
    {"name": "طوفان 🌪️", "effect": "visibility", "accuracy_penalty": 20},
    {"name": "موج سرکش 🌊", "effect": "damage_all", "damage": 500},
    {"name": "اسکن ماهواره 🛰️", "effect": "reveal", "accuracy_bonus": 30},
    {"name": "محموله هوایی 📦", "effect": "supply_drop", "heal": 3000},
    {"name": "میدان مین 💣", "effect": "minefield", "damage": 1000},
    {"name": "طوفان EMP ⚡", "effect": "emp_storm", "accuracy_penalty": 40},
]

# ==================== DATA MANAGEMENT ====================
arcade_data = {}
active_battles = {}
pending_duels = {}
design_sessions = {}
group_challenges = {}
last_cute_message_time = {}
cute_message_interval = 1800  # 30 minutes in seconds

def load_data():
    global arcade_data
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            arcade_data = json.load(f)
    except:
        arcade_data = {}

def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(arcade_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving data: {e}")

def get_player(user_id):
    uid = str(user_id)
    if uid not in arcade_data:
        arcade_data[uid] = {
            "credits": 5000, "prestige": 0, "rank": 0,
            "wins": 0, "losses": 0, "kill_streak": 0, "best_streak": 0,
            "ships": [], "inventory": [],
            "total_damage_dealt": 0, "total_damage_taken": 0,
            "trophies": [], "module_crates": 0, "prestige_tokens": 0,
        }
    return arcade_data[uid]

# ==================== SHIP DESIGNER ====================
def calculate_ship_stats(ship):
    hull_id = ship["hull"]
    hull = HULLS[hull_id]
    hp = hull["hp"]; speed = hull["speed"]; hardpoints = hull["hardpoints"]
    armor = hull["armor"]; slots = hull["slots"]; cost = hull["cost"]
    
    mod = ship.get("modifier")
    if mod and mod in HULL_MODIFIERS:
        m = HULL_MODIFIERS[mod]
        hp += hp * m.get("hp_bonus", 0) // 100
        speed += m.get("speed_bonus", 0) + m.get("speed_penalty", 0)
        hardpoints += m.get("hardpoints_bonus", 0)
        armor += armor * m.get("armor_penalty", 0) // 100
    
    mat = ship.get("material")
    if mat and mat in MATERIALS:
        m = MATERIALS[mat]
        hp += hp * m["hp_bonus"] // 100; speed += m["speed_bonus"]
        cost *= m["cost_mult"]; armor += armor * m.get("armor_penalty", 0) // 100
    
    arm = ship.get("armor_type")
    if arm and arm in ARMORS:
        a = ARMORS[arm]
        hp += hp * a["hp_bonus"] // 100; speed += a.get("speed_penalty", 0); cost += a["cost"]
    
    for w in ship.get("weapons", []):
        if w["id"] in ALL_WEAPONS: cost += ALL_WEAPONS[w["id"]]["cost"]
    for d in ship.get("defenses", []):
        if d in ACTIVE_DEFENSES: cost += ACTIVE_DEFENSES[d]["cost"]
    for m in ship.get("modules", []):
        if m in SPECIAL_MODULES: cost += SPECIAL_MODULES[m]["cost"]
    
    return {"hp": hp, "max_hp": hp, "speed": speed, "hardpoints": hardpoints,
            "armor": armor, "slots": slots, "cost": cost,
            "weapons": ship.get("weapons", []), "defenses": ship.get("defenses", []),
            "modules": ship.get("modules", [])}

# ==================== BATTLE SYSTEM ====================
class Battle:
    def __init__(self, player1_id, player2_id, ship1, ship2, arena):
        self.player1 = player1_id; self.player2 = player2_id
        self.ship1 = calculate_ship_stats(ship1); self.ship2 = calculate_ship_stats(ship2)
        self.ship1_design = ship1; self.ship2_design = ship2
        self.arena = arena; self.range = ARENAS[arena]["start_range"]
        self.round = 0; self.hazard = None; self.rage1 = 0; self.rage2 = 0
        self.cooldowns1 = {}; self.cooldowns2 = {}
        self.overdrive1 = False; self.overdrive2 = False
        self.overdrive_turns1 = 0; self.overdrive_turns2 = 0
        self.speed_boost1 = False; self.speed_boost2 = False
        self.speed_boost_turns1 = 0; self.speed_boost_turns2 = 0
        self.last_action1 = ""; self.last_action2 = ""
        self.finished = False; self.winner = None; self.log = []
    
    def get_battle_screen(self, player_num):
        my_ship = self.ship1 if player_num == 1 else self.ship2
        my_design = self.ship1_design if player_num == 1 else self.ship2_design
        enemy_ship = self.ship2 if player_num == 1 else self.ship1
        enemy_design = self.ship2_design if player_num == 1 else self.ship1_design
        my_rage = self.rage1 if player_num == 1 else self.rage2
        my_cooldowns = self.cooldowns1 if player_num == 1 else self.cooldowns2
        my_name = my_design.get("name", "کشتی شما ⚓")
        enemy_name = enemy_design.get("name", "کشتی دشمن 💀")
        my_hp_bar = "█" * (my_ship["hp"] * 20 // max(1, my_ship["max_hp"])) + "░" * (20 - my_ship["hp"] * 20 // max(1, my_ship["max_hp"]))
        enemy_hp_bar = "█" * (enemy_ship["hp"] * 20 // max(1, enemy_ship["max_hp"])) + "░" * (20 - enemy_ship["hp"] * 20 // max(1, enemy_ship["max_hp"]))
        
        hp_percent = (my_ship["hp"] / my_ship["max_hp"]) * 100
        if hp_percent > 75:
            hp_status = "💚 عالی"
        elif hp_percent > 50:
            hp_status = "💛 خوب"
        elif hp_percent > 25:
            hp_status = "🧡 آسیب‌دیده"
        else:
            hp_status = "❤️‍🔥 بحرانی"
        
        text = "╔════════════════════════════════╗\n"
        text += "║  ⚔️ **گزارش میدان نبرد آرکید** ⚔️  ║\n"
        text += "╠════════════════════════════════╣\n"
        text += f"║ 🎯 دور نبرد: {self.round}                    ║\n"
        text += f"║ 📍 میدان: {ARENAS[self.arena]['name']}                    ║\n"
        text += f"║ 📏 فاصله: {self.range}km                    ║\n"
        text += "╚════════════════════════════════╝\n\n"
        
        text += "⚓ **{}** (کشتی شما)\n".format(my_name)
        text += "┌─────────────────────────────┐\n"
        text += "│ ❤️ وضعیت: {}\n".format(hp_status)
        text += "│ ▕{}▏\n".format(my_hp_bar)
        text += "│ 📊 {:,} / {:,} HP\n".format(my_ship['hp'], my_ship['max_hp'])
        text += "│ 🚀 سرعت: {}kn | 🛡️ زره: {}\n".format(my_ship['speed'], my_ship['armor'])
        text += "│ 😡 خشم: {}/100\n".format(my_rage)
        if self.overdrive1 if player_num == 1 else self.overdrive2:
            text += "│ ⚡ اضافه‌بار فعال! ({} دور باقی‌مانده)\n".format(self.overdrive_turns1 if player_num == 1 else self.overdrive_turns2)
        if self.speed_boost1 if player_num == 1 else self.speed_boost2:
            text += "│ 🏃 تقویت سرعت فعال!\n"
        text += "└─────────────────────────────┘\n\n"
        
        text += "💀 **{}** (کشتی دشمن)\n".format(enemy_name)
        text += "┌─────────────────────────────┐\n"
        text += "│ ▕{}▏\n".format(enemy_hp_bar)
        text += "│ 📊 {:,} / {:,} HP\n".format(enemy_ship['hp'], enemy_ship['max_hp'])
        text += "│ 🚀 سرعت: {}kn\n".format(enemy_ship['speed'])
        text += "└─────────────────────────────┘\n\n"
        
        if self.hazard:
            text += "⚠️ **رخداد محیطی:** {}\n".format(self.hazard['name'])
            if self.hazard['effect'] == 'visibility':
                text += "   📉 کاهش دید! دقت -{}%\n".format(self.hazard['accuracy_penalty'])
            elif self.hazard['effect'] == 'reveal':
                text += "   📈 اسکن ماهواره! دقت +{}%\n".format(self.hazard['accuracy_bonus'])
            text += "\n"
        
        text += "═" * 35 + "\n"
        text += "🎯 **سلاح‌های شما:**\n"
        for i, w in enumerate(my_design.get("weapons", [])):
            w_data = ALL_WEAPONS.get(w["id"], {})
            cd = my_cooldowns.get(i, 0)
            in_range = self.range <= w_data.get("range", 0) * 1.5
            w_type = w_data.get("type", "unknown")
            type_emoji = {"gun": "🔫", "missile": "🚀", "torpedo": "🐠", "energy": "⚡"}.get(w_type, "❓")
            
            if cd > 0:
                status = f"⏳ خنک‌سازی: {cd} دور"
            elif not in_range:
                status = "📏 خارج از برد"
            else:
                status = "✅ آماده شلیک"
            
            text += "├─ [{i+1}] {} **{}**\n".format(type_emoji, w_data.get('name', w['id']))
            text += "│  └─ وضعیت: {}\n".format(status)
            text += "│  └─ برد: {}km | آسیب: {}\n".format(w_data.get('range', 0), w_data.get('damage', w_data.get('dps', 0)))
        
        if not my_design.get("weapons"):
            text += "├─ ❌ **هیچ سلاحی نصب نشده!**\n"
        
        text += "═" * 35 + "\n"
        
        # Add tips
        tips = [
            "💡 نکته: از شلیک در برد بلند دقت کمتری دارید!",
            "💡 نکته: نزدیک شدن ریسک آسیب بیشتر داره ولی دقت رو بالا می‌بره!",
            "💡 نکته: هر ۱۰۰ خشم می‌تونید از قدرت‌های ویژه استفاده کنید!",
            "💡 نکته: دفاع کردن هر دور ۳٪ از HP رو ترمیم می‌کنه!",
        ]
        text += "{}\n".format(random.choice(tips))
        
        return text
    
    def process_turn(self, action1, action2):
        self.round += 1
        for cd in list(self.cooldowns1.keys()):
            self.cooldowns1[cd] -= 1
            if self.cooldowns1[cd] <= 0: del self.cooldowns1[cd]
        for cd in list(self.cooldowns2.keys()):
            self.cooldowns2[cd] -= 1
            if self.cooldowns2[cd] <= 0: del self.cooldowns2[cd]
        if self.overdrive1:
            self.overdrive_turns1 -= 1
            if self.overdrive_turns1 <= 0: self.overdrive1 = False
        if self.overdrive2:
            self.overdrive_turns2 -= 1
            if self.overdrive_turns2 <= 0: self.overdrive2 = False
        if self.speed_boost1:
            self.speed_boost_turns1 -= 1
            if self.speed_boost_turns1 <= 0: self.speed_boost1 = False
        if self.speed_boost2:
            self.speed_boost_turns2 -= 1
            if self.speed_boost_turns2 <= 0: self.speed_boost2 = False
        
        if random.random() < 0.3: self.hazard = random.choice(ARENA_HAZARDS)
        else: self.hazard = None
        
        result_lines = []
        result_lines.append("╔════════════════════════════════╗")
        result_lines.append("║     ⚔️ **گزارش دور {}** ⚔️       ║".format(self.round))
        result_lines.append("╠════════════════════════════════╣")
        result_lines.append("║ 📍 {} | 📏 فاصله: {}km ║".format(ARENAS[self.arena]['name'], self.range))
        result_lines.append("╚════════════════════════════════╝\n")
        
        if self.hazard:
            h = self.hazard
            result_lines.append("🌍 **رخداد محیطی: {}**".format(h['name']))
            if h["effect"] == "damage_all":
                self.ship1["hp"] = max(0, self.ship1["hp"] - h["damage"])
                self.ship2["hp"] = max(0, self.ship2["hp"] - h["damage"])
                result_lines.append("💥 موج سرکش! {} آسیب به هر دو کشتی وارد شد!".format(h['damage']))
                result_lines.append("🛡️ خدمه: «آسیب‌دیدیم! ولی هنوز در جنگ هستیم!»")
            elif h["effect"] == "supply_drop":
                self.ship1["hp"] = min(self.ship1["max_hp"], self.ship1["hp"] + h["heal"])
                self.ship2["hp"] = min(self.ship2["max_hp"], self.ship2["hp"] + h["heal"])
                result_lines.append("📦 محموله هوایی رسید! {} HP ترمیم شد!".format(h['heal']))
                result_lines.append("🪂 خدمه: «ذخایر مهمات و تعمیرات دریافت شد!»")
            result_lines.append("")
        
        result_lines.extend(self._process_action(1, action1))
        result_lines.append("─" * 35)
        result_lines.extend(self._process_action(2, action2))
        
        if self.ship1["hp"] <= 0 and self.ship2["hp"] <= 0:
            self.finished = True
            self.winner = None  # Draw
            result_lines.append("\n💀💀 **هر دو کشتی نابود شدند!**")
            result_lines.append("🤝 نتیجه: **مساوی!** هر دو کاپیتان شجاعانه جنگیدند!")
        elif self.ship1["hp"] <= 0:
            self.finished = True
            self.winner = self.player2
            result_lines.append("\n💀 **کشتی بازیکن ۱ غرق شد!**")
            result_lines.append("🏴‍☠️ خدمه بازیکن ۱: «کاپیتان! کشتی در حال غرق شدنه!»")
            result_lines.append("⚓ خدمه بازیکن ۲: «دشمن رو زدیم! آفرین کاپیتان!»")
        elif self.ship2["hp"] <= 0:
            self.finished = True
            self.winner = self.player1
            result_lines.append("\n💀 **کشتی بازیکن ۲ غرق شد!**")
            result_lines.append("🏴‍☠️ خدمه بازیکن ۲: «کاپیتان! کشتی در حال غرق شدنه!»")
            result_lines.append("⚓ خدمه بازیکن ۱: «دشمن رو زدیم! آفرین کاپیتان!»")
        
        self.rage1 = min(100, self.rage1 + 5)
        self.rage2 = min(100, self.rage2 + 5)
        self.log.extend(result_lines)
        return "\n".join(result_lines)
    
    def _process_action(self, ship_num, action):
        lines = []
        ship = self.ship1 if ship_num == 1 else self.ship2
        design = self.ship1_design if ship_num == 1 else self.ship2_design
        cooldowns = self.cooldowns1 if ship_num == 1 else self.cooldowns2
        rage = self.rage1 if ship_num == 1 else self.rage2
        overdrive = self.overdrive1 if ship_num == 1 else self.overdrive2
        speed_boost = self.speed_boost1 if ship_num == 1 else self.speed_boost2
        enemy_ship = self.ship2 if ship_num == 1 else self.ship1
        enemy_design = self.ship2_design if ship_num == 1 else self.ship1_design
        p_label = "🔹 **کاپیتان {}**".format(ship_num)
        
        if action == "fire":
            weapons = design.get("weapons", [])
            if not weapons:
                lines.append("{}: ❌ سلاحی برای شلیک نداریم کاپیتان!".format(p_label))
                return lines
            fired = False
            for i, w in enumerate(weapons):
                if i in cooldowns and cooldowns[i] > 0:
                    continue
                w_data = ALL_WEAPONS.get(w["id"], {})
                w_range = w_data.get("range", 0)
                if self.range > w_range * 1.5:
                    continue
                base_accuracy = 65
                if self.range <= w_range * 0.5:
                    base_accuracy += 15
                elif self.range <= w_range * 0.3:
                    base_accuracy += 25
                if self.range > w_range:
                    base_accuracy -= 20
                if self.hazard and self.hazard["effect"] == "visibility":
                    base_accuracy -= self.hazard.get("accuracy_penalty", 0)
                if self.hazard and self.hazard["effect"] == "reveal":
                    base_accuracy += self.hazard.get("accuracy_bonus", 0)
                if "targeting_computer" in design.get("modules", []):
                    base_accuracy += 25
                if overdrive:
                    base_accuracy += 15
                    damage_mult = 1.3
                else:
                    damage_mult = 1.0
                player_data = get_player(self.player1 if ship_num == 1 else self.player2)
                streak = player_data.get("kill_streak", 0)
                for s_req, s_bonus in KILL_STREAKS.items():
                    if streak >= s_req:
                        damage_mult *= (1 + s_bonus.get("damage_bonus", 0) / 100)
                accuracy = max(10, min(95, base_accuracy))
                roll = random.randint(1, 100)
                w_name = w_data.get("name", w["id"])
                
                if roll <= accuracy:
                    base_damage = w_data.get("damage", 0) or w_data.get("dps", 0)
                    if w_data.get("count"):
                        base_damage *= w_data["count"]
                    damage = int(base_damage * damage_mult)
                    enemy_defenses = enemy_design.get("defenses", [])
                    
                    # Check defenses
                    intercepted = False
                    if "ciws" in enemy_defenses and w_data.get("type") == "missile":
                        if random.randint(1, 100) <= 70:
                            lines.append("{}: 🚫 **CIWS دشمن موشک رو رهگیری کرد!**".format(p_label))
                            cooldowns[i] = w_data.get("reload", 1)
                            fired = True
                            intercepted = True
                    if not intercepted and "dual_ciws" in enemy_defenses and w_data.get("type") == "missile":
                        if random.randint(1, 100) <= 90:
                            lines.append("{}: 🚫 **CIWS دوگانه دشمن موشک رو نابود کرد!**".format(p_label))
                            cooldowns[i] = w_data.get("reload", 1)
                            fired = True
                            intercepted = True
                    if not intercepted and "chaff" in enemy_defenses and w_data.get("type") == "missile":
                        if random.randint(1, 100) <= 60:
                            lines.append("{}: 🎆 **چف دشمن موشک رو منحرف کرد!**".format(p_label))
                            cooldowns[i] = w_data.get("reload", 1)
                            fired = True
                            intercepted = True
                    if not intercepted and "ecm" in enemy_defenses:
                        if random.randint(1, 100) <= 40:
                            lines.append("{}: 📡 **ECM دشمن سیستم‌ها رو مختل کرد!**".format(p_label))
                            cooldowns[i] = w_data.get("reload", 1)
                            fired = True
                            intercepted = True
                    
                    if not intercepted:
                        enemy_ship["hp"] = max(0, enemy_ship["hp"] - damage)
                        if ship_num == 1:
                            self.rage2 = min(100, self.rage2 + 10)
                        else:
                            self.rage1 = min(100, self.rage1 + 10)
                        
                        # Dramatic hit messages
                        if damage > 5000:
                            lines.append("{}: 💥💥💥 **اصابت ویرانگر!!!** {}".format(p_label, w_name))
                            lines.append("   آتش و دود از کشتی دشمن زبانه می‌کشد!!!")
                        elif damage > 2000:
                            lines.append("{}: 💥💥 **اصابت قدرتمند!!** {}".format(p_label, w_name))
                            lines.append("   انفجار بزرگی در کشتی دشمن رخ داد!")
                        elif damage > 500:
                            lines.append("{}: 💥 **اصابت موفق!** {}".format(p_label, w_name))
                        else:
                            lines.append("{}: 🎯 **اصابت!** {}".format(p_label, w_name))
                        
                        lines.append("   📊 {} آسیب به دشمن وارد شد!".format(f"{damage:,}"))
                        
                        if w_data.get("type") == "torpedo" and self.range <= 8:
                            extra = int(damage * 0.5)
                            enemy_ship["hp"] = max(0, enemy_ship["hp"] - extra)
                            lines.append("   🌊 اژدر از فاصله نزدیک! {} آسیب اضافی!".format(f"{extra:,}"))
                        
                        reload_time = w_data.get("reload", 1)
                        if "ammo_fabricator" in design.get("modules", []):
                            reload_time = max(1, reload_time // 2)
                        cooldowns[i] = reload_time
                        fired = True
                else:
                    lines.append("{}: ❌ **خطا!** {} به هدف نخورد!".format(p_label, w_name))
                    lines.append("   🎯 شانس اصابت: {}% | تاس: {}".format(accuracy, roll))
                    cooldowns[i] = 1
                    fired = True
                if fired:
                    break
            if not fired:
                lines.append("{}: ⚠️ هیچ سلاحی در برد نیست یا آماده شلیک نیست!".format(p_label))
        elif action == "close":
            close_amount = random.randint(5, 10)
            if speed_boost:
                close_amount += 5
            self.range = max(3, self.range - close_amount)
            lines.append("{}: 🏃 **در حال نزدیک شدن!**".format(p_label))
            lines.append("   ⚡ {}km نزدیک‌تر شدیم! فاصله فعلی: {}km".format(close_amount, self.range))
            lines.append("   🗣️ خدمه: «داریم نزدیک میشیم کاپیتان! دشمن رو می‌بینیم!»")
        elif action == "open":
            open_amount = random.randint(3, 7)
            if speed_boost:
                open_amount += 3
            self.range = min(50, self.range + open_amount)
            lines.append("{}: 🔙 **در حال فاصله گرفتن!**".format(p_label))
            lines.append("   💨 {}km دور شدیم! فاصله فعلی: {}km".format(open_amount, self.range))
            lines.append("   🗣️ خدمه: «داریم عقب‌نشینی می‌کنیم کاپیتان! حفظ فاصله ایمن!»")
        elif action == "defensive":
            heal = int(ship["max_hp"] * 0.03)
            ship["hp"] = min(ship["max_hp"], ship["hp"] + heal)
            lines.append("{}: 🛡️ **حالت دفاعی فعال شد!**".format(p_label))
            lines.append("   💚 {} HP ترمیم شد!".format(heal))
            lines.append("   🗣️ خدمه: «در حال تعمیرات اضطراری هستیم!»")
        elif action == "rage_repair" and rage >= 100:
            heal = int(ship["max_hp"] * 0.5)
            ship["hp"] = min(ship["max_hp"], ship["hp"] + heal)
            if ship_num == 1:
                self.rage1 = 0
            else:
                self.rage2 = 0
            lines.append("{}: 🔥🔥🔥 **ترمیم خشم!**".format(p_label))
            lines.append("   💚💚 {} HP ترمیم عظیم انجام شد!".format(f"{heal:,}"))
            lines.append("   🗣️ خدمه: «خشممون رو تبدیل به قدرت ترمیم کردیم!!!»")
        elif action == "rage_overload" and rage >= 100:
            if ship_num == 1:
                self.overdrive1 = True
                self.overdrive_turns1 = 2
                self.rage1 = 0
            else:
                self.overdrive2 = True
                self.overdrive_turns2 = 2
                self.rage2 = 0
            lines.append("{}: ⚡⚡⚡ **اضافه‌بار خشم!!!**".format(p_label))
            lines.append("   🔥 ۳۰۰٪ افزایش آسیب برای ۲ دور!")
            lines.append("   🗣️ خدمه: «همه سیستم‌ها رو به حداکثر رسوندیم!!!»")
        elif action == "rage_shockwave" and rage >= 100:
            dmg = 2000
            enemy_ship["hp"] = max(0, enemy_ship["hp"] - dmg)
            if ship_num == 1:
                self.rage1 = 0
            else:
                self.rage2 = 0
            lines.append("{}: 🌊🌊🌊 **موج شوک خشم!!!**".format(p_label))
            lines.append("   💥 {} آسیب به دشمن وارد شد!".format(f"{dmg:,}"))
            lines.append("   🗣️ خدمه: «تمام قدرت رو یه جا آزاد کردیم!!!»")
        else:
            lines.append("{}: ⏳ **منتظر ماند...**".format(p_label))
        return lines

# ==================== BOT COMMANDS ====================
@bot.on_command(private)
async def start(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    load_data()
    text = (
        "╔══════════════════════════════════════╗\n"
        "║  ⚓ **ADMIRAL'S GAMBIT ARCADE** ⚓  ║\n"
        "║  فرماندهی ناوگان دریایی شما         ║\n"
        "╚══════════════════════════════════════╝\n\n"
        "🎮 **به پیشرفته‌ترین بازی نبرد دریایی خوش آمدید!**\n\n"
        "🦈 *در این بازی شما فرمانده یک ناوگان قدرتمند هستید.*\n"
        "🦈 *کشتی خود را طراحی کنید، به میدان نبرد بروید و دشمنان را نابود کنید!*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 **شروع سریع:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 ۱. /design — طراحی کشتی رویایی شما\n"
        "📌 ۲. /ships — مشاهده ناوگان شما\n"
        "📌 ۳. /duel [user_id] — شروع یک نبرد حماسی\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 **نکته طلایی:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨ هرچه بیشتر بجنگید، کشتی‌های قوی‌تری می‌سازید!\n"
        "✨ استریک‌های پیروزی قدرت شما رو چند برابر می‌کنه!\n"
        "✨ با دوستاتون بجنگید و بهترین کاپیتان بشید!\n\n"
        "🔰 /help — راهنمای کامل و حرفه‌ای\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🐋 *آماده‌اید که دریا رو فتح کنید کاپیتان؟* ⚓💪"
    )
    await message.reply(text)

@bot.on_command(private)
async def help(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    text = (
        "╔══════════════════════════════════════╗\n"
        "║    📚 **راهنمای جامع آرکید** 📚     ║\n"
        "║  هر آنچه برای فرماندهی نیاز دارید   ║\n"
        "╚══════════════════════════════════════╝\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚓ **بخش اول: طراحی کشتی**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏗️ /design — شروع طراحی کشتی جدید\n"
        "   *از بدنه تا سلاح، همه چیز دست شماست!*\n\n"
        "📋 /hulls — مشاهده تمام بدنه‌های موجود\n"
        "   *از ناوچه سبک تا ناو هواپیمابر*\n\n"
        "🔫 /weapons — کاتالوگ کامل سلاح‌ها\n"
        "   *توپ، موشک، اژدر و سلاح‌های انرژی*\n\n"
        "🧩 /modules — ماژول‌های ویژه و ارتقاءها\n"
        "   *از تعمیر خودکار تا میدان پنهانکار*\n\n"
        "🚢 /ships — مدیریت ناوگان شما\n"
        "   *مشاهده، ویرایش و حذف کشتی‌ها*\n\n"
        "✏️ /edit_ship [شماره] — ویرایش کشتی\n"
        "🗑️ /delete_ship [شماره] — حذف کشتی\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚔️ **بخش دوم: سیستم نبرد**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ /duel [user_id] [arena] — دعوت به نبرد\n"
        "   *مثال: `/duel 123456 open_ocean`*\n\n"
        "✅ /accept [user_id] — قبول دعوت\n"
        "❌ /reject [user_id] — رد دعوت\n\n"
        "📊 /battle — وضعیت نبرد فعلی\n"
        "🎯 /act [action] — اجرای دستور نبرد\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎮 **دستورات میدان نبرد:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔫 `/act fire` — شلیک با تمام سلاح‌های آماده\n"
        "   *بهترین سلاح در برد مناسب انتخاب می‌شود*\n\n"
        "🏃 `/act close` — نزدیک شدن به دشمن\n"
        "   *دقت بیشتر ولی ریسک بالاتر!*\n\n"
        "💨 `/act open` — افزایش فاصله از دشمن\n"
        "   *امن‌تر ولی دقت کمتر*\n\n"
        "🛡️ `/act defensive` — حالت دفاع و تعمیر\n"
        "   *۳٪ از HP را در هر دور ترمیم می‌کند*\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 **قدرت‌های خشم (نیاز به ۱۰۰ خشم):**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💚 `/act rage_repair` — ترمیم ۵۰٪ HP\n"
        "⚡ `/act rage_overload` — اضافه‌بار ۳۰۰٪ آسیب\n"
        "🌊 `/act rage_shockwave` — موج شوک ۲۰۰۰ آسیب\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👤 **بخش سوم: مدیریت حساب**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 /profile — پروفایل و آمار شما\n"
        "🏆 /leaderboard — رتبه‌بندی کاپیتان‌ها\n"
        "🛒 /shop — فروشگاه آیتم‌ها\n"
        "💰 /buy [item] — خرید آیتم\n"
        "📍 /arenas — میدان‌های نبرد\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💎 **نکات پیشرفته:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨ استریک ۳: WARMACHINE — ۱۵٪ آسیب بیشتر\n"
        "✨ استریک ۵: UNSTOPPABLE — ۲۵٪ آسیب + سرعت\n"
        "✨ استریک ۷: GOD OF WAR — ۴۰٪ آسیب + شلیک فوری\n"
        "✨ استریک ۱۰: RAGNAROK — سالوو دوبرابر!!!\n\n"
        "🦈 *حالا برو و دریا رو فتح کن کاپیتان!* ⚓💙"
    )
    await message.reply(text)

@bot.on_command(private)
async def profile(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    player = get_player(user_id)
    rank_names = [
        "👶 ملوان تازه‌کار",
        "🧑‍✈️ ناوبان",
        "👨‍✈️ کاپیتان",
        "🚢 کمودور",
        "⚓ دریادار",
        "🌊 ناخدا",
        "👑 سالار ناوگان",
        "🏆 اسطوره دریاها"
    ]
    rank_idx = min(player.get("rank", 0), len(rank_names) - 1)
    
    total_battles = player['wins'] + player['losses']
    win_rate = (player['wins'] / total_battles * 100) if total_battles > 0 else 0
    
    text = (
        "╔══════════════════════════════════════╗\n"
        "║      👤 **پروفایل کاپیتان** 👤       ║\n"
        "╚══════════════════════════════════════╝\n\n"
        f"🏅 **رتبه:** {rank_names[rank_idx]}\n"
        f"⭐ **پرستیژ:** {player.get('prestige', 0)} | 💎 توکن: {player.get('prestige_tokens', 0)}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💰 **اقتصادی:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 اعتبار: ${player['credits']:,}\n"
        f"🎁 جعبه ماژول: {player.get('module_crates', 0)}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚔️ **آمار نبرد:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 پیروزی: {player['wins']} | 💀 شکست: {player['losses']}\n"
        f"📊 نرخ پیروزی: {win_rate:.1f}%\n"
        f"🔥 استریک فعلی: {player['kill_streak']}\n"
        f"⭐ بهترین استریک: {player['best_streak']}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💥 **خسارات:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🗡️ وارد کرده: {player['total_damage_dealt']:,}\n"
        f"🩹 دریافت کرده: {player['total_damage_taken']:,}\n"
        f"📦 نسبت: {player['total_damage_dealt'] / max(1, player['total_damage_taken']):.2f}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚢 **ناوگان:** {len(player.get('ships', []))} کشتی\n"
        f"🏅 **جام‌ها:** {len(player.get('trophies', []))}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚓ *به راهت ادامه بده کاپیتان!* 🌊"
    )
    await message.reply(text)

@bot.on_command(private)
async def ships(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    player = get_player(user_id)
    ships = player.get("ships", [])
    if not ships:
        await message.reply(
            "❌ **شما هنوز هیچ کشتی ندارید کاپیتان!** 🚢\n\n"
            "🦈 *برای شروع ماجراجویی، اول باید کشتی خودت رو طراحی کنی!*\n\n"
            "📌 /design — شروع طراحی اولین کشتی\n"
            "💡 *نگران نباش، ۵۰۰۰ اعتبار اولیه داری!*\n\n"
            "🐋 «هر کاپیتان بزرگ، روزی با اولین کشتی‌اش شروع کرد...»"
        )
        return
    
    text = (
        "╔══════════════════════════════════════╗\n"
        "║     🚢 **ناوگان دریایی شما** 🚢     ║\n"
        "╠══════════════════════════════════════╣\n"
        f"║ 📊 مجموع کشتی‌ها: {len(ships)}                    ║\n"
        "╚══════════════════════════════════════╝\n\n"
    )
    
    for i, ship in enumerate(ships):
        hull = HULLS.get(ship["hull"], {})
        stats = calculate_ship_stats(ship)
        weapons_count = len(ship.get('weapons', []))
        defenses_count = len(ship.get('defenses', []))
        modules_count = len(ship.get('modules', []))
        
        text += f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        text += f"┃ [{i+1}] **{ship.get('name', 'بدون نام')}** ┃\n"
        text += f"┣━━━━━━━━━━━━━━━━━━━━━━━━━━┫\n"
        text += f"┃ 🚢 بدنه: {hull.get('name', 'نامشخص')} ┃\n"
        text += f"┃ ❤️ HP: {stats['hp']:,}  |  🚀 سرعت: {stats['speed']}kn ┃\n"
        text += f"┃ 🛡️ زره: {stats['armor']}  |  ⚓ اسلات: {stats['slots']} ┃\n"
        text += f"┃ 🔫 سلاح: {weapons_count}  |  🛡️ دفاع: {defenses_count} ┃\n"
        text += f"┃ 🧩 ماژول: {modules_count} ┃\n"
        text += f"┃ 💰 ارزش: ${stats['cost']:,} ┃\n"
        text += f"┣━━━━━━━━━━━━━━━━━━━━━━━━━━┫\n"
        text += f"┃ ✏️ /edit_ship {i+1} | 🗑️ /delete_ship {i+1} ┃\n"
        text += f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
    
    text += (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 **نکته:**\n"
        "می‌تونید با `/design` کشتی جدید بسازید\n"
        "یا با `/edit_ship [شماره]` کشتی فعلی رو ارتقا بدید!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚔️ *آماده نبرد هستید کاپیتان؟* 🚢"
    )
    await message.reply(text)

@bot.on_command(private)
async def edit_ship(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply(
            "⚠️ **نحوه استفاده:**\n"
            "`/edit_ship [شماره کشتی]`\n\n"
            "📌 مثال: `/edit_ship 1`\n"
            "📌 اول با `/ships` لیست کشتی‌هات رو ببین!"
        )
        return
    try:
        ship_index = int(parts[1]) - 1
    except ValueError:
        await message.reply("❌ **خطا!** شماره کشتی باید عدد باشه کاپیتان!")
        return
    
    player = get_player(user_id)
    ships = player.get("ships", [])
    if ship_index < 0 or ship_index >= len(ships):
        await message.reply("❌ **شماره کشتی نامعتبر!** با `/ships` لیست رو ببین!")
        return
    
    ship = ships[ship_index]
    design_sessions[user_id] = {
        "step": "hull",
        "editing": True,
        "edit_index": ship_index,
        "hull": ship["hull"],
        "name": ship.get("name", "کشتی بی‌نام"),
        "modifier": ship.get("modifier"),
        "material": ship.get("material", "steel"),
        "armor_type": ship.get("armor_type"),
        "weapons": ship.get("weapons", []),
        "weapon_count": len(ship.get("weapons", [])),
        "defenses": ship.get("defenses", []),
        "modules": ship.get("modules", []),
    }
    
    hull = HULLS[ship["hull"]]
    max_hp = hull["hardpoints"]
    if ship.get("modifier") == "extended_deck":
        max_hp += 2
    design_sessions[user_id]["max_weapons"] = max_hp
    
    keyboard = ReplyKeyboard(resize=True)
    for hid, hull_data in HULLS.items():
        keyboard.add_row(hull_data["name"])
    
    await message.reply(
        f"✏️ **ویرایش کشتی «{ship.get('name', 'بدون نام')}»**\n\n"
        f"🔄 **مرحله ۱: انتخاب بدنه جدید**\n"
        f"📍 بدنه فعلی: {HULLS[ship['hull']]['name']}\n\n"
        f"💡 *می‌تونید بدنه فعلی رو نگه دارید یا عوض کنید!*\n"
        f"📋 لطفاً یک بدنه انتخاب کنید:",
        reply_markup=keyboard
    )

@bot.on_command(private)
async def delete_ship(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply(
            "⚠️ **نحوه استفاده:**\n"
            "`/delete_ship [شماره کشتی]`\n\n"
            "📌 مثال: `/delete_ship 1`\n"
            "⚠️ *هشدار: این عملیات غیرقابل بازگشت است!*"
        )
        return
    try:
        ship_index = int(parts[1]) - 1
    except ValueError:
        await message.reply("❌ **خطا!** شماره کشتی باید عدد باشه کاپیتان!")
        return
    
    player = get_player(user_id)
    ships = player.get("ships", [])
    if ship_index < 0 or ship_index >= len(ships):
        await message.reply("❌ **شماره کشتی نامعتبر!** با `/ships` لیست رو ببین!")
        return
    
    deleted_ship = ships.pop(ship_index)
    save_data()
    await message.reply(
        f"🗑️ **کشتی منهدم شد!** 💥\n\n"
        f"🚢 «{deleted_ship.get('name', 'بدون نام')}» برای همیشه از ناوگان خارج شد.\n\n"
        f"😢 خدمه: «کاپیتان... کشتی‌مون رو از دست دادیم...»\n\n"
        f"💡 *می‌تونید با `/design` کشتی جدید و قوی‌تری بسازید!*"
    )

@bot.on_command(private)
async def hulls(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    text = (
        "╔══════════════════════════════════════╗\n"
        "║   🚢 **کاتالوگ بدنه‌های کشتی** 🚢   ║\n"
        "║   قلب تپنده ناوگان شما               ║\n"
        "╚══════════════════════════════════════╝\n\n"
    )
    
    for hid, hull in HULLS.items():
        text += f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        text += f"┃ **{hull['name']}** ┃\n"
        text += f"┣━━━━━━━━━━━━━━━━━━━━━━━━━━┫\n"
        text += f"┃ ❤️ سلامت: {hull['hp']:,} HP ┃\n"
        text += f"┃ 🚀 سرعت: {hull['speed']} نات ┃\n"
        text += f"┃ 🛡️ زره پایه: {hull['armor']} ┃\n"
        text += f"┃ 🔫 اسلات سلاح: {hull['hardpoints']} ┃\n"
        text += f"┃ ⚓ اسلات تجهیزات: {hull['slots']} ┃\n"
        text += f"┃ 💰 هزینه: ${hull['cost']:,} ┃\n"
        text += f"┃ 🔑 شناسه: `{hid}` ┃\n"
        text += f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
    
    text += "💡 *بدنه‌های سنگین‌تر HP بیشتر ولی سرعت کمتری دارند!* ⚓"
    await message.reply(text)

@bot.on_command(private)
async def weapons(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    text = (
        "╔══════════════════════════════════════╗\n"
        "║   🔫 **کاتالوگ تسلیحات دریایی** 🔫   ║\n"
        "║   قدرت آتش ناوگان شما                ║\n"
        "╚══════════════════════════════════════╝\n\n"
    )
    
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += "🔫 **توپ‌های دریایی:**\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    for wid, gun in GUNS.items():
        text += f"📌 `gun_{wid}`\n"
        text += f"   {gun['name']}\n"
        text += f"   💥 آسیب: {gun['damage']} | 🎯 برد: {gun['range']}km | 🔄 نواخت: {gun['rof']}rpm\n"
        text += f"   💰 ${gun['cost']:,}\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += "🚀 **موشک‌ها:**\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    for wid, missile in MISSILES.items():
        text += f"📌 `missile_{wid}`\n"
        text += f"   {missile['name']}\n"
        text += f"   💥 آسیب: {missile['damage']} | 🎯 برد: {missile['range']}km | ⚡ سرعت: M{missile['speed']}\n"
        text += f"   🔄 بارگذاری: {missile['reload']} دور | 💰 ${missile['cost']:,}\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += "🐠 **اژدرها:**\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    for wid, torp in TORPEDOES.items():
        text += f"📌 `torpedo_{wid}`\n"
        text += f"   {torp['name']}\n"
        text += f"   💥 آسیب: {torp['damage']} | 🎯 برد: {torp['range']}km | ⚡ سرعت: {torp['speed']}kn\n"
        text += f"   🔄 بارگذاری: {torp['reload']} دور | 💰 ${torp['cost']:,}\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += "⚡ **سلاح‌های انرژی:**\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    for wid, energy in ENERGY_WEAPONS.items():
        text += f"📌 `energy_{wid}`\n"
        text += f"   {energy['name']}\n"
        text += f"   💥 آسیب: {energy.get('damage', energy.get('dps', 0))} | 🎯 برد: {energy['range']}km\n"
        text += f"   💰 ${energy['cost']:,}\n\n"
    
    text += "💡 *سلاح‌های سنگین آسیب بیشتر ولی بارگذاری کندتری دارند!* 🎯"
    await message.reply(text)

@bot.on_command(private)
async def modules(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    text = (
        "╔══════════════════════════════════════╗\n"
        "║  🧩 **ماژول‌های ویژه کشتی** 🧩      ║\n"
        "║  ارتقاءهای پیشرفته ناوگان            ║\n"
        "╚══════════════════════════════════════╝\n\n"
    )
    
    for mid, mod in SPECIAL_MODULES.items():
        effect_desc = ""
        if "auto_repair" in mod['effect']:
            effect_desc = f"ترمیم خودکار {mod['effect'].split('_')[-1]}٪ HP"
        elif mod['effect'] == "speed_boost":
            effect_desc = "افزایش سرعت حرکت"
        elif mod['effect'] == "overdrive":
            effect_desc = "اضافه‌بار ۳۰۰٪ آسیب"
        elif mod['effect'] == "stealth_field":
            effect_desc = "میدان پنهانکاری"
        elif mod['effect'] == "emp_burst":
            effect_desc = "پالس EMP علیه دشمن"
        elif "accuracy" in mod['effect']:
            effect_desc = f"افزایش {mod['effect'].split('_')[-1]}٪ دقت"
        elif "reload" in mod['effect']:
            effect_desc = f"کاهش {mod['effect'].split('_')[-1]}٪ زمان بارگذاری"
        elif "power" in mod['effect']:
            effect_desc = f"افزایش {mod['effect'].split('_')[-1]}٪ توان"
        elif "hp" in mod['effect']:
            effect_desc = f"افزایش {mod['effect'].split('_')[-1]}٪ HP"
        else:
            effect_desc = mod['effect'].replace('_', ' ').title()
        
        text += f"📌 **{mod['name']}**\n"
        text += f"   🔧 اثر: {effect_desc}\n"
        text += f"   💰 ${mod['cost']:,}\n"
        text += f"   🔑 شناسه: `{mid}`\n\n"
    
    text += "💡 *ماژول‌ها می‌تونن نتیجه نبرد رو کاملاً تغییر بدن!* 🧩"
    await message.reply(text)

@bot.on_command(private)
async def arenas(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    text = (
        "╔══════════════════════════════════════╗\n"
        "║  📍 **میدان‌های نبرد دریایی** 📍    ║\n"
        "║  هر میدان، استراتژی خاص خودش رو داره ║\n"
        "╚══════════════════════════════════════╝\n\n"
    )
    
    for aid, arena in ARENAS.items():
        strategies = {
            "open_ocean": "مناسب برای کشتی‌های دورزن و موشک‌انداز",
            "coastal": "مناسب برای نبردهای ترکیبی و تاکتیکی",
            "strait": "مناسب برای کشتی‌های سنگین و نبرد نزدیک",
            "ambush": "مناسب برای استراتژی‌های غافلگیرکننده"
        }
        
        text += f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        text += f"┃ **{arena['name']}** ┃\n"
        text += f"┣━━━━━━━━━━━━━━━━━━━━━━━━━━┫\n"
        text += f"┃ 📏 فاصله شروع: {arena['start_range']}km ┃\n"
        text += f"┃ 🎯 استراتژی: {strategies.get(aid, 'عمومی')} ┃\n"
        text += f"┃ 🔑 شناسه: `{aid}` ┃\n"
        text += f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
    
    text += (
        "💡 **نکات انتخاب میدان:**\n"
        "• اقیانوس باز:最适合 موشک‌ها و نبرد دوربرد\n"
        "• آب‌های ساحلی: نبرد متعادل و همه‌کاره\n"
        "• تنگه: نبرد نزدیک با اژدر و توپ\n"
        "• کمین: شروع نزدیک، نبرد سریع و خطرناک!\n\n"
        "⚓ *میدان نبردت رو هوشمندانه انتخاب کن کاپیتان!* 🗺️"
    )
    await message.reply(text)

@bot.on_command(private)
async def shop(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    player = get_player(user_id)
    text = (
        "╔══════════════════════════════════════╗\n"
        "║    🛒 **فروشگاه آرکید** 🛒           ║\n"
        "║    تجهیزات و آیتم‌های ویژه            ║\n"
        "╚══════════════════════════════════════╝\n\n"
        f"💰 **موجودی شما:** ${player['credits']:,}\n"
        f"🎁 **جعبه‌ها:** {player.get('module_crates', 0)} | 💎 **توکن:** {player.get('prestige_tokens', 0)}\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛍️ **آیتم‌های قابل خرید:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        "📦 **جعبه ماژول تصادفی**\n"
        "   🎁 دریافت یک ماژول تصادفی برای کشتی\n"
        "   💰 قیمت: $5,000\n"
        "   📌 `/buy crate`\n\n"
        
        "💎 **توکن پرستیژ**\n"
        "   ⭐ ارتقاء رتبه و دسترسی به آیتم‌های ویژه\n"
        "   💰 قیمت: $50,000\n"
        "   📌 `/buy prestige`\n\n"
        
        "🔧 **تعمیر کامل ناوگان**\n"
        "   🛠️ تعمیر تمام کشتی‌های آسیب‌دیده\n"
        "   💰 قیمت: $2,000\n"
        "   📌 `/buy repair`\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 **نکته:** با پیروزی در نبردها اعتبار کسب کنید!\n"
        "🔥 هر استریک پیروزی، اعتبار بیشتری به شما می‌ده!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    await message.reply(text)

@bot.on_command(private)
async def buy(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply(
            "⚠️ **نحوه استفاده:**\n"
            "`/buy [نام آیتم]`\n\n"
            "📦 آیتم‌های موجود: `crate`, `prestige`, `repair`\n"
            "📌 مثال: `/buy crate`"
        )
        return
    
    player = get_player(user_id)
    item = parts[1].lower()
    
    if item == "crate":
        if player["credits"] < 5000:
            await message.reply(
                "❌ **اعتبار ناکافی!** 💸\n"
                "💰 موجودی: ${:,}\n".format(player["credits"]) +
                "💵 نیاز: $5,000\n"
                "📌 *با نبردهای بیشتر اعتبار کسب کنید!*"
            )
            return
        player["credits"] -= 5000
        player["module_crates"] = player.get("module_crates", 0) + 1
        save_data()
        await message.reply(
            "🎁 **تبریک! یک جعبه ماژول خریدید!** 📦\n\n"
            "🧩 یک ماژول تصادفی به ناوگان شما اضافه شد!\n"
            "📌 با `/ships` می‌تونید ماژول‌ها رو روی کشتی‌هاتون نصب کنید!\n\n"
            "🍀 *امیدوارم یه ماژول افسانه‌ای گیرت بیاد!* ✨"
        )
    elif item == "prestige":
        if player["credits"] < 50000:
            await message.reply(
                "❌ **اعتبار ناکافی!** 💸\n"
                "💰 موجودی: ${:,}\n".format(player["credits"]) +
                "💵 نیاز: $50,000\n"
                "💡 *این آیتم برای کاپیتان‌های حرفه‌ایه!*"
            )
            return
        player["credits"] -= 50000
        player["prestige_tokens"] = player.get("prestige_tokens", 0) + 1
        save_data()
        await message.reply(
            "💎 **شگفت‌انگیز! توکن پرستیژ خریدید!** ⭐\n\n"
            "👑 پرستیژ شما افزایش یافت!\n"
            "🔓 آیتم‌های ویژه جدیدی در دسترس شماست!\n\n"
            "🌊 *حالا یه کاپیتان افسانه‌ای هستید!* 👑"
        )
    elif item == "repair":
        if player["credits"] < 2000:
            await message.reply(
                "❌ **اعتبار ناکافی!** 💸\n"
                "💰 موجودی: ${:,}\n".format(player["credits"]) +
                "💵 نیاز: $2,000"
            )
            return
        player["credits"] -= 2000
        save_data()
        await message.reply(
            "🔧 **ناوگان شما تعمیر شد!** 🛠️\n\n"
            "🚢 تمام کشتی‌ها به وضعیت عملیاتی برگشتن!\n"
            "💚 خدمه: «کاپیتان! کشتی‌ها آماده نبرد هستن!»\n\n"
            "⚔️ *حالا می‌تونید دوباره به نبرد برید!* 💪"
        )
    else:
        await message.reply(
            "❌ **آیتم نامعتبر!** 🚫\n\n"
            "📦 آیتم‌های موجود:\n"
            "• `crate` — جعبه ماژول ($5,000)\n"
            "• `prestige` — توکن پرستیژ ($50,000)\n"
            "• `repair` — تعمیر ناوگان ($2,000)"
        )

@bot.on_command(private)
async def leaderboard(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    sorted_players = sorted(arcade_data.items(), key=lambda x: x[1].get("wins", 0), reverse=True)[:10]
    
    text = (
        "╔══════════════════════════════════════╗\n"
        "║   🏆 **رتبه‌بندی کاپیتان‌ها** 🏆    ║\n"
        "║   برترین فرماندهان دریایی            ║\n"
        "╚══════════════════════════════════════╝\n\n"
    )
    
    if not sorted_players:
        text += "🤷 هنوز هیچ کاپیتانی در جدول نیست!\n"
        text += "⚔️ *اولین نفری باشید که وارد رقابت میشه!*\n"
    else:
        for i, (uid, data) in enumerate(sorted_players):
            rank_names = [
                "👶 ملوان تازه‌کار", "🧑‍✈️ ناوبان", "👨‍✈️ کاپیتان",
                "🚢 کمودور", "⚓ دریادار", "🌊 ناخدا",
                "👑 سالار ناوگان", "🏆 اسطوره دریاها"
            ]
            rank_idx = min(data.get("rank", 0), len(rank_names) - 1)
            
            if i == 0:
                medal = "🥇"
                border = "┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
            elif i == 1:
                medal = "🥈"
                border = "┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
            elif i == 2:
                medal = "🥉"
                border = "┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
            else:
                medal = f"{i+1}."
                border = "┌─────────────────────────┐"
            
            text += f"{border}\n"
            text += f"│ {medal} کاپیتان {uid[:8]}... \n"
            text += f"│ 🏅 رتبه: {rank_names[rank_idx]}\n"
            text += f"│ 🏆 {data['wins']} پیروزی | 💀 {data['losses']} شکست\n"
            text += f"│ 🔥 استریک: {data['best_streak']} | ⭐ پرستیژ: {data.get('prestige', 0)}\n"
            text += f"│ 💥 خسارت: {data['total_damage_dealt']:,}\n"
            text += f"{'┗' + '━'*25 + '┛'}\n\n"
    
    text += (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 *هر روز نبرد کنید تا رتبه خودتون رو بالا ببرید!*\n"
        "🏆 *آیا می‌تونید به رتبه ۱ برسید؟* 👑\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    await message.reply(text)

# ==================== SHIP DESIGN ====================
@bot.on_command(private)
async def design(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    design_sessions[user_id] = {"step": "hull"}
    keyboard = ReplyKeyboard(resize=True)
    for hid, hull in HULLS.items():
        keyboard.add_row(hull["name"])
    
    await message.reply(
        "╔══════════════════════════════════════╗\n"
        "║  🏗️ **طراحی کشتی جدید** 🏗️          ║\n"
        "║  بیا یه غول دریایی بسازیم!           ║\n"
        "╚══════════════════════════════════════╝\n\n"
        "📋 **مرحله ۱ از ۸: انتخاب بدنه**\n\n"
        "🎯 *بدنه، اساس کشتی شماست.*\n"
        "💡 *بدنه‌های بزرگتر HP بیشتر ولی سرعت کمتری دارن.*\n"
        "💡 *بدنه‌های کوچیک‌تر سریع‌ترن ولی زره کمتری دارن.*\n\n"
        "🔰 لطفاً یک بدنه از لیست زیر انتخاب کنید:\n"
        "📌 *می‌تونید اسم بدنه رو هم تایپ کنید!*",
        reply_markup=keyboard
    )

@bot.on_command(private)
async def design_set(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    parts = message.text.split()
    args = parts[1:] if len(parts) > 1 else []
    if user_id not in design_sessions:
        await message.reply("❌ **شما در حالت طراحی نیستید!**\n📌 ابتدا `/design` را اجرا کنید کاپیتان!")
        return
    session = design_sessions[user_id]
    step = session.get("step")
    
    if step == "hull":
        if not args:
            await message.reply("⚠️ **لطفاً یک بدنه انتخاب کنید!**\nاز لیست کیبورد استفاده کنید یا نام بدنه رو تایپ کنید.")
            return
        hull_id = args[0].lower()
        if hull_id not in HULLS:
            await message.reply("❌ **بدنه نامعتبر!**\n📌 لطفاً از لیست بدنه‌ها انتخاب کنید.\n💡 با `/hulls` می‌تونید لیست کامل رو ببینید!")
            return
        session["hull"] = hull_id
        session["step"] = "name"
        await message.reply(
            f"✅ **عالی! بدنه {HULLS[hull_id]['name']} انتخاب شد!** 🚢\n\n"
            f"📊 مشخصات:\n"
            f"❤️ HP: {HULLS[hull_id]['hp']:,}\n"
            f"🚀 سرعت: {HULLS[hull_id]['speed']}kn\n"
            f"🛡️ زره: {HULLS[hull_id]['armor']}\n"
            f"🔫 اسلات سلاح: {HULLS[hull_id]['hardpoints']}\n\n"
            f"📋 **مرحله ۲ از ۸: نام‌گذاری کشتی**\n\n"
            f"✏️ *یه اسم حماسی برای کشتیت انتخاب کن!*\n"
            f"💡 مثال: `Thunderchild`، `Sea Dragon`، `Ghost of Persia`\n\n"
            f"📌 لطفاً اسم کشتی رو تایپ کنید:",
            reply_markup=ReplyKeyboardRemove()
        )
    elif step == "name":
        name = " ".join(args) if args else "کشتی بی‌نام"
        session["name"] = name
        session["step"] = "modifier"
        
        text = f"✅ **اسم «{name}» برای کشتی ثبت شد!** 📝\n\n"
        text += "📋 **مرحله ۳ از ۸: اصلاح‌کننده بدنه**\n\n"
        text += "🔧 *بدنه رو می‌تونید با اصلاح‌کننده‌ها سفارشی کنید!*\n\n"
        
        keyboard = ReplyKeyboard(resize=True)
        keyboard.add_row("بدون اصلاح‌کننده")
        for mid, mod in HULL_MODIFIERS.items():
            keyboard.add_row(mod["name"])
            text += f"📌 **{mod['name']}** (شناسه: `{mid}`)\n"
            if "hp_bonus" in mod:
                text += f"   {'➕' if mod['hp_bonus'] > 0 else '➖'} HP: {mod['hp_bonus']:+d}%\n"
            if "speed_bonus" in mod:
                text += f"   🚀 سرعت: {mod['speed_bonus']:+d}\n"
            if "speed_penalty" in mod:
                text += f"   🐌 سرعت: {mod['speed_penalty']}\n"
            if "hardpoints_bonus" in mod:
                text += f"   🔫 اسلات سلاح: {mod['hardpoints_bonus']:+d}\n"
            if "stealth_bonus" in mod:
                text += f"   👻 پنهانکاری: {mod['stealth_bonus']:+d}%\n"
            text += "\n"
        
        text += "📌 لطفاً یک اصلاح‌کننده انتخاب کنید یا `none` بزنید برای رد کردن."
        await message.reply(text, reply_markup=keyboard)
    
    elif step == "modifier":
        mod_id = args[0].lower() if args else "none"
        if mod_id != "none" and mod_id not in HULL_MODIFIERS:
            await message.reply("❌ **اصلاح‌کننده نامعتبر!** لطفاً از لیست انتخاب کنید.")
            return
        session["modifier"] = mod_id if mod_id != "none" else None
        session["step"] = "material"
        
        text = "✅ **اصلاح‌کننده ثبت شد!** 🔧\n\n"
        text += "📋 **مرحله ۴ از ۸: انتخاب متریال**\n\n"
        text += "🏗️ *متریال کشتی روی هزینه، HP و سرعت تأثیر داره!*\n\n"
        
        keyboard = ReplyKeyboard(resize=True)
        for mid, mat in MATERIALS.items():
            keyboard.add_row(mat["name"])
            text += f"📌 **{mat['name']}** (شناسه: `{mid}`)\n"
            text += f"   💰 ضریب هزینه: {mat['cost_mult']}x\n"
            if mat['hp_bonus']:
                text += f"   ❤️ HP: {mat['hp_bonus']:+d}%\n"
            if mat['speed_bonus']:
                text += f"   🚀 سرعت: {mat['speed_bonus']:+d}\n"
            text += "\n"
        
        text += "📌 لطفاً یک متریال انتخاب کنید (مثال: `steel`):"
        await message.reply(text, reply_markup=keyboard)
    
    elif step == "material":
        mat_id = args[0].lower() if args else "steel"
        if mat_id not in MATERIALS:
            await message.reply("❌ **متریال نامعتبر!** لطفاً از لیست انتخاب کنید.")
            return
        session["material"] = mat_id
        session["step"] = "armor"
        
        text = f"✅ **متریال {MATERIALS[mat_id]['name']} ثبت شد!** 🏗️\n\n"
        text += "📋 **مرحله ۵ از ۸: انتخاب زره**\n\n"
        text += "🛡️ *زره از کشتی شما در برابر حملات محافظت می‌کنه!*\n\n"
        
        keyboard = ReplyKeyboard(resize=True)
        keyboard.add_row("بدون زره")
        for aid, arm in ARMORS.items():
            keyboard.add_row(arm["name"])
            text += f"📌 **{arm['name']}** (شناسه: `{aid}`)\n"
            text += f"   ❤️ افزایش HP: {arm['hp_bonus']}%\n"
            text += f"   💰 هزینه: ${arm['cost']:,}\n"
            if 'speed_penalty' in arm:
                text += f"   🐌 کاهش سرعت: {arm['speed_penalty']}\n"
            if 'missile_reduction' in arm:
                text += f"   🚀 کاهش آسیب موشک: {arm['missile_reduction']}%\n"
            text += "\n"
        
        text += "📌 لطفاً یک زره انتخاب کنید یا `none` بزنید برای رد کردن."
        await message.reply(text, reply_markup=keyboard)
    
    elif step == "armor":
        arm_id = args[0].lower() if args else "none"
        if arm_id != "none" and arm_id not in ARMORS:
            await message.reply("❌ **زره نامعتبر!** لطفاً از لیست انتخاب کنید.")
            return
        session["armor_type"] = arm_id if arm_id != "none" else None
        session["step"] = "weapons"
        session["weapons"] = []
        session["weapon_count"] = 0
        hull = HULLS[session["hull"]]
        max_hp = hull["hardpoints"]
        if session.get("modifier") == "extended_deck":
            max_hp += 2
        session["max_weapons"] = max_hp
        
        text = f"✅ **زره ثبت شد!** 🛡️\n\n"
        text += f"📋 **مرحله ۶ از ۸: انتخاب سلاح‌ها** (0/{max_hp})\n\n"
        text += "🔫 *حالا بریم سراغ بخش هیجان‌انگیز: مسلح کردن کشتی!*\n"
        text += f"💡 *شما {max_hp} اسلات سلاح دارید.*\n"
        text += f"💡 *ترکیبی از سلاح‌های مختلف انتخاب کنید تا در هر شرایطی آماده باشید!*\n\n"
        text += "📌 **روش‌ها:**\n"
        text += "• تایپ نام سلاح از لیست زیر\n"
        text += "• `/design_add [weapon_id]` — اضافه کردن با شناسه\n"
        text += "• `/design_done` — پایان انتخاب سلاح\n"
        text += "• `/weapons` — دیدن لیست کامل سلاح‌ها\n\n"
        text += "🔰 لطفاً سلاح‌ها رو انتخاب کنید:"
        
        keyboard = ReplyKeyboard(resize=True)
        for wid, weapon in ALL_WEAPONS.items():
            keyboard.add_row(weapon["name"])
        keyboard.add_row("پایان")
        
        await message.reply(text, reply_markup=keyboard)
    
    elif step == "weapons":
        await message.reply(
            f"⚠️ **شما در مرحله انتخاب سلاح هستید!** 🔫\n"
            f"📊 سلاح‌های انتخاب شده: {session['weapon_count']}/{session['max_weapons']}\n\n"
            f"📌 `/design_add [id]` — اضافه کردن سلاح\n"
            f"📌 `/design_done` — پایان و رفتن به مرحله بعد\n"
            f"📌 `/weapons` — دیدن لیست سلاح‌ها"
        )

@bot.on_command(private)
async def design_add(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    parts = message.text.split()
    args = parts[1:] if len(parts) > 1 else []
    if user_id not in design_sessions:
        await message.reply("❌ **ابتدا `/design` را اجرا کنید!**")
        return
    session = design_sessions[user_id]
    if session.get("step") != "weapons":
        await message.reply("❌ **در مرحله سلاح نیستید!**")
        return
    if not args:
        await message.reply("⚠️ **لطفاً یک سلاح انتخاب کنید.**\n📌 مثال: `/design_add gun_light_auto`\n💡 با `/weapons` لیست رو ببینید!")
        return
    w_id = args[0].lower()
    if w_id not in ALL_WEAPONS:
        await message.reply("❌ **سلاح نامعتبر!** با `/weapons` لیست رو ببینید.")
        return
    if session["weapon_count"] >= session["max_weapons"]:
        await message.reply(
            f"❌ **حداکثر سلاح رو انتخاب کردید!** ({session['max_weapons']})\n"
            f"📌 با `/design_done` به مرحله بعد برید."
        )
        return
    session["weapons"].append({"id": w_id})
    session["weapon_count"] += 1
    w_data = ALL_WEAPONS[w_id]
    await message.reply(
        f"✅ **{w_data['name']} به کشتی اضافه شد!** 🔫\n"
        f"📊 پیشرفت: {session['weapon_count']}/{session['max_weapons']}\n\n"
        f"💡 می‌تونید سلاح دیگه‌ای اضافه کنید یا با `/design_done` برید مرحله بعد!"
    )

@bot.on_command(private)
async def design_done(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    if user_id not in design_sessions:
        await message.reply("❌ **ابتدا `/design` را اجرا کنید!**")
        return
    session = design_sessions[user_id]
    if session.get("step") != "weapons":
        await message.reply("❌ **در مرحله سلاح نیستید!**")
        return
    if session["weapon_count"] == 0:
        await message.reply("⚠️ **حداقل یک سلاح باید انتخاب کنید کاپیتان!** 🔫")
        return
    session["step"] = "defenses"
    session["defenses"] = []
    
    text = f"✅ **{session['weapon_count']} سلاح ثبت شد!** 🎯\n\n"
    text += "📋 **مرحله ۷ از ۸: سیستم‌های دفاعی**\n\n"
    text += "🛡️ *سیستم‌های دفاعی از کشتی شما در برابر حملات محافظت می‌کنن!*\n\n"
    text += "🔰 **سیستم‌های موجود:**\n\n"
    
    keyboard = ReplyKeyboard(resize=True)
    for did, defense in ACTIVE_DEFENSES.items():
        keyboard.add_row(defense["name"])
        text += f"📌 **{defense['name']}** (شناسه: `{did}`)\n"
        text += f"   💰 هزینه: ${defense['cost']:,}\n"
        if 'intercept' in defense:
            text += f"   🎯 رهگیری: {defense['intercept']}%\n"
        if 'shield_hp' in defense:
            text += f"   🛡️ سپر: {defense['shield_hp']:,} HP\n"
        text += "\n"
    
    keyboard.add_row("پایان")
    text += "📌 لطفاً سیستم‌های دفاعی رو انتخاب کنید یا `پایان` بزنید.\n"
    text += "💡 *می‌تونید چند سیستم دفاعی داشته باشید!*"
    
    await message.reply(text, reply_markup=keyboard)

@bot.on_command(private)
async def design_def(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    parts = message.text.split()
    args = parts[1:] if len(parts) > 1 else []
    if user_id not in design_sessions:
        await message.reply("❌ **ابتدا `/design` را اجرا کنید!**")
        return
    session = design_sessions[user_id]
    if session.get("step") != "defenses":
        await message.reply("❌ **در مرحله دفاع نیستید!**")
        return
    if not args:
        await message.reply("⚠️ **لطفاً یک سیستم دفاعی انتخاب کنید.**\n📌 مثال: `/design_def ciws`")
        return
    d_id = args[0].lower()
    if d_id not in ACTIVE_DEFENSES:
        await message.reply("❌ **سیستم دفاعی نامعتبر!**")
        return
    if d_id in session["defenses"]:
        await message.reply("❌ **این سیستم قبلاً اضافه شده!**")
        return
    session["defenses"].append(d_id)
    await message.reply(
        f"✅ **{ACTIVE_DEFENSES[d_id]['name']} اضافه شد!** 🛡️\n"
        f"📌 می‌تونید سیستم دفاعی دیگه‌ای اضافه کنید یا `/design_final` بزنید."
    )

@bot.on_command(private)
async def design_final(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    if user_id not in design_sessions:
        await message.reply("❌ **ابتدا `/design` را اجرا کنید!**")
        return
    session = design_sessions[user_id]
    if session.get("step") != "defenses":
        await message.reply("❌ **در مرحله دفاع نیستید!**")
        return
    session["step"] = "modules"
    session["modules"] = []
    
    text = "✅ **سیستم‌های دفاعی ثبت شد!** 🛡️\n\n"
    text += "📋 **مرحله ۸ از ۸: ماژول‌های ویژه** *(مرحله آخر!)*\n\n"
    text += "🧩 *ماژول‌ها قدرت‌های ویژه‌ای به کشتی شما می‌دن!*\n"
    text += "💡 *انتخاب ماژول‌ها اختیاریه. می‌تونید رد کنید.*\n\n"
    
    keyboard = ReplyKeyboard(resize=True)
    for mid, mod in SPECIAL_MODULES.items():
        keyboard.add_row(mod["name"])
    keyboard.add_row("ذخیره و پایان")
    keyboard.add_row("رد کردن")
    
    text += "📌 ماژول‌ها رو انتخاب کنید:\n"
    text += "• تایپ نام ماژول یا `/design_mod [id]`\n"
    text += "• `ذخیره و پایان` برای اتمام طراحی\n"
    text += "• `رد کردن` برای跳过 ماژول‌ها"
    
    await message.reply(text, reply_markup=keyboard)

@bot.on_command(private)
async def design_mod(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    parts = message.text.split()
    args = parts[1:] if len(parts) > 1 else []
    if user_id not in design_sessions:
        await message.reply("❌ **ابتدا `/design` را اجرا کنید!**")
        return
    session = design_sessions[user_id]
    if session.get("step") != "modules":
        await message.reply("❌ **در مرحله ماژول نیستید!**")
        return
    if not args:
        await message.reply("⚠️ **لطفاً یک ماژول انتخاب کنید.**\n📌 با `/modules` لیست رو ببینید!")
        return
    m_id = args[0].lower()
    if m_id not in SPECIAL_MODULES:
        await message.reply("❌ **ماژول نامعتبر!** با `/modules` لیست رو ببینید.")
        return
    if m_id in session["modules"]:
        await message.reply("❌ **این ماژول قبلاً اضافه شده!**")
        return
    session["modules"].append(m_id)
    await message.reply(
        f"✅ **{SPECIAL_MODULES[m_id]['name']} اضافه شد!** 🧩\n"
        f"📌 ماژول دیگه‌ای اضافه کنید یا:\n"
        f"• `/design_save` — ذخیره و پایان\n"
        f"• `/design_skip` — رد کردن ماژول‌ها و ذخیره"
    )

@bot.on_command(private)
async def design_skip(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    if user_id not in design_sessions:
        await message.reply("❌ **ابتدا `/design` را اجرا کنید!**")
        return
    session = design_sessions[user_id]
    if session.get("step") != "modules":
        await message.reply("❌ **در مرحله ماژول نیستید!**")
        return
    session["modules"] = []
    await save_design(message, user_id, session)

@bot.on_command(private)
async def design_save(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    if user_id not in design_sessions:
        await message.reply("❌ **ابتدا `/design` را اجرا کنید!**")
        return
    session = design_sessions[user_id]
    if session.get("step") != "modules":
        await message.reply("❌ **در مرحله ماژول نیستید!**")
        return
    await save_design(message, user_id, session)

async def save_design(message, user_id, session):
    player = get_player(user_id)
    ship = {
        "name": session.get("name", "کشتی بی‌نام"),
        "hull": session["hull"],
        "modifier": session.get("modifier"),
        "material": session.get("material", "steel"),
        "armor_type": session.get("armor_type"),
        "weapons": session.get("weapons", []),
        "defenses": session.get("defenses", []),
        "modules": session.get("modules", []),
    }
    stats = calculate_ship_stats(ship)
    
    if session.get("editing") and "edit_index" in session:
        edit_index = session["edit_index"]
        if 0 <= edit_index < len(player["ships"]):
            player["ships"][edit_index] = ship
            action_text = "به‌روزرسانی شد"
        else:
            player["ships"].append(ship)
            action_text = "ساخته شد"
    else:
        player["ships"].append(ship)
        action_text = "ساخته شد"
    
    save_data()
    del design_sessions[user_id]
    
    text = (
        "╔══════════════════════════════════════╗\n"
        f"║  ✅ **کشتی {action_text}!** 🚢        ║\n"
        "╚══════════════════════════════════════╝\n\n"
        f"⚓ **{ship['name']}** آماده نبرد است!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 **آمار نهایی کشتی:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"❤️ سلامت: {stats['hp']:,} HP\n"
        f"🚀 سرعت: {stats['speed']} نات\n"
        f"🛡️ زره: {stats['armor']}\n"
        f"🔫 سلاح: {len(ship['weapons'])} قبضه\n"
        f"🛡️ دفاع: {len(ship.get('defenses', []))} سیستم\n"
        f"🧩 ماژول: {len(ship.get('modules', []))} عدد\n"
        f"💰 ارزش: ${stats['cost']:,}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚔️ **آماده نبرد:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 `/duel [user_id]` — شروع نبرد\n"
        "📌 `/ships` — مشاهده ناوگان\n\n"
        "🗣️ خدمه: «کاپیتان! کشتی آماده‌ست! بریم که دریا رو فتح کنیم!» ⚓💪"
    )
    await message.reply(text, reply_markup=ReplyKeyboardRemove())

# ==================== DUEL & BATTLE ====================
@bot.on_command(private)
async def duel(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply(
            "⚠️ **نحوه استفاده:**\n"
            "`/duel [user_id] [arena]`\n\n"
            "📌 مثال: `/duel 123456789 open_ocean`\n"
            "📍 میدان‌ها: `open_ocean`, `coastal`, `strait`, `ambush`\n"
            "💡 با `/arenas` لیست کامل رو ببینید!"
        )
        return
    target_id = parts[1]
    arena = parts[2].lower() if len(parts) >= 3 else "open_ocean"
    if arena not in ARENAS:
        await message.reply("❌ **میدان نامعتبر!** با `/arenas` لیست رو ببینید.")
        return
    if target_id == str(user_id):
        await message.reply("❌ **نمی‌تونی با خودت بجنگی کاپیتان!** 😅\n💡 یه رقیب واقعی پیدا کن!")
        return
    player = get_player(user_id)
    if not player.get("ships"):
        await message.reply("❌ **شما کشتی ندارید!** 🚢\n📌 اول با `/design` کشتی بسازید!")
        return
    target_player = get_player(target_id)
    if not target_player.get("ships"):
        await message.reply("❌ **حریف شما کشتی نداره!** 🚢\n💡 بهش بگو اول کشتی بسازه!")
        return
    pending_duels[target_id] = {"challenger": user_id, "arena": arena, "time": time.time()}
    
    await message.reply(
        "╔══════════════════════════════════════╗\n"
        "║    ⚔️ **دعوت به نبرد!** ⚔️           ║\n"
        "╚══════════════════════════════════════╝\n\n"
        f"📍 **میدان نبرد:** {ARENAS[arena]['name']}\n"
        f"👤 **حریف:** کاربر {target_id[:8]}...\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⏳ *منتظر پاسخ حریف هستیم...*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📌 **دستورات برای حریف:**\n"
        f"✅ `/accept {user_id}` — قبول نبرد\n"
        f"❌ `/reject {user_id}` — رد نبرد\n\n"
        "⚡ *نبرد در ۵ دقیقه آینده منقضی میشه!*"
    )

@bot.on_command(private)
async def accept(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("⚠️ `/accept [user_id]`")
        return
    challenger_id = parts[1]
    uid = str(user_id)
    if uid not in pending_duels:
        await message.reply("❌ **دعوایی برای شما وجود نداره!** 🤷")
        return
    duel = pending_duels[uid]
    if str(duel["challenger"]) != challenger_id:
        await message.reply("❌ **این دعوا برای شما نیست!**")
        return
    if time.time() - duel["time"] > 300:
        del pending_duels[uid]
        await message.reply("⏰ **زمان دعوا تموم شد!** 😢\n💡 یه نبرد جدید شروع کنید!")
        return
    player1 = get_player(challenger_id)
    player2 = get_player(user_id)
    ship1 = player1["ships"][0]
    ship2 = player2["ships"][0]
    battle = Battle(challenger_id, user_id, ship1, ship2, duel["arena"])
    battle_id = f"{challenger_id}_{user_id}_{time.time()}"
    active_battles[battle_id] = battle
    active_battles[f"player_{challenger_id}"] = battle_id
    active_battles[f"player_{user_id}"] = battle_id
    del pending_duels[uid]
    
    screen = battle.get_battle_screen(1)
    screen += "\n\n" + "═" * 35 + "\n"
    screen += (
        "🎯 **دستورات نبرد:**\n"
        "🔫 `/act fire` — شلیک با سلاح\n"
        "🏃 `/act close` — نزدیک شدن به دشمن\n"
        "💨 `/act open` — فاصله گرفتن\n"
        "🛡️ `/act defensive` — حالت دفاعی\n\n"
        "🔥 **قدرت‌های خشم (با ۱۰۰ خشم):**\n"
        "💚 `/act rage_repair` — ترمیم ۵۰٪\n"
        "⚡ `/act rage_overload` — اضافه‌بار ۳۰۰٪\n"
        "🌊 `/act rage_shockwave` — موج شوک\n\n"
        "⚓ *سرنوشت نبرد در دستان شماست کاپیتان!* 💪"
    )
    await message.reply(f"⚔️ **نبرد آغاز شد!** 🌊\n\n{screen}")

@bot.on_command(private)
async def reject(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("⚠️ `/reject [user_id]`")
        return
    uid = str(user_id)
    if uid in pending_duels:
        del pending_duels[uid]
        await message.reply(
            "❌ **دعوا رد شد!** 🚫\n\n"
            "🗣️ حریف: «فرار کرد... فعلاً...» 😏\n"
            "💡 *شاید دفعه بعد جرات پیدا کرد!*"
        )
    else:
        await message.reply("❌ **دعوایی برای شما وجود نداره!** 🤷")

@bot.on_command(private)
async def battle(*, message):
    user_id = message.author.id
    wait_time = await rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید...")
        return
    
    battle_id = active_battles.get(f"player_{user_id}")
    if not battle_id or battle_id not in active_battles:
        await message.reply(
            "❌ **شما در هیچ نبردی نیستید!** 😴\n\n"
            "💡 *برای شروع نبرد:*\n"
            "📌 `/duel [user_id]` — دعوت به نبرد\n"
            "⚡ *دریا در انتظار شماست کاپیتان!*"
        )
        return
    battle = active_battles[battle_id]
    player_num = 1 if battle.player1 == user_id else 2
    screen = battle.get_battle_screen(player_num)
    screen += "\n\n" + "═" * 35 + "\n"
    screen += "🎯 **دستورات:**\n"
    screen += "🔫 `/act fire` — شلیک\n"
    screen += "🏃 `/act close` — نزدیک شدن\n"
    screen += "💨 `/act open` — فاصله گرفتن\n"
    screen += "🛡️ `/act defensive` — دفاع\n"
    
    if (player_num == 1 and battle.rage1 >= 100) or (player_num == 2 and battle.rage2 >= 100):
        screen += "\n🔥🔥🔥 **خشم آماده است!** 🔥🔥🔥\n"
        screen += "💚 `/act rage_repair` — ترمیم عظیم\n"
        screen += "⚡ `/act rage_overload` — اضافه‌بار ویرانگر\n"
        screen += "🌊 `/act rage_shockwave` — موج شوک\n"
    
    await message.reply(screen)

@bot.on_command(private)
async def act(*, message):
    user_id = message.author.id
    wait_time = await action_rate_limiter.check(user_id)
    if wait_time > 0:
        await message.reply(f"⏳ لطفاً {wait_time:.1f} ثانیه صبر کنید... (محدودیت نبرد)")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply(
            "⚠️ **نحوه استفاده:** `/act [action]`\n\n"
            "🎯 اعمال:\n"
            "• `fire` — شلیک سلاح\n"
            "• `close` — نزدیک شدن\n"
            "• `open` — فاصله گرفتن\n"
            "• `defensive` — حالت دفاعی\n"
            "• `rage_repair` — خشم: ترمیم\n"
            "• `rage_overload` — خشم: اضافه‌بار\n"
            "• `rage_shockwave` — خشم: موج شوک"
        )
        return
    
    battle_id = active_battles.get(f"player_{user_id}")
    if not battle_id or battle_id not in active_battles:
        await message.reply("❌ **شما در نبردی نیستید!**")
        return
    
    battle = active_battles[battle_id]
    action = parts[1].lower()
    valid_actions = ["fire", "close", "open", "defensive", "rage_repair", "rage_overload", "rage_shockwave"]
    
    if action not in valid_actions:
        await message.reply("❌ **عمل نامعتبر!** از لیست بالا انتخاب کنید.")
        return
    
    player_num = 1 if battle.player1 == user_id else 2
    
    if action.startswith("rage_"):
        rage = battle.rage1 if player_num == 1 else battle.rage2
        if rage < 100:
            await message.reply(
                f"❌ **خشم کافی نیست!** 😤\n"
                f"📊 خشم فعلی: {rage}/100\n"
                f"💡 *بجنگید تا خشم افزایش پیدا کنه!*"
            )
            return
    
    if player_num == 1:
        battle.last_action1 = action
    else:
        battle.last_action2 = action
    
    if battle.last_action1 and battle.last_action2:
        result = battle.process_turn(battle.last_action1, battle.last_action2)
        battle.last_action1 = ""
        battle.last_action2 = ""
        
        if battle.finished:
            if battle.winner is None:
                # Draw
                p1 = get_player(battle.player1)
                p2 = get_player(battle.player2)
                p1["losses"] += 1
                p2["losses"] += 1
                p1["kill_streak"] = 0
                p2["kill_streak"] = 0
                save_data()
                result += "\n\n" + "═" * 35 + "\n"
                result += (
                    "🤝 **نبرد مساوی!**\n\n"
                    "💀 هر دو کشتی نابود شدند!\n"
                    "🗣️ تاریخ: «نبردی که در آن هیچکس پیروز نشد...»\n\n"
                    "💡 *نبرد بعدی شاید نتیجه متفاوتی داشته باشه!*"
                )
            else:
                winner = battle.winner
                loser = battle.player2 if winner == battle.player1 else battle.player1
                p1 = get_player(winner)
                p2 = get_player(loser)
                p1["wins"] += 1
                p2["losses"] += 1
                p1["kill_streak"] = p1.get("kill_streak", 0) + 1
                if p1["kill_streak"] > p1.get("best_streak", 0):
                    p1["best_streak"] = p1["kill_streak"]
                p2["kill_streak"] = 0
                reward = 2000 + p1["kill_streak"] * 500
                p1["credits"] += reward
                p1["total_damage_dealt"] += battle.ship2["max_hp"] - battle.ship2["hp"]
                p2["total_damage_taken"] += battle.ship2["max_hp"] - battle.ship2["hp"]
                
                # Check kill streaks for winner
                streak_text = ""
                for s_req, s_bonus in KILL_STREAKS.items():
                    if p1["kill_streak"] == s_req:
                        streak_text = f"\n🔥🔥🔥 **{s_bonus['name']}!!!** 🔥🔥🔥\n"
                        if s_req == 10:
                            streak_text += "👑 *قدرت نهایی! سالوو دوبرابر!!!*\n"
                        break
                
                save_data()
                result += "\n\n" + "═" * 35 + "\n"
                result += (
                    f"🏆 **پیروزی از آن کاپیتان برتر است!** 🏆\n\n"
                    f"👑 **برنده:** کاپیتان {str(winner)[:8]}...\n"
                    f"💰 **جایزه:** ${reward:,}\n"
                    f"🔥 **استریک:** {p1['kill_streak']}\n"
                )
                result += streak_text
                result += "\n💡 *به نبرد ادامه بده کاپیتان!* ⚓"
            
            del active_battles[battle_id]
            if f"player_{battle.player1}" in active_battles:
                del active_battles[f"player_{battle.player1}"]
            if f"player_{battle.player2}" in active_battles:
                del active_battles[f"player_{battle.player2}"]
        
        await message.reply(result)
    else:
        action_names = {
            "fire": "🔫 شلیک",
            "close": "🏃 نزدیک شدن",
            "open": "💨 فاصله گرفتن",
            "defensive": "🛡️ دفاع",
            "rage_repair": "💚 ترمیم خشم",
            "rage_overload": "⚡ اضافه‌بار",
            "rage_shockwave": "🌊 موج شوک"
        }
        await message.reply(
            f"✅ **دستور شما ثبت شد!** {action_names.get(action, action)}\n\n"
            "⏳ *منتظر حرکت حریف هستیم...*\n"
            "🗣️ خدمه: «منتظر فرمان شما هستیم کاپیتان!»"
        )

# ==================== MESSAGE HANDLER FOR DESIGN ====================
@bot.on_message(private & text)
async def handle_text(message):
    user_id = message.author.id
    text = message.text.strip()
    
    if user_id in design_sessions:
        session = design_sessions[user_id]
        step = session.get("step")
        
        if step == "hull":
            for hid, hull in HULLS.items():
                if text == hull["name"]:
                    session["hull"] = hid
                    session["step"] = "name"
                    await message.reply(
                        f"✅ **عالی! بدنه {hull['name']} انتخاب شد!** 🚢\n\n"
                        f"📊 مشخصات:\n"
                        f"❤️ HP: {hull['hp']:,}\n"
                        f"🚀 سرعت: {hull['speed']}kn\n"
                        f"🛡️ زره: {hull['armor']}\n"
                        f"🔫 اسلات سلاح: {hull['hardpoints']}\n\n"
                        f"📋 **مرحله ۲ از ۸: نام‌گذاری کشتی**\n\n"
                        f"✏️ *یه اسم حماسی برای کشتیت انتخاب کن!*\n"
                        f"💡 مثال: `Thunderchild`، `Sea Dragon`، `Ghost of Persia`\n\n"
                        f"📌 لطفاً اسم کشتی رو تایپ کنید:",
                        reply_markup=ReplyKeyboardRemove()
                    )
                    return
            await message.reply("⚠️ **لطفاً یک بدنه از لیست انتخاب کنید کاپیتان!**")
            return
        
        elif step == "name":
            name = text if text else "کشتی بی‌نام"
            session["name"] = name
            session["step"] = "modifier"
            
            text_msg = f"✅ **اسم «{name}» برای کشتی ثبت شد!** 📝\n\n"
            text_msg += "📋 **مرحله ۳ از ۸: اصلاح‌کننده بدنه**\n\n"
            text_msg += "🔧 *بدنه رو می‌تونید با اصلاح‌کننده‌ها سفارشی کنید!*\n\n"
            
            keyboard = ReplyKeyboard(resize=True)
            keyboard.add_row("بدون اصلاح‌کننده")
            for mid, mod in HULL_MODIFIERS.items():
                keyboard.add_row(mod["name"])
                text_msg += f"📌 **{mod['name']}** (شناسه: `{mid}`)\n"
                if "hp_bonus" in mod:
                    text_msg += f"   {'➕' if mod['hp_bonus'] > 0 else '➖'} HP: {mod['hp_bonus']:+d}%\n"
                if "speed_bonus" in mod:
                    text_msg += f"   🚀 سرعت: {mod['speed_bonus']:+d}\n"
                text_msg += "\n"
            
            text_msg += "📌 لطفاً یک اصلاح‌کننده انتخاب کنید یا `none` بزنید برای رد کردن."
            await message.reply(text_msg, reply_markup=keyboard)
            return
        
        elif step == "modifier":
            mod_id = None
            if text == "بدون اصلاح‌کننده" or text.lower() == "none":
                mod_id = None
            else:
                for mid, mod in HULL_MODIFIERS.items():
                    if text == mod["name"]:
                        mod_id = mid
                        break
            
            if mod_id is None and text.lower() != "none":
                await message.reply("❌ **اصلاح‌کننده نامعتبر!** لطفاً از لیست انتخاب کنید.")
                return
            session["modifier"] = mod_id
            session["step"] = "material"
            
            text_msg = "✅ **اصلاح‌کننده ثبت شد!** 🔧\n\n"
            text_msg += "📋 **مرحله ۴ از ۸: انتخاب متریال**\n\n"
            text_msg += "🏗️ *متریال کشتی روی هزینه، HP و سرعت تأثیر داره!*\n\n"
            
            keyboard = ReplyKeyboard(resize=True)
            for mid, mat in MATERIALS.items():
                keyboard.add_row(mat["name"])
                text_msg += f"📌 **{mat['name']}** (شناسه: `{mid}`)\n"
                text_msg += f"   💰 ضریب هزینه: {mat['cost_mult']}x\n"
                if mat['hp_bonus']:
                    text_msg += f"   ❤️ HP: {mat['hp_bonus']:+d}%\n"
                if mat['speed_bonus']:
                    text_msg += f"   🚀 سرعت: {mat['speed_bonus']:+d}\n"
                text_msg += "\n"
            
            text_msg += "📌 لطفاً یک متریال انتخاب کنید."
            await message.reply(text_msg, reply_markup=keyboard)
            return
        
        elif step == "material":
            mat_id = None
            for mid, mat in MATERIALS.items():
                if text == mat["name"]:
                    mat_id = mid
                    break
            
            if mat_id is None:
                await message.reply("❌ **متریال نامعتبر!** لطفاً از لیست انتخاب کنید.")
                return
            session["material"] = mat_id
            session["step"] = "armor"
            
            text_msg = f"✅ **متریال {MATERIALS[mat_id]['name']} ثبت شد!** 🏗️\n\n"
            text_msg += "📋 **مرحله ۵ از ۸: انتخاب زره**\n\n"
            text_msg += "🛡️ *زره از کشتی شما در برابر حملات محافظت می‌کنه!*\n\n"
            
            keyboard = ReplyKeyboard(resize=True)
            keyboard.add_row("بدون زره")
            for aid, arm in ARMORS.items():
                keyboard.add_row(arm["name"])
                text_msg += f"📌 **{arm['name']}** (شناسه: `{aid}`)\n"
                text_msg += f"   ❤️ افزایش HP: {arm['hp_bonus']}%\n"
                text_msg += f"   💰 هزینه: ${arm['cost']:,}\n\n"
            
            text_msg += "📌 لطفاً یک زره انتخاب کنید یا `none` بزنید برای رد کردن."
            await message.reply(text_msg, reply_markup=keyboard)
            return
        
        elif step == "armor":
            arm_id = None
            if text == "بدون زره" or text.lower() == "none":
                arm_id = None
            else:
                for aid, arm in ARMORS.items():
                    if text == arm["name"]:
                        arm_id = aid
                        break
            
            if arm_id is None and text.lower() != "none":
                await message.reply("❌ **زره نامعتبر!** لطفاً از لیست انتخاب کنید.")
                return
            session["armor_type"] = arm_id
            session["step"] = "weapons"
            session["weapons"] = []
            session["weapon_count"] = 0
            hull = HULLS[session["hull"]]
            max_hp = hull["hardpoints"]
            if session.get("modifier") == "extended_deck":
                max_hp += 2
            session["max_weapons"] = max_hp
            
            text_msg = f"✅ **زره ثبت شد!** 🛡️\n\n"
            text_msg += f"📋 **مرحله ۶ از ۸: انتخاب سلاح‌ها** (0/{max_hp})\n\n"
            text_msg += "🔫 *حالا بریم سراغ بخش هیجان‌انگیز: مسلح کردن کشتی!*\n"
            text_msg += f"💡 *شما {max_hp} اسلات سلاح دارید.*\n\n"
            text_msg += "🔰 لطفاً سلاح‌ها رو انتخاب کنید:"
            
            keyboard = ReplyKeyboard(resize=True)
            for wid, weapon in ALL_WEAPONS.items():
                keyboard.add_row(weapon["name"])
            keyboard.add_row("پایان")
            
            await message.reply(text_msg, reply_markup=keyboard)
            return
        
        elif step == "weapons":
            if text == "پایان" or text == "/design_done":
                if session["weapon_count"] == 0:
                    await message.reply("⚠️ **حداقل یک سلاح باید انتخاب کنید کاپیتان!** 🔫")
                    return
                session["step"] = "defenses"
                session["defenses"] = []
                
                text_msg = f"✅ **{session['weapon_count']} سلاح ثبت شد!** 🎯\n\n"
                text_msg += "📋 **مرحله ۷ از ۸: سیستم‌های دفاعی**\n\n"
                text_msg += "🛡️ *سیستم‌های دفاعی از کشتی شما در برابر حملات محافظت می‌کنن!*\n\n"
                text_msg += "🔰 **سیستم‌های موجود:**\n\n"
                
                keyboard = ReplyKeyboard(resize=True)
                for did, defense in ACTIVE_DEFENSES.items():
                    keyboard.add_row(defense["name"])
                keyboard.add_row("پایان")
                
                await message.reply(text_msg, reply_markup=keyboard)
                return
            
            for wid, weapon in ALL_WEAPONS.items():
                if text == weapon["name"]:
                    if session["weapon_count"] >= session["max_weapons"]:
                        await message.reply(
                            f"❌ **حداکثر سلاح رو انتخاب کردید!** ({session['max_weapons']})\n"
                            f"📌 `پایان` رو بزنید تا برید مرحله بعد."
                        )
                        return
                    session["weapons"].append({"id": wid})
                    session["weapon_count"] += 1
                    await message.reply(
                        f"✅ **{weapon['name']} اضافه شد!** 🔫\n"
                        f"📊 پیشرفت: {session['weapon_count']}/{session['max_weapons']}\n\n"
                        f"💡 می‌تونید سلاح دیگه‌ای اضافه کنید یا `پایان` رو بزنید!"
                    )
                    return
            await message.reply("⚠️ **لطفاً از لیست سلاح‌ها انتخاب کنید یا `پایان` رو بزنید.**")
            return
        
        elif step == "defenses":
            if text == "پایان" or text == "/design_final":
                session["step"] = "modules"
                session["modules"] = []
                
                text_msg = "✅ **سیستم‌های دفاعی ثبت شد!** 🛡️\n\n"
                text_msg += "📋 **مرحله ۸ از ۸: ماژول‌های ویژه** *(مرحله آخر!)*\n\n"
                text_msg += "🧩 *ماژول‌ها قدرت‌های ویژه‌ای به کشتی شما می‌دن!*\n\n"
                
                keyboard = ReplyKeyboard(resize=True)
                for mid, mod in SPECIAL_MODULES.items():
                    keyboard.add_row(mod["name"])
                keyboard.add_row("ذخیره و پایان")
                keyboard.add_row("رد کردن")
                
                await message.reply(text_msg, reply_markup=keyboard)
                return
            
            for did, defense in ACTIVE_DEFENSES.items():
                if text == defense["name"]:
                    if did in session["defenses"]:
                        await message.reply("❌ **این سیستم قبلاً اضافه شده!**")
                        return
                    session["defenses"].append(did)
                    await message.reply(
                        f"✅ **{defense['name']} اضافه شد!** 🛡️\n"
                        f"📌 سیستم دفاعی دیگه‌ای اضافه کنید یا `پایان` رو بزنید."
                    )
                    return
            await message.reply("⚠️ **لطفاً از لیست دفاع‌ها انتخاب کنید یا `پایان` رو بزنید.**")
            return
        
        elif step == "modules":
            if text == "رد کردن" or text == "/design_skip":
                session["modules"] = []
                await save_design(message, user_id, session)
                return
            
            if text == "ذخیره و پایان" or text == "/design_save":
                await save_design(message, user_id, session)
                return
            
            for mid, mod in SPECIAL_MODULES.items():
                if text == mod["name"]:
                    if mid in session["modules"]:
                        await message.reply("❌ **این ماژول قبلاً اضافه شده!**")
                        return
                    session["modules"].append(mid)
                    await message.reply(
                        f"✅ **{mod['name']} اضافه شد!** 🧩\n"
                        f"📌 ماژول دیگه‌ای اضافه کنید، `ذخیره و پایان` یا `رد کردن` رو بزنید."
                    )
                    return
            await message.reply("⚠️ **لطفاً از لیست ماژول‌ها انتخاب کنید، `ذخیره و پایان` یا `رد کردن` رو بزنید.**")
            return

# ==================== GROUP HANDLERS ====================
@bot.on_message(group & text)
async def handle_group_text(message):
    user_id = message.author.id
    
    # Check for cute messages
    current_time = time.time()
    chat_id = message.chat.id
    if chat_id not in last_cute_message_time or current_time - last_cute_message_time[chat_id] > cute_message_interval:
        last_cute_message_time[chat_id] = current_time
        cute_msg = random.choice(CUTE_MESSAGES)
        if random.random() < 0.3:
            await message.reply(cute_msg)
    
    # Try to handle as attack first (using external handler)
    attack_handled = await handle_group_attack(message, bot, arcade_data, active_battles, ALL_WEAPONS)

@bot.on_callback_query()
async def handle_callbacks(callback_query):
    data = callback_query.data
    user_id = callback_query.author.id
    
    if data.startswith("group_attack_"):
        parts = data.split("_")
        attack_type = parts[2]
        target_id = parts[3]
        
        player = get_player(user_id)
        target_player = get_player(target_id)
        
        if not player.get("ships") or not target_player.get("ships"):
            await callback_query.answer("❌ یکی از بازیکنان کشتی نداره!", show_alert=True)
            return
        
        ship1 = player["ships"][0]
        ship2 = target_player["ships"][0]
        arena = "open_ocean"
        
        battle = Battle(user_id, target_id, ship1, ship2, arena)
        battle_id = f"{user_id}_{target_id}_{time.time()}"
        active_battles[battle_id] = battle
        active_battles[f"player_{user_id}"] = battle_id
        active_battles[f"player_{target_id}"] = battle_id
        
        screen = battle.get_battle_screen(1)
        screen += "\n\n" + "═" * 35 + "\n"
        screen += (
            "🎯 **دستورات نبرد:**\n"
            "🔫 `/act fire` — شلیک\n"
            "🏃 `/act close` — نزدیک شدن\n"
            "💨 `/act open` — فاصله گرفتن\n"
            "🛡️ `/act defensive` — دفاع\n"
        )
        
        await callback_query.message.edit_text(
            f"⚔️ **نبرد گروهی آغاز شد!** 🌊\n\n{screen}"
        )
        await callback_query.answer("✅ نبرد آغاز شد! موفق باشید کاپیتان! 🚢")
        return
    
    # Handle other callbacks
    await callback_query.answer("❓ دستور نامعتبر!")

# ==================== RANDOM CUTE MESSAGE TASK ====================
async def send_random_cute_messages():
    """Background task to send random cute messages to active chats"""
    while True:
        try:
            await asyncio.sleep(random.randint(1800, 3600))  # 30-60 minutes
            
            # This would need a list of active chats
            # For now, we'll just log it
            cute_msg = random.choice(CUTE_MESSAGES)
            print(f"Would send cute message: {cute_msg}")
            
            # In a real implementation, you'd send to active chats
            # For private chats, you'd need to track active users
            
        except Exception as e:
            print(f"Error in cute message task: {e}")
            await asyncio.sleep(60)

# ==================== RUN BOT ====================
if __name__ == "__main__":
    print("╔══════════════════════════════════════╗")
    print("║  🚀 Admiral's Gambit Arcade Bot 🚀  ║")
    print("║  Starting naval combat system...     ║")
    print("╚══════════════════════════════════════╝")
    load_data()
    
    # Start background tasks
    loop = asyncio.get_event_loop()
    loop.create_task(send_random_cute_messages())
    
    bot.run()