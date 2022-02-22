import csv
import io
import logging
import typing

import discord
from asgiref.sync import sync_to_async
from discord.ext import commands

from bot.utils import to_dict
from whois import admin
from whois.models import WRHDiscordMap, WRHDiscordServers
ZWIFT_EVENT_URL = "https://zwiftpower.com/events.php?zid={zid}"
ZWIFT_LOGO_URL = "https://zwiftpower.com/zp_logo.png"
ZWIFT_PROFILE_URL = "https://www.zwiftpower.com/profile.php?z={zwid}"


class WhoisCog(commands.Cog, name='We Race Here player commands'):

    def __init__(self, bot, logger=None):
        self.bot = bot
        self.logger = logger or logging.getLogger("ZwiftPlayerCog")

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.group(pass_context=True, name='admin', help='We Race Here player admin commands')
    async def admin(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('```fix\nInvalid zw admin command passed!\ntype "!zw help admin" command for more info\n```')

    @admin.command(help='connect current guild to a discordbots.weracehere.org')
    async def connect(self, ctx):
        guild_id = ctx.guild.id
        guild_name = ctx.message.guild.name
        print(guild_id)
        obj, _ = await sync_to_async(WRHDiscordServers.objects.update_or_create)(guild_id=guild_id,guild_name=guild_name)
        desc = f'**{guild_name}** connected to  discordbots.weracehere.org.'
        embed = discord.Embed(description=desc)

        await ctx.send(embed=embed)
    @commands.guild_only()
    @commands.command(help='assign a zwift id to your discord account!')
    async def set(self, ctx, zwid: int):
        await self._set(ctx, zwid)

    async def _set(self, ctx, zwid: int, member: discord.Member = None):
        user_id = (member or ctx.author).id
        guild_id = ctx.guild.id
        print(guild_id)
        obj, _ = await sync_to_async(WRHDiscordMap.objects.update_or_create)(
            defaults={'zwift_id': zwid}, discord_id=user_id, guild_id=guild_id)
        desc = f'**{zwid}** zwift id assigned to {obj.discord_mention}.'
        embed = discord.Embed(description=desc)
        embed.set_author(name="Go to zwift profile", icon_url=ZWIFT_LOGO_URL,
                         url=ZWIFT_PROFILE_URL.format(zwid=zwid))

        await ctx.send(embed=embed)

    @admin.command(name='set', help='assign a zwift id to a discord account!')
    async def admin_set(self, ctx, zwid: int, member: discord.Member):
        await self._set(ctx, zwid, member=member)

    @admin.command(name='clear', help='unassign a zwift id from a discord account!')
    async def admin_clear(self, ctx, member: discord.Member):
        await self._clear(ctx, member=member)

    async def _clear(self, ctx, member: discord.Member = None):
        user_id = (member or ctx.author).id
        guild_id = ctx.guild.id
        obj = await sync_to_async(WRHDiscordMap.objects.filter(discord_id=user_id, guild_id=guild_id).first)()
        if not obj:
            response = 'No zwift id is assigned to {}!'.format('You' if member is None else member.mention)
        else:
            response = f'**{obj.zwift_id}** zwift id unassigned from {obj.discord_mention}{" (You)" if member is None else ""}!'
            await sync_to_async(obj.delete)()
        await ctx.send(response)


    @admin.command(help='get members list of current guild!')
    async def members(self, ctx, type='csv'):
        guild_id = ctx.guild.id
        csvfile = io.StringIO()
        fields = ['discord_id', 'zwid_assigned', 'name', 'discriminator', 'nick', 'bot', 'joined_at']
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        rows = []
        async for m in ctx.guild.fetch_members(limit=None):
            row = to_dict(m, fields=fields, fields_map={
                'discord_id': lambda: str(m.id)
            })
            rows.append(row)

        ids = [r['discord_id'] for r in rows]
        zwift_assigns = {
            r.discord_id: r.zwift_id for r in await sync_to_async(list)(
                WRHDiscordMap.objects.filter(guild_id=guild_id, discord_id__in=ids))
        }

        for r in rows:
            r['zwid_assigned'] = zwift_assigns.get(r['discord_id'])

        writer.writerows(rows)
        csvfile.seek(0)
        await ctx.author.send(f'all members of "{ctx.guild}" guild:',
                              file=discord.File(fp=csvfile, filename='members.csv'))
        await ctx.send(f'list of members sent to {ctx.author.mention}(You) via direct message!')
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
            embed.set_author(name="Go to zwift profile", icon_url=ZWIFT_LOGO_URL,
                             url=ZWIFT_PROFILE_URL.format(zwid=zwid))
        elif isinstance(member_or_zwid, int):
            response = f'**{member_or_zwid}** zwift id is not assigned to any memebr!'
        else:
            response = '**No** zwift id is assigned to {}{}!'.format(member_or_zwid.mention,
                                                                     ' (You)' if member_or_zwid == ctx.author else '')
        await ctx.send(response, embed=embed)