from django.db import models

# Create your models here.
from django.db.models import JSONField


class WRHDiscordMap(models.Model):
    """
    Have user to zwift_id map
    """
    zwift_id = models.IntegerField()  # Zwift id
    discord_id = models.CharField(max_length=32)  # Discord Id
    guild_id = models.CharField(max_length=20)  # Discord server Id
    datetime = models.DateTimeField(auto_now=True)  # Date Time created

    class Meta:
        unique_together = (('guild_id', 'discord_id'),)

    @property
    def discord_mention(self):
        return f'<@!{self.discord_id}>'

    def __str__(self):
        return f'{self.zwift_id}{self.discord_mention}'


class WRHDiscordServers(models.Model):
    """
    Stores all the connected Discord server information
    """
    guild_id = models.CharField(max_length=20)  # Discord Guild ID
    guild_name = models.CharField(max_length=50)  # Discord server name
    team_id = models.CharField(max_length=20)  # Team Id for the discord server
    results = models.BooleanField()
    filters = JSONField()
    # team_result_channel = models.CharField(max_length=200)  # All result goes to this channel

# class ConfigManager(models.Model):
#     """
#     Config Manager to store all the confiruation
#     """
#     name = models.CharField(max_length=200)  # Name of the Configuration
#     value = models.CharField(max_length=200)  # Value of the configuration


class ZwiftTeamResult(models.Model):
    """
    Zwift Team Result Cache -> For Duplicare
    """
    zwift_team_id = models.IntegerField()
    data = models.JSONField()
    datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.zwift_team_id)
