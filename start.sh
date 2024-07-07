#!/bin/bash

CURRENT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

NAME=telegram-bot-where-do-you-sit

docker build gdzie\ siedzisz\ w\ samolocie --tag $NAME

docker stop $NAME
docker rm $NAME

if [ ! -f $CURRENT_DIR/where_do_you_sit.db ]; then
    touch $CURRENT_DIR/where_do_you_sit.db
fi

docker run \
    --detach \
    --restart always \
    --name $NAME \
    --volume $CURRENT_DIR/where_do_you_sit.db:/app/where_do_you_sit.db \
    $NAME
