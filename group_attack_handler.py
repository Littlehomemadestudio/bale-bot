"""
Group Attack Handler for Admiral's Gambit Arcade
Handles natural language attack parsing and execution in group chats
"""
import re
import random
import time
from collections import defaultdict

# ==================== WEAPON KEYWORDS ====================
TRIGGER_WORDS_EN = [
    "fire", "shoot", "attack", "destroy", "kill", "bombard", "blast", 
    "strike", "launch", "hit", "engage", "aim", "target", "open fire"
]

TRIGGER_WORDS_FA = [
    "آتش", "شلیک", "حمله", "بزن", "بکوب", "منهدم", "منفجر", "پرتاب", 
    "هدف", "درگیر", "آتیش", "بزنید", "شلیک کنید", "آتش کنید", "حمله کنید",
    "بزنش", "بکوبش", "منهدمش", "بترکون", "بترکونش", "نابود", "نابودش"
]

WEAPON_KEYWORDS = {
    "gun": ["cannon", "gun", "توپ", "کانن", "مسلسل", "machinegun", "machine gun",
            "artillery", "توپخانه", "gatling", "گاتلینگ", "canon", "کنن"],
    "missile": ["missile", "rocket", "موشک", "راکت", "موسک", "cruise", "کروز",
                "موشک انداز", "راکت انداز", "missle"],
    "torpedo": ["torpedo", "اژدر", "torpedo", "اژدر", "underwater", "زیرآبی",
                "torpeedo", "ترپدو"],
    "energy": ["laser", "لیزر", "plasma", "پلاسما", "railgun", "ریلگان", 
               "beam", "پرتو", "energy", "انرژی", "لیزر", "lazer"]
}

SIZE_KEYWORDS = {
    "light": ["light", "small", "سبک", "کوچک", "نرم", "weak", "ضعیف", "کم", 
              "یه", "یکم", "کمی", "آروم", "smallest", "کوچکترین"],
    "medium": ["medium", "standard", "متوسط", "استاندارد", "normal", "معمولی",
               "medium", "میانه", "متوسطه"],
    "heavy": ["heavy", "big", "large", "سنگین", "بزرگ", "strong", "قوی", 
              "massive", "عظیم", "شدید", "محکم", "کاری", "حسابی", "گنده",
              "biggest", "largest", "heaviest", "بزرگترین", "سنگین‌ترین"],
    "maximum": ["maximum", "ultimate", "max", "نهایی", "بیشترین", "اقصی", 
                "ماکزیمم", "فول", "full", "تمام", "همه", "هرچی", "هر چی"]
}

ALTITUDE_KEYWORDS = [
    "altitude", "ارتفاع", "angle", "زاویه", "degree", "درجه",
    "elevation", "شیب", "trajectory", "مسیر", "پرواز", "flight"
]

# ==================== HIT MESSAGES ====================
HIT_MESSAGES = {
    "perfect": [
        "🎯 **اصابت مستقیم!!!** کشتی دشمن به شدت آسیب دید! 💥",
        "💥 **هدف منهدم شد!!!** چه نشونه‌گیری عالی‌ای! 🔥",
        "🔥 **آتش از کشتی دشمن زبانه می‌کشه!!!** عالی بود کاپیتان! 💪",
        "⚡ **ضربه کاری!!!** دشمن به سختی تکون خورد! 🚢💢",
        "🎪 **سیرک مرگ!!!** اصابت بی‌نظیر! خدمه دشمن وحشت کردن! 😱"
    ],
    "good": [
        "✅ **اصابت موفق!** آسیب خوبی وارد شد. 👏",
        "👏 **نشونه‌گیری خوب!** دشمن تکون خورد! 💢",
        "💢 **ضربه محکمی بهشون زدی!** ادامه بده! ⚔️",
        "🎯 **هدف اصابت کرد!** دشمن داره آب می‌گیره! 🌊",
        "💪 **محکم زدیشون!** آفرین کاپیتان! ⚓"
    ],
    "glancing": [
        "😬 **اصابت سطحی!** فقط خش افتاد... 🛡️",
        "💨 **از کنارش رد شد...** آسیب کم! 🌊",
        "🛡️ **به زره خورد!** زیاد کاری نکرد... 😕",
        "📉 **ضربه ضعیف...** دشمن فقط لرزید! 😤",
        "💧 **فقط رنگش رو خراشیدی!** بیشتر تلاش کن! 😅"
    ],
    "miss": [
        "❌ **خطا!** توی آب خورد! 🌊💦",
        "🌊 **والها رو ترسوندی** ولی دشمن رو نه! 🐋",
        "😅 **اوه... ماهی‌ها رو زدی!** دشمن سالم موند! 🐠",
        "💨 **هوا رو سوراخ کردی!** هدف رو نزدی! 😤",
        "🤦 **اشتباه زدی!** دشمن داره می‌خنده! 😡",
        "🎲 **شانس باهات یار نبود...** دوباره تلاش کن! 🎯"
    ],
    "intercepted": [
        "🚫 **سیستم دفاعی دشمن خنثاش کرد!** CIWS وارد عمل شد! 🛡️",
        "🛡️ **CIWS دشمن موشک رو زد!** لعنتی! 😤",
        "💢 **دشمن سپر داره!** حمله دفع شد! 🚫",
        "🔰 **دفاع دشمن فعال شد!** نتونستیم نفوذ کنیم! 😞",
        "⚡ **ECM دشمن مسیر رو منحرف کرد!** حمله ناموفق! 📡"
    ]
}

# ==================== COOLDOWN MANAGEMENT ====================
class CooldownManager:
    def __init__(self):
        self.cooldowns = defaultdict(dict)
    
    def is_on_cooldown(self, user_id, weapon_key, battle_round=0):
        if user_id not in self.cooldowns:
            return False
        if weapon_key not in self.cooldowns[user_id]:
            return False
        if battle_round > 0:
            return self.cooldowns[user_id][weapon_key] > battle_round
        else:
            return time.time() < self.cooldowns[user_id][weapon_key]
    
    def set_cooldown(self, user_id, weapon_key, duration, battle_round=0):
        if battle_round > 0:
            self.cooldowns[user_id][weapon_key] = battle_round + duration
        else:
            self.cooldowns[user_id][weapon_key] = time.time() + duration
    
    def get_remaining_cooldown(self, user_id, weapon_key, battle_round=0):
        if not self.is_on_cooldown(user_id, weapon_key, battle_round):
            return 0
        if battle_round > 0:
            return self.cooldowns[user_id][weapon_key] - battle_round
        else:
            return max(0, self.cooldowns[user_id][weapon_key] - time.time())

cooldown_manager = CooldownManager()

# ==================== NLP PARSER ====================
class AttackParser:
    def __init__(self, message_text):
        self.text = message_text.lower()
        self.original = message_text
    
    def has_trigger_words(self):
        for word in TRIGGER_WORDS_EN + TRIGGER_WORDS_FA:
            if word in self.text:
                return True
        return False
    
    def get_weapon_type(self):
        for wtype, keywords in WEAPON_KEYWORDS.items():
            for keyword in keywords:
                if keyword in self.text:
                    return wtype
        return None
    
    def get_size_preference(self):
        for size, keywords in SIZE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in self.text:
                    return size
        return None
    
    def get_caliber(self):
        patterns = [
            r'(\d+)\s*mm',
            r'(\d+)\s*میلیمتر',
            r'(\d+)\s*میلی متر',
            r'caliber\s*(\d+)',
            r'calibre\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text)
            if match:
                return int(match.group(1))
        
        persian_numbers = {
            '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
            '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
        }
        
        for pattern in [r'([۰-۹]+)\s*mm', r'([۰-۹]+)\s*میلیمتر']:
            match = re.search(pattern, self.text)
            if match:
                persian_num = match.group(1)
                english_num = ''.join(persian_numbers.get(c, c) for c in persian_num)
                return int(english_num)
        
        return None
    
    def get_altitude(self):
        for keyword in ALTITUDE_KEYWORDS:
            if keyword in self.text:
                patterns = [
                    rf'{keyword}\s*(\d+)',
                    rf'(\d+)\s*{keyword}',
                    rf'(\d+)\s*degree',
                    rf'(\d+)\s*درجه',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, self.text)
                    if match:
                        return int(match.group(1))
                
                persian_numbers = {
                    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
                    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
                }
                
                for pattern in [rf'{keyword}\s*([۰-۹]+)', rf'([۰-۹]+)\s*{keyword}']:
                    match = re.search(pattern, self.text)
                    if match:
                        persian_num = match.group(1)
                        english_num = ''.join(persian_numbers.get(c, c) for c in persian_num)
                        return int(english_num)
                
                return 0
        
        return None
    
    def get_emotion(self):
        angry_words = [
            "لعنتی", "damn", "fuck", "shit", "bastard", "مادر",
            "گه", "آشغال", "سگ", "خر", "fucking", "stupid", "idiot",
            "احمق", "نفهم", "کثافت", "پدرسگ"
        ]
        
        emotion_score = 0
        for word in angry_words:
            if word in self.text:
                emotion_score += 1
        
        if emotion_score >= 3:
            return "furious"
        elif emotion_score >= 1:
            return "angry"
        else:
            return "normal"

# ==================== MATH CHALLENGE ====================
def generate_math_challenge(target_number):
    if target_number <= 0:
        return None, None
    
    challenges = []
    
    if target_number > 2:
        a = random.randint(1, target_number - 1)
        b = target_number - a
        challenges.append((f"{a} + {b} = ?", target_number, "simple"))
    
    a = random.randint(target_number + 1, target_number + 20)
    b = a - target_number
    challenges.append((f"{a} - {b} = ?", target_number, "simple"))
    
    if target_number <= 20:
        factors = []
        for i in range(1, target_number + 1):
            if target_number % i == 0 and i <= 10 and target_number // i <= 10:
                factors.append((i, target_number // i))
        if factors:
            a, b = random.choice(factors)
            challenges.append((f"{a} × {b} = ?", target_number, "medium"))
    
    if not challenges:
        a = target_number - random.randint(1, max(1, target_number - 1))
        b = target_number - a
        challenges.append((f"{a} + {b} = ?", target_number, "simple"))
    
    return random.choice(challenges)

# ==================== WEAPON MATCHING ====================
def find_best_weapon(parser, ship_weapons, all_weapons_data):
    weapon_type = parser.get_weapon_type()
    size_pref = parser.get_size_preference()
    caliber = parser.get_caliber()
    
    available_weapons = []
    for w in ship_weapons:
        wid = w["id"]
        if wid in all_weapons_data:
            w_data = all_weapons_data[wid]
            available_weapons.append((wid, w_data))
    
    if not available_weapons:
        return None, None, 0
    
    if caliber:
        for wid, w_data in available_weapons:
            w_name = w_data.get("name", "").lower()
            if str(caliber) in w_name:
                return wid, w_data, 95
    
    if weapon_type:
        type_weapons = [(wid, wd) for wid, wd in available_weapons 
                       if wd.get("type") == weapon_type]
        if type_weapons:
            available_weapons = type_weapons
    
    available_weapons.sort(key=lambda x: x[1].get("damage", x[1].get("dps", 0)), reverse=True)
    
    if size_pref == "light":
        available_weapons.sort(key=lambda x: x[1].get("damage", x[1].get("dps", 0)))
        return available_weapons[0][0], available_weapons[0][1], 70
    elif size_pref in ["heavy", "maximum"]:
        return available_weapons[0][0], available_weapons[0][1], 80
    
    if available_weapons:
        return available_weapons[0][0], available_weapons[0][1], 60
    
    return None, None, 0

# ==================== ACCURACY CALCULATION ====================
def calculate_accuracy(weapon_data, range_km, altitude_mentioned, altitude_correct, emotion):
    base_accuracy = 65
    
    weapon_type = weapon_data.get("type", "gun")
    type_modifiers = {"gun": 0, "missile": 5, "torpedo": -10, "energy": 15}
    base_accuracy += type_modifiers.get(weapon_type, 0)
    
    weapon_range = weapon_data.get("range", 10)
    if range_km <= weapon_range * 0.3:
        base_accuracy += 20
    elif range_km <= weapon_range * 0.5:
        base_accuracy += 10
    elif range_km > weapon_range:
        base_accuracy -= 25
    elif range_km > weapon_range * 0.7:
        base_accuracy -= 5
    
    if altitude_mentioned:
        if altitude_correct:
            base_accuracy += 15
        else:
            base_accuracy -= 25
    
    if emotion == "furious":
        base_accuracy += 10
    elif emotion == "angry":
        base_accuracy += 5
    
    base_accuracy += random.randint(-10, 10)
    base_accuracy = max(5, min(95, base_accuracy))
    
    return base_accuracy

# ==================== DAMAGE CALCULATION ====================
def calculate_damage(base_damage, accuracy_roll, accuracy_percent, altitude_mentioned, altitude_correct):
    if accuracy_roll > accuracy_percent:
        return 0, "miss"
    
    if accuracy_roll <= accuracy_percent * 0.2:
        hit_quality = "perfect"
        damage_mult = 1.5
    elif accuracy_roll <= accuracy_percent * 0.5:
        hit_quality = "good"
        damage_mult = 1.0
    else:
        hit_quality = "glancing"
        damage_mult = 0.5
    
    if random.random() < 0.05:
        hit_quality = "perfect"
        damage_mult *= 2
    
    if altitude_mentioned:
        if altitude_correct:
            damage_mult *= 1.2
        else:
            damage_mult *= 0.8
    
    final_damage = int(base_damage * damage_mult)
    return final_damage, hit_quality

# ==================== RESPONSE GENERATOR ====================
def generate_attack_response(attacker_name, target_name, weapon_name, damage, 
                             hit_quality, math_challenge=None, math_correct=None,
                             altitude_mentioned=False, cooldown_remaining=0):
    response = ""
    response += "╔══════════════════════════════════════╗\n"
    response += "║     ⚔️ **گزارش حمله دریایی** ⚔️     ║\n"
    response += "╚══════════════════════════════════════╝\n\n"
    
    response += f"👤 **فرمانده:** {attacker_name}\n"
    response += f"🎯 **هدف:** {target_name}\n"
    response += f"🔫 **سلاح:** {weapon_name}\n\n"
    
    response += "─" * 38 + "\n\n"
    
    if damage > 0:
        category = hit_quality if hit_quality in HIT_MESSAGES else "good"
        hit_msg = random.choice(HIT_MESSAGES[category])
        response += f"{hit_msg}\n\n"
        
        if damage > 2000:
            response += f"💥💥💥 **آسیب وارد شده: {damage:,}** 💥💥💥\n"
            response += "🔥 *انفجار مهیب! دشمن به شدت آسیب دید!*\n"
        elif damage > 1000:
            response += f"💥💥 **آسیب وارد شده: {damage:,}** 💥💥\n"
            response += "💢 *ضربه محکمی بود! دشمن تکون خورد!*\n"
        elif damage > 500:
            response += f"💥 **آسیب وارد شده: {damage:,}** 💥\n"
            response += "👊 *ضربه خوبی بهشون زدی!*\n"
        else:
            response += f"💢 **آسیب وارد شده: {damage:,}** 💢\n"
            response += "😬 *ضربه ضعیفی بود... ولی بالاخره ضربه‌ست!*\n"
        
        if altitude_mentioned and math_correct is not None:
            if math_correct:
                response += "\n📐 **زاویه صحیح!** +۲۰٪ آسیب اضافی! ✅\n"
            else:
                response += "\n📐 **زاویه اشتباه!** -۲۰٪ کاهش آسیب! ❌\n"
    else:
        if hit_quality == "intercepted":
            hit_msg = random.choice(HIT_MESSAGES["intercepted"])
        else:
            hit_msg = random.choice(HIT_MESSAGES["miss"])
        response += f"{hit_msg}\n\n"
        response += "💨 **آسیب: ۰** - حمله ناموفق!\n"
    
    response += "\n" + "─" * 38 + "\n"
    
    if cooldown_remaining > 0:
        response += f"\n⏳ **خنک‌سازی سلاح:** {cooldown_remaining} ثانیه\n"
    
    crew_comments = [
        "🗣️ خدمه: «کاپیتان! منتظر دستور بعدی هستیم!»",
        "🗣️ خدمه: «آماده شلیک مجدد هستیم!»",
        "🗣️ ناوبان: «هدف در رادار مشاهده میشه!»",
        "🗣️ مهندس: «سیستم‌ها آماده‌ان کاپیتان!»",
    ]
    response += f"\n{random.choice(crew_comments)}\n"
    
    return response

# ==================== MAIN ATTACK HANDLER ====================
async def handle_group_attack(message, bot, arcade_data, active_battles, ALL_WEAPONS):
    # Check if message is a reply
    if not message.reply_to_message or not message.reply_to_message.author:
        return False
    
    # Parse the message
    parser = AttackParser(message.text)
    
    # Check if it's an attack command
    if not parser.has_trigger_words():
        return False
    
    attacker_id = message.author.id
    target_user = message.reply_to_message.author
    target_id = target_user.id
    
    # Prevent self-attack
    if attacker_id == target_id:
        await message.reply(
            "❌ **کاپیتان! نمی‌تونی به خودت حمله کنی!** 😅\n"
            "💡 *این که خودکشیه! یه دشمن واقعی پیدا کن!*"
        )
        return True
    
    # Get player data - import from main
    import __main__
    get_player = __main__.get_player
    
    player = get_player(attacker_id)
    target_player = get_player(target_id)
    
    # Check ships
    if not player.get("ships"):
        await message.reply(
            f"❌ **{message.author.first_name} کشتی نداره!** 🚢\n"
            "💡 اول با `/design` کشتی بساز!"
        )
        return True
    
    if not target_player.get("ships"):
        await message.reply(
            f"❌ **{target_user.first_name} کشتی نداره!** 🚢\n"
            "💡 *بهش بگو اول کشتی بسازه!*"
        )
        return True
    
    # Get ships
    attacker_ship = player["ships"][0]
    
    # Find best weapon
    weapon_id, weapon_data, confidence = find_best_weapon(
        parser, attacker_ship.get("weapons", []), ALL_WEAPONS
    )
    
    if not weapon_data:
        await message.reply(
            "❌ **سلاحی پیدا نشد!** 🔍\n"
            "💡 *مشخص کن با چی می‌خوای حمله کنی!*\n"
            "📌 مثال: `با توپ سنگین آتش کن!` یا `موشک شلیک کن!`"
        )
        return True
    
    # Check cooldown
    if cooldown_manager.is_on_cooldown(attacker_id, weapon_id):
        remaining = cooldown_manager.get_remaining_cooldown(attacker_id, weapon_id)
        await message.reply(
            f"⏳ **سلاح در حال خنک‌سازی!** 🔫\n"
            f"🔧 {weapon_data.get('name', 'سلاح')} تا {remaining:.1f} ثانیه دیگه آماده نیست!\n"
            f"💡 *صبور باش کاپیتان!* ⚓"
        )
        return True
    
    # Handle altitude
    altitude = parser.get_altitude()
    altitude_mentioned = altitude is not None
    math_challenge = None
    correct_answer = None
    math_correct = None
    
    if altitude_mentioned and altitude > 0:
        challenge_text, correct_answer, difficulty = generate_math_challenge(altitude)
        if challenge_text:
            math_challenge = challenge_text
    
    # Calculate accuracy
    range_km = 20
    emotion = parser.get_emotion()
    accuracy_percent = calculate_accuracy(
        weapon_data, range_km, altitude_mentioned, 
        True if not math_challenge else True,  # Assume correct if no challenge
        emotion
    )
    
    # Roll for hit
    accuracy_roll = random.randint(1, 100)
    
    # Calculate damage
    base_damage = weapon_data.get("damage", weapon_data.get("dps", 100))
    if weapon_data.get("count"):
        base_damage *= weapon_data["count"]
    
    if math_challenge:
        damage, hit_quality = calculate_damage(
            base_damage, accuracy_roll, accuracy_percent, True, True
        )
    else:
        damage, hit_quality = calculate_damage(
            base_damage, accuracy_roll, accuracy_percent, False, False
        )
    
    # Generate response
    response = generate_attack_response(
        message.author.first_name,
        target_user.first_name,
        weapon_data.get("name", "سلاح"),
        damage,
        hit_quality,
        math_challenge=math_challenge,
        math_correct=math_correct,
        altitude_mentioned=altitude_mentioned,
        cooldown_remaining=0
    )
    
    # Add math challenge if applicable
    if math_challenge:
        response += f"\n🧮 **چالش ریاضی:**\n"
        response += f"📐 برای زاویه {altitude} درجه:\n"
        response += f"``` {math_challenge} ```\n"
        response += f"⏰ *۱۰ ثانیه وقت داری جواب بدی!*\n"
        response += f"📌 با `/answer [عدد]` جواب بده!\n"
    
    # Set cooldown
    weapon_type = weapon_data.get("type", "gun")
    cooldown_times = {"gun": 3, "missile": 5, "torpedo": 4, "energy": 3}
    cooldown = cooldown_times.get(weapon_type, 3)
    cooldown_manager.set_cooldown(attacker_id, weapon_id, cooldown)
    
    # Send response
    await message.reply(response)
    
    return True