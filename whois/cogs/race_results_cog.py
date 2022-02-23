import asyncio
import csv
import datetime
import io
import logging
import random
import re
import time
import typing
from html import unescape

import discord
import requests
from asgiref.sync import sync_to_async
from discord.ext import commands, tasks
from django.contrib.humanize.templatetags.humanize import ordinal
from django.utils import timezone
from django.db import close_old_connections
from firebase_admin import db, auth
from firebase_admin.auth import UserNotFoundError

from whois.models import ZwiftTeamResult, WRHDiscordMap, WRHDiscordServers

from bot.utils import to_dict, zwift_power_get_api_async

ZWIFT_PROFILE_URL = "https://www.zwiftpower.com/profile.php?z={zwid}"
ZWIFT_EVENT_URL = "https://zwiftpower.com/events.php?zid={zid}"
ZWIFT_LOGO_URL = "https://zwiftpower.com/zp_logo.png"
COUNTRY_FLAG_URL = 'https://cdn.staticaly.com/gh/hampusborgos/country-flags/master/png100px/{code}.png'
# TEAM_RESULTS_URL = 'https://zwiftpower.com/api3.php?do=team_results&id={team_id}&_={ts}'
TEAM_RESULTS_URL = 'https://zwiftapi.weracehere.org/team_results?id={team_id}'
TEAM_STAT_URL = 'https://zwiftpower.com/cache3/teams/{team_id}_riders.json?_={ts}'
num_to_team_category = {40: "D", 30: "C", 20: "B", 10: "A", 5: "A+", 0: "E"}


def team_result_category_to_icon(c):
    return f':regional_indicator_{c.lower()}:' if c else c


class RaceResultCog(commands.Cog):
    DISCORD_SLEEP_LOOP = 0.001

    def __init__(self, bot, start_bg_tasks=True, logger=None):
        self.bot = bot
        self.logger = logger or logging.getLogger("RaceResultCog")
        if start_bg_tasks:
            self.show_team_results.start()

    def _result_response(self, r, discord_players):

        cat = r['category']
        pos = ordinal(r['pos'])
        player_name = unescape(r['player_name'])
        player_id = int(r['player_id'])
        event_id = int(r['event_id'])
        flag = r['flag']
        if player_id in discord_players:
            player_name = '{} {}'.format(player_name, discord_players[player_id].discord_mention)
        event_name = unescape(r['event_name'])
        desc = f'{team_result_category_to_icon(cat)} **{player_name}** finished **{pos}**'
        embed = discord.Embed(title=event_name, url=ZWIFT_EVENT_URL.format(zid=event_id), description=desc)
        embed.set_author(name=player_name, url=ZWIFT_PROFILE_URL.format(zwid=player_id),
                         icon_url=COUNTRY_FLAG_URL.format(code=flag))
        return (None, embed)

    async def __send_new_team_result(self, new_results, guild, channel_name, team_id=None):
        if not new_results:
            self.logger.info(f'No new Result on team_id "{team_id}"!')
            return

        channel = discord.utils.get(guild.channels, name=channel_name)
        if not channel:
            self.logger.warning(f'Invalid channel "{channel_name}" on guild "{guild}"')
            return
        self.logger.info(f'Try to send messages to: guild={guild} channel={channel_name}')
        zwids = [r['player_id'] for r in new_results]
        discord_players = {
            r.zwift_id: r for r in await sync_to_async(list)(
                WRHDiscordMap.objects.filter(zwift_id__in=zwids, guild_id=guild.id))
        }

        for r in new_results:
            msg, embed = self._result_response(r, discord_players=discord_players)
            self.logger.info("Sending message[category=%s, player_id=%s]: %s",
                             r['category'], r['player_id'], embed.description)
            await channel.send(msg, embed=embed)

    async def __send_team_result_by_advanced_filters(self, new_results, guild, advanced_filters, team_id=None,server=None):
        print('new_results',new_results)
        if not new_results:
            self.logger.info(f'Advanced filter: No new Result on team_id "{team_id}"!')
            return
        for cfg in (advanced_filters or []):
            channel_name = str(cfg.get('channel_name')).replace(' ', '-')
            channel = channel_name and discord.utils.get(guild.channels, name=channel_name)
            self.logger.info(f'Channel {channel} Not found in {guild.channels}')
            if not channel:
                category = discord.utils.get(guild.categories, name='Text Channels')
                await guild.create_text_channel(channel_name, category=category)
                self.logger.warning(f'Advanced filter: Invalid channel "{channel_name}" on guild "{guild}"')
            channel = channel_name and discord.utils.get(guild.channels, name=channel_name)
            self.logger.info(f'Advanced filter: Try to send messages to: guild={guild} channel={channel_name}')
            category = cfg.get('category')
            event_type = cfg.get('type', [])
            event_pattern = cfg.get('title_filter')
            results = []
            zwids = [r['player_id'] for r in new_results]
            discord_players = {
                r.zwift_id: r for r in await sync_to_async(list)(
                    WRHDiscordMap.objects.filter(zwift_id__in=zwids, guild_id=guild.id))
            }
            event_map = {
                'Races': 'TYPE_RACE'
            }
            for r in new_results:
                cat = r['category']
                f_t = r['f_t']
                if len(category) >=1:
                    if category and ((cat or '').lower() not in [i.lower() for i in category]):
                        continue
                if len(event_type) >=1:
                    if (str(f_t).strip().lower() not in [event_map.get(i).lower() for i in event_type]):
                        continue
                event_name = unescape(r['event_name'])
                if event_pattern and (not re.search(event_pattern, event_name, re.IGNORECASE)):
                    continue
                msg, embed = self._result_response(r, discord_players=discord_players)

                self.logger.info("Advanced filter: Sending message[category=%s,Race Type =%s, player_id=%s]: %s",
                                 cat, f_t, r['player_id'], embed.description)
                await channel.send(msg, embed=embed)

    async def __get_new_team_result(self, team_id):
        self.logger.info(f'Getting new results of team_id={team_id} ...')
        data = await zwift_power_get_api_async(TEAM_RESULTS_URL.format(team_id=team_id))
        events = data['events']
        records = data['data']
        cleaned_records = {}

        for r in records:
            cleaned_records.setdefault(str(r['zid']), {})[str(r.get('zwid'))] = {
                'name': r.get('name'),
                'cat': r.get('category'),
                'flag': r.get('flag'),
                'f_t': r.get('f_t'),
                'ts': (events.get(r['zid']) or {}).get('date'),
                'pos': r.get('pos')
            }

        last_db_records = await sync_to_async(
            ZwiftTeamResult.objects.filter(zwift_team_id=team_id).order_by('id').last)()
        last_db_records = last_db_records and last_db_records.data
        new_results = []
        today = datetime.date.today()
        for event_id, players in cleaned_records.items():
            for player_id, player in players.items():
                player_name = player.pop('name')
                timestamp = player.pop('ts')
                category = player.pop('cat')
                flag = player.pop('flag')
                f_t = player.pop('f_t')
                event_date = datetime.datetime.fromtimestamp(timestamp).date()
                print(event_id, player_id, player_name , event_date, today)
                if (not last_db_records) or (event_date != today):
                    continue
                if (last_db_records.get(event_id) or {}).get(player_id) != player:
                    new_results.append({
                        'player_id': player_id,
                        'event_id': event_id,
                        'player_name': player_name,
                        'datetime': event_date,
                        'category': category,
                        'f_t': f_t,
                        'flag': flag,
                        'event_name': (events.get(event_id) or {}).get('title'),
                        **player
                        })
                else:
                    print("Else block")
        return new_results, cleaned_records

    async def __get_team_stat(self, team_id):
        self.logger.info(f'Getting stats of team_id={team_id} ...')
        data = await zwift_power_get_api_async(TEAM_STAT_URL.format(team_id=team_id, ts=int(time.time() * 1000)))
        records = data['data']

        stats = {f'cat_{c}_size': 0 for c in num_to_team_category.values()}
        stats['team_size'] = len(records)
        for r in records:
            cat = num_to_team_category.get(r["div"])
            if f'cat_{cat}_size' in stats:
                stats[f'cat_{cat}_size'] += 1
        return stats

    async def __update_team_stats(self, guild, team_id, team_stat):
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(create_instant_invite=False, connect=False),
            guild.me.top_role: discord.PermissionOverwrite(view_channel=True, connect=True),
        }
        category_name = '📊 TEAM STATS 📊'
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)
        for c in guild.voice_channels:
            if c.category == category:
                await c.delete()
        await category.edit(position=0)
        discord_members = len(guild.members)
        await guild.create_voice_channel(f'Team#: {team_id}', overwrites=overwrites, category=category)
        await guild.create_voice_channel(f'Discord Members: {discord_members}',
                                         overwrites=overwrites, category=category)
        await guild.create_voice_channel(f'Team Size: {team_stat["team_size"]}', overwrites=overwrites,
                                         category=category)
        team_cats = sorted(num_to_team_category.values())
        for team_cat in team_cats:
            cat_size = team_stat[f'cat_{team_cat}_size']
            await guild.create_voice_channel(f'Category {team_cat} Size: {cat_size}', overwrites=overwrites,
                                             category=category)

    @tasks.loop(minutes=2)
    async def show_team_results(self):
        await self.bot.wait_until_ready()
        close_old_connections()
        # Team and Guid Setup
        self.logger.info("Next show_team_results loop.")
        teams_results_cache = {}
        teams_stats_cache = {}

        servers = await sync_to_async(list)(
                WRHDiscordServers.objects.filter())
        # servers = sync_to_async(WRHDiscordServers.objects.all())
        for server in servers:
            guild_id = int(server.guild_id)
            team_id = int(server.team_id)
            if not team_id:
                pass
            guild = discord.utils.get(self.bot.guilds, id=guild_id)
            if not guild:
                self.logger.warning(f'Invalid guild id "{guild_id}"')
                pass
            self.logger.info(f"*********** Guild: {guild_id} - {guild}", )

            # Channel Creation
            try:
                if team_id in teams_stats_cache:
                    team_stat = teams_stats_cache[team_id]
                else:
                    team_stat = await self.__get_team_stat(team_id)
                    teams_stats_cache[team_id] = team_stat
                await self.__update_team_stats(guild, team_id, team_stat)
            except Exception:
                self.logger.exception('unexpected error!')
                await asyncio.sleep(self.DISCORD_SLEEP_LOOP)

            # Result Processing
            try:
                if team_id in teams_results_cache:
                    new_results, records = teams_results_cache[team_id], None
                else:
                    new_results, records = await self.__get_new_team_result(team_id)
                    teams_results_cache[team_id] = new_results
                    await sync_to_async(ZwiftTeamResult.objects.create)(zwift_team_id=team_id, data=records)

                # channel_name = 'Team Result'
                # if channel_name:
                #     await self.__send_new_team_result(new_results, guild, channel_name, team_id=team_id)
                advanced_filters = server.filters.get('data')
                if advanced_filters:
                    await self.__send_team_result_by_advanced_filters(new_results, guild, advanced_filters,
                                                                      team_id=team_id, server=server)
            except Exception:
                self.logger.exception('unexpected error!')
                await asyncio.sleep(self.DISCORD_SLEEP_LOOP)
                pass

        if records is not None:
            await asyncio.sleep(self.DISCORD_SLEEP_LOOP)

        self.logger.info("Finished!")

    @commands.guild_only()
    @commands.command(help='Get TeamStats')
    async def teamstats(self, ctx, zwid: int):
        await self._teamstats(ctx, zwid)

    async def _teamstats(self, ctx, id: int, member: discord.Member = None):
        result = requests.get(f'https://zwiftapi.weracehere.org/team_riders?id={id}')
        desc = f'No result for **{id}**.'

        if result.status_code == 200:
            try:
                if result.json().get("data", None):
                    result = result.json().get("data", None)
                    D = [i for i in result if i.get('div', '') == 40]
                    C = [i for i in result if i.get('div', '') == 30]
                    B = [i for i in result if i.get('div', '') == 20]
                    A = [i for i in result if i.get('div', '') == 10]
                    Aplus = [i for i in result if i.get('div', '') == 5]
                    E = [i for i in result if i.get('div', '') == 0]
                    desc = f'{len(result)} members \n' \
                           f'{len(D)} D \n' \
                           f'{len(C)} C \n' \
                           f'{len(B)} B \n' \
                           f'{len(A)} A \n' \
                           f'{len(Aplus)} A+ \n' \
                           f'{len(E)} E \n'
            except Exception as e:
                pass
        embed = discord.Embed(description=desc)
        await ctx.send(embed=embed)