#!/bin/sh
sudo docker run -d -p 1238:8080 -v ${PWD}/rent.db:/vol/rent.db -it countingrent
