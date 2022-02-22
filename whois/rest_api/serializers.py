from whois import models
from rest_framework import  serializers


class WRHDiscordServersSerailizers(serializers.ModelSerializer):
    class Meta:
        model = models.WRHDiscordServers
        fields = '__all__'
