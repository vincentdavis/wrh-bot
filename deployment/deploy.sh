#!/bin/bash
git clone https://github.com/we-race-here/wrh-bot.git /home/jenkins/wrh-bot
cd /home/jenkins/wrh-bot
git checkout main
mkdir -p media

sudo cp -rf ../nginx.conf  /etc/nginx/nginx.conf
sudo cp -rf ../default.conf  /etc/nginx/sites-available/default
cp ../.env /home/jenkins/wrh-bot/wrh_bot/
pip install uwsgi
#python manage.py collectstatic
python manage.py makemigrations
python manage.py migrate

# Restart nginx
sudo /etc/init.d/nginx start || sudo /etc/init.d/nginx start

# Running Celery
#celery -A zp_result worker -l info &
#celery -A zp_result beat &
python manage.py zwift_bot &
#nohup python manage.py whois_bot_start &
# Running Server
uwsgi --socket mysite.sock --module wrh_bot.wsgi --buffer-size=100000 --chmod-socket=666 --master --processes 4 --threads 2