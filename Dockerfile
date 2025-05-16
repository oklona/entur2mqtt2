FROM python:latest

RUN mkdir /entur2mqtt
COPY entur2mqtt.py /entur2mqtt

RUN pip install --upgrade pip
RUN pip install requests paho-mqtt

CMD [ "python3", "/entur2mqtt/entur2mqtt.py" ]
