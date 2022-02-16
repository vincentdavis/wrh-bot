"""wrh_bot URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import random
import time

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path

import asyncio
from time import sleep
import httpx
from django.http import HttpResponse
import random

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = 'OTQzMTExNTM2Nzk1MzQ5MDAy.YguTEA.4qDsOQflIZ1MQQz62SfDfRbFpWM'
GUILD = 'general'
client = discord.Client()
@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    brooklyn_99_quotes = [
        'I\'m the human form of the 💯 emoji.',
        'Bingpot!',
        (
            'Cool. Cool cool cool cool cool cool cool, '
            'no doubt no doubt no doubt no doubt.'
        ),
    ]

    if message.content == '99':
        response = random.choice(brooklyn_99_quotes)
        await message.channel.send(response)


async def http_call_async():
  for num in range(1,6):
    await asyncio.sleep(1)
    print(num)
  async with httpx.AsyncClient() as client:
    r = await client.get("https://httpbin.org")
    print(r)

async def async_view(request):
  loop = asyncio.get_event_loop()
  loop.create_task(http_call_async())
  return HttpResponse('Non-blocking HTTP request')

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", async_view)
]



