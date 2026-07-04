#!/usr/bin/env python3
"""
Admiral's Gambit Arcade - Main Entry Point
Run this file to start the bot.

Usage:
    python run.py
"""
import os
import sys
import logging
from balethon import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import package components
from admirals_gambit import (
    Config,
    DataLoader,
    Battle,
    RateLimiter,
    HULLS, GUNS, MISSILES, TORPEDOES,
    ENERGY_WEAPONS, ARMORS, ACTIVE_DEFENSES, SPECIAL_MODULES,
    ARENAS, KILL_STREAKS, ARENA_HAZARDS
)

# Initialize global instances
data_loader = DataLoader()
rate_limiter = RateLimiter()

# Create bot instance
bot = Client(Config.TOKEN)

# Store active battles
active_battles = {}


def get_player(user_id):
    """Get or create player data"""
    return data_loader.get_player(user_id)


def save_player(user_id, player_data):
    """Save player data"""
    data_loader.save_player(user_id, player_data)


@bot.on_command('start')
async def start_cmd(client, update):
    """Welcome command"""
    user = update.sender
    welcome_msg = (
        "⚓ **به آرکید دریایی دریاسالار خوش آمدید!** ⚓\n\n"
        "دستورات اصلی:\n"
        "🚢 /fleet - مشاهده ناوگان شما\n"
        "⚔️ /battle - شروع نبرد جدید\n"
        "🛠️ /build - ساخت کشتی جدید\n"
        "📊 /stats - مشاهده آمار\n"
        "❓ /help - راهنما\n\n"
        "برای شروع /fleet را بزنید!"
    )
    await bot.send_message(update.chat_id, welcome_msg)


@bot.on_command('help')
async def help_cmd(client, update):
    """Help command"""
    help_msg = (
        "📘 **راهنمای بازی**\n\n"
        "**کشتی‌سازی:**\n"
        "• از /build استفاده کنید\n"
        "• بدنه، سلاح و زره انتخاب کنید\n\n"
        "**نبرد:**\n"
        "• /battle برای نبرد تصادفی\n"
        "• /challenge @user برای چالش دوستانه\n\n"
        "**مدیریت:**\n"
        "• /fleet - مشاهده کشتی‌ها\n"
        "• /repair - تعمیر کشتی‌ها\n"
        "• /stats - آمار بازی\n\n"
        "سوالات بیشتر؟ به پشتیبانی پیام دهید."
    )
    await bot.send_message(update.chat_id, help_msg)


@bot.on_command('fleet')
async def fleet_cmd(client, update):
    """Show player fleet"""
    user_id = update.sender_id
    player = get_player(user_id)
    
    if not player or 'ships' not in player or not player['ships']:
        await bot.send_message(
            update.chat_id,
            "🚫 هنوز کشتی‌ای ندارید!\nاز /build برای ساخت کشتی استفاده کنید."
        )
        return
    
    ships = player['ships']
    msg = "🚢 **ناوگان شما:**\n\n"
    
    for i, ship in enumerate(ships, 1):
        ship_name = ship.get('name', f'کشتی {i}')
        hull_id = ship.get('hull', 'unknown')
        hull_name = HULLS.get(hull_id, {}).get('name', 'نامشخص')
        hp = ship.get('hp', 0)
        max_hp = ship.get('max_hp', 0)
        
        status = "✅ سالم" if hp == max_hp else f"⚠️ {hp}/{max_hp}"
        msg += f"{i}. {ship_name} ({hull_name}) - {status}\n"
    
    msg += "\nبرای مدیریت از /build یا /repair استفاده کنید."
    await bot.send_message(update.chat_id, msg)


@bot.on_command('build')
async def build_cmd(client, update):
    """Ship building interface"""
    user_id = update.sender_id
    player = get_player(user_id)
    
    if not player:
        player = {'ships': [], 'resources': {'credits': 1000}}
        save_player(user_id, player)
    
    build_menu = (
        "🛠️ **کارگاه ساخت کشتی**\n\n"
        "مراحل ساخت:\n"
        "1️⃣ انتخاب بدنه\n"
        "2️⃣ انتخاب سلاح‌ها\n"
        "3️⃣ انتخاب زره و تجهیزات\n"
        "4️⃣ نام‌گذاری کشتی\n\n"
        "برای شروع دستور زیر را بزنید:\n"
        "/build_hull"
    )
    await bot.send_message(update.chat_id, build_menu)


@bot.on_command('battle')
async def battle_cmd(client, update):
    """Start a new battle"""
    user_id = update.sender_id
    chat_id = update.chat_id
    
    # Check rate limit
    if not rate_limiter.check_limit(user_id, 'action'):
        await bot.send_message(
            chat_id,
            "⏳ لطفاً کمی صبر کنید و سپس دوباره تلاش کنید."
        )
        return
    
    player = get_player(user_id)
    
    if not player or 'ships' not in player or not player['ships']:
        await bot.send_message(
            chat_id,
            "🚫 برای نبرد نیاز به کشتی دارید!\nابتدا با /build کشتی بسازید."
        )
        return
    
    # Check if already in battle
    if user_id in active_battles:
        await bot.send_message(
            chat_id,
            "⚔️ شما هم‌اکنون در حال نبرد هستید!\nصبر کنید تا نبرد فعلی پایان یابد."
        )
        return
    
    # Initialize battle
    battle = Battle(player)
    active_battles[user_id] = battle
    
    await bot.send_message(
        chat_id,
        "⚔️ **جستجو برای حریف...**\n\n"
        "لطفاً صبر کنید..."
    )
    
    # Simulate finding opponent (in real implementation, match with another player)
    await process_battle_turn(client, update, battle)


async def process_battle_turn(client, update, battle):
    """Process one turn of battle"""
    try:
        result = battle.process_turn()
        
        if result.get('ended'):
            # Battle ended
            user_id = update.sender_id
            if user_id in active_battles:
                del active_battles[user_id]
            
            winner_msg = "🏆 **پیروزی!**" if result.get('won') else "💀 **شکست!**"
            final_msg = (
                f"{winner_msg}\n\n"
                f"نتیجه: {result.get('message', '')}\n\n"
                "برای نبرد مجدد /battle را بزنید."
            )
            await bot.send_message(update.chat_id, final_msg)
        else:
            # Battle continues
            battle_screen = battle.get_battle_screen()
            controls = (
                "\n\n**دستورات نبرد:**\n"
                "⚔️ /attack - حمله عادی\n"
                "🎯 /aimed - حمله دقیق\n"
                "🛡️ /defend - دفاع\n"
                "⚡ /overdrive - اضافه‌بار (اگر آماده است)"
            )
            await bot.send_message(update.chat_id, battle_screen + controls)
            
    except Exception as e:
        logger.error(f"Battle error: {e}")
        await bot.send_message(update.chat_id, "❌ خطا در پردازش نبرد. لطفاً دوباره تلاش کنید.")


@bot.on_command('attack')
async def attack_cmd(client, update):
    """Attack command during battle"""
    user_id = update.sender_id
    
    if user_id not in active_battles:
        await bot.send_message(
            update.chat_id,
            "⚔️ در حال حاضر در نبرد نیستید!\nبا /battle نبرد جدیدی شروع کنید."
        )
        return
    
    battle = active_battles[user_id]
    battle.set_action('attack')
    await process_battle_turn(client, update, battle)


@bot.on_command('defend')
async def defend_cmd(client, update):
    """Defend command during battle"""
    user_id = update.sender_id
    
    if user_id not in active_battles:
        await bot.send_message(
            update.chat_id,
            "⚔️ در حال حاضر در نبرد نیستید!"
        )
        return
    
    battle = active_battles[user_id]
    battle.set_action('defend')
    await process_battle_turn(client, update, battle)


@bot.on_command('stats')
async def stats_cmd(client, update):
    """Show player statistics"""
    user_id = update.sender_id
    player = get_player(user_id)
    
    if not player:
        await bot.send_message(
            update.chat_id,
            "📊 هنوز آماری ندارید. با بازی کردن آمار کسب کنید!"
        )
        return
    
    wins = player.get('wins', 0)
    losses = player.get('losses', 0)
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0
    
    stats_msg = (
        "📊 **آمار بازیکن**\n\n"
        f"🏆 پیروزی‌ها: {wins}\n"
        f"💀 شکست‌ها: {losses}\n"
        f"📈 نرخ برد: {win_rate:.1f}%\n"
        f"🚢 کشتی‌ها: {len(player.get('ships', []))}\n"
    )
    await bot.send_message(update.chat_id, stats_msg)


async def on_start():
    """Called when bot starts"""
    logger.info("✅ Admiral's Gambit Bot started successfully!")
    logger.info(f"📦 Loaded {len(HULLS)} hull types")
    logger.info(f"⚔️ Loaded {len(GUNS)} guns, {len(MISSILES)} missiles")
    logger.info(f"🏟️ Loaded {len(ARENAS)} arenas")


async def on_stop():
    """Called when bot stops"""
    logger.info("👋 Admiral's Gambit Bot stopped.")


# Register event handlers
bot.add_event_handler('connect', on_start)
bot.add_event_handler('disconnect', on_stop)


if __name__ == '__main__':
    print("=" * 50)
    print("⚓ Admiral's Gambit Arcade Bot")
    print("=" * 50)
    print("Starting bot...")
    
    try:
        bot.start()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)
