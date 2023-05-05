# apollo how to start
install order:
~~~
apt-get update &&
apt-get upgrade &&
apt-get install git &&
apt-get install systemd-timesyncd &&
apt-get install python3-pip &&
apt-get install tmuxp &&
apt-get install fail2ban
~~~
git clone apollo, requirements and futuresboard
~~~
cd && git clone https://github.com/ka1myk/apollo.git && cd apollo && pip3 install -r requirements.txt &&
cd && git clone https://github.com/ecoppen/futuresboard.git && cd futuresboard && python3 -m pip install . && mv config/config.json.example config/config.json
~~~
crontab (type: crontab -e):
~~~
shell=/bin/bash path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:/usr/local/bin/futuresboard
@reboot sleep 10; tmuxp load /root/apollo/session.yaml

1       * * * * cd /root/apollo && python3 fill.py && python3 transfer.py
6-58/5  * * * * cd /root/apollo && python3 open.py
7-59/2  * * * * cd /root/apollo && python3 close.py
~~~