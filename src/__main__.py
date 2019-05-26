import json

import buildabot
import logging
import atexit
import asyncio
import os

bot_logger = logging.getLogger('bot')
bot_logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='bot.log', encoding='utf-8', mode='a+')
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] <%(levelname)s> %(message)s'))
bot_logger.addHandler(handler)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"

config = json.load(open('config.json'))

bot = buildabot.Bot(config=config, features_dir='src/features/')


def exit_handler():
    bot.feature_manager.logger.info("Stopping...")
    for feature_name in bot.feature_manager.features:
        feature = bot.feature_manager.features[feature_name]

        if not feature.is_enabled():
            continue
        if not bot.feature_manager.can_disable(feature):
            feature.logger.info("Can't disable, forcing.")

        feature.unregister_all_events()
        feature.logger.info("Disabled")
        # await feature.disable()

    bot.feature_manager.logger.info("Thank you and goodbye :)")


atexit.register(exit_handler)

bot.run()
