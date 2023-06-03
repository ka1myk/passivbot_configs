# how to start apollo
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
git clone apollo and futuresboard, install all requirements 
~~~
cd && git clone https://github.com/ka1myk/apollo.git && cd apollo && pip3 install -r requirements.txt &&
cd && git clone https://github.com/ecoppen/futuresboard.git && cd futuresboard && python3 -m pip install . && mv config/config.json.example config/config.json
~~~
setup crontab (type: crontab -e, ctrl+c, ctrl+v, ctrl+s, ctrl+x):
~~~
shell=/bin/bash path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:/usr/local/bin/futuresboard
@reboot sleep 10; tmuxp load /root/apollo/session.yaml

1,16,31,46                      * * * * cd /root/apollo && python3 helper.py --function open && cd /root/apollo && python3 helper.py --function close
4-15/2,19-30/2,34-45/2,49-58/2  * * * * cd /root/apollo && python3 helper.py --function close
59                              * * * * cd /root/apollo && python3 helper.py --function transfer
~~~