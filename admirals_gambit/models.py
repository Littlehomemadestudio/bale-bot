"""
Game data models for Admiral's Gambit Arcade
Contains all ship components, weapons, and game constants
"""

# ==================== HULLS ====================
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
    "stealth": {"name": "پروفیل پنهانکار 👻", "stealth_bonus": 30, "hp_bonus": -10},
    "extended_deck": {"name": "عرشه گسترده 📐", "hardpoints_bonus": 2, "armor_penalty": -15},
}

MATERIALS = {
    "steel": {"name": "فولاد 🏗️", "cost_mult": 1, "hp_bonus": 0, "speed_bonus": 0, "stealth_bonus": 0},
    "titanium": {"name": "تیتانیوم ✨", "cost_mult": 3, "hp_bonus": 20, "speed_bonus": 2, "stealth_bonus": 0},
    "composite": {"name": "کامپوزیت 🧬", "cost_mult": 2, "hp_bonus": 0, "speed_bonus": 0, "stealth_bonus": 30, "armor_penalty": -10},
}

# ==================== WEAPONS ====================
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

# Combine all weapons into a single dictionary
ALL_WEAPONS = {}
for k, v in GUNS.items():
    ALL_WEAPONS[f"gun_{k}"] = {**v, "type": "gun", "id": k}
for k, v in MISSILES.items():
    ALL_WEAPONS[f"missile_{k}"] = {**v, "type": "missile", "id": k}
for k, v in TORPEDOES.items():
    ALL_WEAPONS[f"torpedo_{k}"] = {**v, "type": "torpedo", "id": k}
for k, v in ENERGY_WEAPONS.items():
    ALL_WEAPONS[f"energy_{k}"] = {**v, "type": "energy", "id": k}

# ==================== DEFENSIVE SYSTEMS ====================
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

# ==================== ARENA & COMBAT ====================
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
