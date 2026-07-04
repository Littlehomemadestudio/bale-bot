"""
Battle system for Admiral's Gambit Arcade
Handles combat mechanics, turn processing, and battle state
"""
import random
from typing import Dict, Any, List, Optional, Tuple

from .models import (
    HULLS, HULL_MODIFIERS, MATERIALS, ARMORS, ACTIVE_DEFENSES,
    SPECIAL_MODULES, ALL_WEAPONS, ARENAS, KILL_STREAKS, ARENA_HAZARDS
)
from .data_loader import get_player


def calculate_ship_stats(ship: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate final ship stats based on components"""
    hull_id = ship["hull"]
    hull = HULLS[hull_id]
    hp = hull["hp"]
    speed = hull["speed"]
    hardpoints = hull["hardpoints"]
    armor = hull["armor"]
    slots = hull["slots"]
    cost = hull["cost"]
    
    # Apply hull modifier
    mod = ship.get("modifier")
    if mod and mod in HULL_MODIFIERS:
        m = HULL_MODIFIERS[mod]
        hp += hp * m.get("hp_bonus", 0) // 100
        speed += m.get("speed_bonus", 0) + m.get("speed_penalty", 0)
        hardpoints += m.get("hardpoints_bonus", 0)
        armor += armor * m.get("armor_penalty", 0) // 100
    
    # Apply material
    mat = ship.get("material")
    if mat and mat in MATERIALS:
        m = MATERIALS[mat]
        hp += hp * m["hp_bonus"] // 100
        speed += m["speed_bonus"]
        cost *= m["cost_mult"]
        armor += armor * m.get("armor_penalty", 0) // 100
    
    # Apply armor type
    arm = ship.get("armor_type")
    if arm and arm in ARMORS:
        a = ARMORS[arm]
        hp += hp * a["hp_bonus"] // 100
        speed += a.get("speed_penalty", 0)
        cost += a["cost"]
    
    # Add weapon costs
    for w in ship.get("weapons", []):
        if w["id"] in ALL_WEAPONS:
            cost += ALL_WEAPONS[w["id"]]["cost"]
    
    # Add defense costs
    for d in ship.get("defenses", []):
        if d in ACTIVE_DEFENSES:
            cost += ACTIVE_DEFENSES[d]["cost"]
    
    # Add module costs
    for m in ship.get("modules", []):
        if m in SPECIAL_MODULES:
            cost += SPECIAL_MODULES[m]["cost"]
    
    return {
        "hp": hp, "max_hp": hp, "speed": speed,
        "hardpoints": hardpoints, "armor": armor,
        "slots": slots, "cost": cost,
        "weapons": ship.get("weapons", []),
        "defenses": ship.get("defenses", []),
        "modules": ship.get("modules", [])
    }


class Battle:
    """Manages naval battle between two players"""
    
    def __init__(self, player1_id: int, player2_id: int, 
                 ship1: Dict[str, Any], ship2: Dict[str, Any], arena: str):
        """
        Initialize a new battle
        
        Args:
            player1_id: First player's user ID
            player2_id: Second player's user ID
            ship1: First player's ship design
            ship2: Second player's ship design
            arena: Arena identifier
        """
        self.player1 = player1_id
        self.player2 = player2_id
        self.ship1 = calculate_ship_stats(ship1)
        self.ship2 = calculate_ship_stats(ship2)
        self.ship1_design = ship1
        self.ship2_design = ship2
        self.arena = arena
        self.range = ARENAS[arena]["start_range"]
        self.round = 0
        self.hazard: Optional[Dict[str, Any]] = None
        self.rage1 = 0
        self.rage2 = 0
        self.cooldowns1: Dict[int, int] = {}
        self.cooldowns2: Dict[int, int] = {}
        self.overdrive1 = False
        self.overdrive2 = False
        self.overdrive_turns1 = 0
        self.overdrive_turns2 = 0
        self.speed_boost1 = False
        self.speed_boost2 = False
        self.speed_boost_turns1 = 0
        self.speed_boost_turns2 = 0
        self.last_action1 = ""
        self.last_action2 = ""
        self.finished = False
        self.winner: Optional[int] = None
        self.log: List[str] = []
    
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
