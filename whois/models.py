from django.db import models

# Create your models here.


class WRHDiscordMap(models.Model):
    zwift_id = models.IntegerField()
    discord_id = models.CharField(max_length=32)
    guild_id = models.CharField(max_length=20)
    datetime = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('guild_id', 'discord_id'),)

    @property
    def discord_mention(self):
        return f'<@!{self.discord_id}>'

    def __str__(self):
        return f'{self.zwift_id}{self.discord_mention}'
