from rest_framework.routers import DefaultRouter
from whois.rest_api import viewset
router =  DefaultRouter()
router.register('WRHDiscordServers', viewset.WRHDiscordServersView)