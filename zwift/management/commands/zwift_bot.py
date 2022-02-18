import logging
import sys

import discord
from django.core.management import BaseCommand
from bot.bot import BasicCommandBot
from zwift.cogs.zwift_cog import ZwiftCog
from wrh_bot.settings import DISCORD_TOKEN_ZWIFT


def get_logger():
    logger = logging.getLogger('')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = get_logger()


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info('Starting wrh Discord Bot ...')
        intents = discord.Intents(messages=True, guilds=True, members=True)
        bot = BasicCommandBot(command_prefix='!zw ', intents=intents, description='We Race Here Bot for better racing!',logger=logger)
        bot.add_cog(ZwiftCog(bot, logger=logger))
        bot.run(DISCORD_TOKEN_ZWIFT)


