FROM debian:11

RUN apt-get update && apt-get -y upgrade \
    && apt-get -y install python3 python-is-python3 python3-pip nano

WORKDIR /opt/CryoEM

COPY requirements.txt scripts/* /opt/CryoEM/

RUN pip3 install -r requirements.txt

CMD [ "/bin/bash", "init.sh" ]
