FROM opsbase:latest
MAINTAINER huangyj
COPY sia /root/sia
WORKDIR /root/sia/
RUN yum -y install mysql-connector-python.noarch redis.x86_64\
    && mkdir -p /var/log/sia/ \
    && mkdir -p /usr/share/fonts/monaco/ \
    && mkdir /etc/ops_sia/ \
    && cp /root/sia/Monaco.ttf /usr/share/fonts/monaco/Monaco.ttf \
#    && cp etc/ops_sia.conf /etc/ops_sia/ \
    && pip install -r requirements.txt \
    && echo -e "python /root/sia/bin/sia_api" > /root/start.sh
CMD sh /root/start.sh