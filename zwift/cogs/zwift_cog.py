import logging
import typing

import discord
import requests
from asgiref.sync import sync_to_async
from discord.ext import commands


class ZwiftCog(commands.Cog, name='Zwift player commands'):

    def __init__(self, bot, logger=None):
        self.bot = bot
        self.logger = logger or logging.getLogger("ZwiftPlayerCog")

    @commands.guild_only()
    @commands.command(help='Get Team Results')
    async def teamresult(self, ctx, zwid: int):
        await self._teamresult(ctx, zwid)

    async def _teamresult(self, ctx, id: int, member: discord.Member = None):
        user_id = (member or ctx.author).id
        guild_id = ctx.guild.id
        result = requests.get(f'https://zwiftapi.weracehere.org/team_results?id={id}')
        desc = f'No result for **{id}**.'
        if result.status_code == 200:
            try:
                if result.json().get("data", None):
                    desc = f'Total {len(result.json().get("data", None))} Results Found'
            except Exception as e:
                pass
        embed = discord.Embed(description=desc)
        # embed.set_author(name="Go to zwift profile", icon_url=ZWIFT_LOGO_URL,
        #                  url=ZWIFT_PROFILE_URL.format(zwid=zwid))

        await ctx.send(embed=embed)

