import logging

from discord.ext import commands


class BasicCommandBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = kwargs.pop('logger', None) or logging.getLogger('ZwiftBot')

    async def on_ready(self):
        self.logger.info(f'{self.user.name} has connected to Discord!')

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