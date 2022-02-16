import logging
import typing

import discord
from asgiref.sync import sync_to_async
from discord.ext import commands
from whois.models import WRHDiscordMap

class WhoisCog(commands.Cog, name='Zwift player commands'):

    def __init__(self, bot, logger=None):
        self.bot = bot
        self.logger = logger or logging.getLogger("ZwiftPlayerCog")

    @commands.guild_only()
    @commands.command(help='assign a zwift id to your discord account!')
    async def set(self, ctx, zwid: int):
        await self._set(ctx, zwid)

    async def _set(self, ctx, zwid: int, member: discord.Member = None):
        user_id = (member or ctx.author).id
        guild_id = ctx.guild.id
        obj, _ = await sync_to_async(WRHDiscordMap.objects.update_or_create)(
            defaults={'zwift_id': zwid}, discord_id=user_id, guild_id=guild_id)
        desc = f'**{zwid}** zwift id assigned to {obj.discord_mention}.'
        embed = discord.Embed(description=desc)
        # embed.set_author(name="Go to zwift profile", icon_url=ZWIFT_LOGO_URL,
        #                  url=ZWIFT_PROFILE_URL.format(zwid=zwid))

        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(help='show what zwift id is assigned to a discord account!')
    async def whois(self, ctx, member_or_zwid: typing.Union[discord.Member, int] = None):
        guild_id = ctx.guild.id

        member_or_zwid = member_or_zwid or ctx.author
        print(guild_id, member_or_zwid)
        zwid = None
        if isinstance(member_or_zwid, int):
            zwid = member_or_zwid
            qs = WRHDiscordMap.objects.filter(zwift_id=member_or_zwid, guild_id=guild_id)
        else:
            qs = WRHDiscordMap.objects.filter(discord_id=member_or_zwid.id, guild_id=guild_id)
        # discord_players = [r for r in await sync_to_async(list)(qs)]
        mentions = []
        for discord_player in await sync_to_async(list)(qs):
            zwid = discord_player.zwift_id
            user_id = int(discord_player.discord_id)
            user_display = discord_player.discord_mention
            if user_id == ctx.author.id:
                user_display = f'{user_display} (You)'
            mentions.append(user_display)

        response = embed = None
        if mentions:
            desc = '**{}** zwift id is assigned to {}.'.format(zwid, ', '.join(mentions))
            embed = discord.Embed(description=desc)
            # embed.set_author(name="Go to zwift profile", icon_url=ZWIFT_LOGO_URL,
            #                  url=ZWIFT_PROFILE_URL.format(zwid=zwid))
        elif isinstance(member_or_zwid, int):
            response = f'**{member_or_zwid}** zwift id is not assigned to any memebr!'
        else:
            response = '**No** zwift id is assigned to {}{}!'.format(member_or_zwid.mention,
                                                                     ' (You)' if member_or_zwid == ctx.author else '')
        await ctx.send(response, embed=embed)