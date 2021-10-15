FROM alpine:3.14

RUN apk add --update --no-cache python3 nano \
    && ln -sf python3 /usr/bin/python \
    && python3 -m ensurepip \
    && pip3 install --no-cache --upgrade pip

WORKDIR /opt/fs2od

COPY requirements.txt /opt/fs2od/

RUN pip3 install --no-cache -r requirements.txt

COPY init.sh app/* /opt/fs2od/

RUN chmod u+x run-dirs-check.py test.py

CMD [ "/bin/sh", "init.sh" ]
