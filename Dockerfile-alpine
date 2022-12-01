FROM alpine:3.16

RUN apk add --update --no-cache python3 gcc musl-dev python3-dev nano \
    && ln -sf python3 /usr/bin/python \
    && python3 -m ensurepip \
    && pip3 install --no-cache --upgrade pip

WORKDIR /opt/fs2od

COPY requirements.txt /opt/fs2od/

RUN pip3 install --no-cache -r requirements.txt

COPY init.sh app/* /opt/fs2od/

RUN chmod u+x fs2od.py \
    && ln -s /opt/fs2od/fs2od.py /usr/bin/fs2od.py

CMD [ "/bin/sh", "init.sh" ]
