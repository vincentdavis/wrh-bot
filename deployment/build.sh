#!/bin/sh

docker build -t wrh-bot-image:prd -f Dockerfile .
if [ `echo $?` == 0 ]; then
	docker rm -f zp-results
	docker run -dt --restart=always -p 8003:8003 --name wrh-bot wrh-bot-image:prd
fi