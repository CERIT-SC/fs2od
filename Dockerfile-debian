FROM debian:11-slim

RUN apt-get update && apt-get -y upgrade && apt-get -y install --no-install-recommends \
    python3 \
    python-is-python3 \
    python3-pip \
    nano \
    && pip3 install --no-cache --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/fs2od

COPY requirements.txt /opt/fs2od/

RUN pip3 install --no-cache -r requirements.txt

COPY init.sh app/* /opt/fs2od/

RUN chmod u+x fs2od.py \
    && ln -s /opt/fs2od/fs2od.py /usr/bin/fs2od.py

CMD [ "/bin/bash", "init.sh" ]
