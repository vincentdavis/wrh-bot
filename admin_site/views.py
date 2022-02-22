from django.contrib.auth import authenticate, login
from django.forms import model_to_dict
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView
from rest_framework import serializers
from whois.models import WRHDiscordServers
from wrh_bot.settings import BotLink


class WRHDiscordServersSerailizers(serializers.ModelSerializer):
    class Meta:
        model = WRHDiscordServers
        fields = '__all__'

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['WRHDiscordServers'] = [dict(i) for i in WRHDiscordServersSerailizers(WRHDiscordServers.objects.all(), many=True).data]
        context['BotLink'] = BotLink
        return context


def user_login(request):
    if request.method == 'POST':
        # Process the request if posted data are available
        username = request.POST['username']
        password = request.POST['password']
        # Check username and password combination if correct
        user = authenticate(username=username, password=password)
        if user is not None:
            # Save session as cookie to login the user
            login(request, user)
            # Success, now let's login the user.

            return HttpResponseRedirect(reverse('admin_site:home'))
        else:
            # Incorrect credentials, let's throw an error to the screen.
            return render(request, 'registration/login-vuetify.html', {'error_message': 'Incorrect username and / or password.'})
    else:
        # No post data availabe, let's just show the page to the user.
        return render(request, 'registration/login-vuetify.html')