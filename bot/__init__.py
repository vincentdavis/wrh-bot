import asyncio
import logging

import discord
from discord.ext import commands

# from helpers.shortcuts import get_pyredisrpc_server


rpc_server = None


class ZwiftBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redisrpc_sleep = kwargs.pop('redisrpc_sleep', None) or 0.1
        self.skip_redisrpc_server = kwargs.pop('skip_redisrpc_server', False)
        self.logger = kwargs.pop('logger', None) or logging.getLogger('ZwiftBot')
        # if not rpc_server.logger:
        #     rpc_server.logger = self.logger

    async def run_redisrpc_server(self):
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                pass
                # await rpc_server.pull_method()
            except Exception:
                self.logger.exception('Unexpected Error!')
            await asyncio.sleep(self.redisrpc_sleep)

    async def on_ready(self):
        self.logger.info(f'{self.user.name} has connected to Discord!')
        if not self.skip_redisrpc_server:
            self.redisrpc_server_task = self.loop.create_task(self.run_redisrpc_server())

    async def on_member_join(self, member):
        self.logger.info(f'{member} joined!')

    async def on_member_remove(self, member):
        self.logger.info(f'{member} left!')

    async def on_command_error(self, ctx, error):
        self.logger.error(error)

        if isinstance(error, commands.errors.CommandNotFound):
            response = '```fix\n{}\ntype "{}help" command to see the commands list```'.format(error,
                                                                                              self.command_prefix)
        elif isinstance(error, (commands.errors.CommandError, commands.errors.CheckFailure)):
            response = '```fix\n{}\n```'.format(error)
        else:
            response = '```fix\nUnknown error:\n{}\n```'.format(error)
        await ctx.send(response)




