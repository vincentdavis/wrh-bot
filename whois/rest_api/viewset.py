from rest_framework import viewsets
from whois.rest_api import serializers
from whois import models


class WRHDiscordServersView(viewsets.ModelViewSet):
    serializer_class = serializers.WRHDiscordServersSerailizers
    queryset = models.WRHDiscordServers.objects.all()
