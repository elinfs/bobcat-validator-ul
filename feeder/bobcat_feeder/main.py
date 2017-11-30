from typing import Dict
import argparse
import asyncio
import logging
import json
import pynmea2
import datetime
import pprint
import socket
import aiohttp
from hbmqtt.client import MQTTClient
from hbmqtt.mqtt.constants import QOS_2

def main():
    asyncio.get_event_loop().run_until_complete(run())

async def run():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 10110))
    while true:
        rawGpsData = client_socket.recv(4096)
        data = get_mqtt_data(rawGpsData)        
        
        await send_realtime("127.0.0.1", data)
        await asyncio.sleep(5)

def get_gps_data(data: str):
    data = data[data.find('$GPRMC'):]
    strArr = data.split('\\')
    print(strArr[0])
    return strData[0]

def get_mqtt_data(rawGps: str):
    data = {}

    data['/service/v1/gps/rmc'] = get_gps_data(rawGps)

    time = {
            'iso8601': datetime.utcnow()
    }

    data["/service/v1/Validate/time"] = json.dumps(time)

    journey = {
            'line': '2te'
    }

    data["/service/v1/journey"] = json.dumps(journey)

    stop = {
        'GIDHpl': '2037'
    }

    data["/service/v1/lastStop"] = json.dumps(stop)    

    next = {
        'GIDHpl': '2038'
    }

    data["/service/v1/nextStop"] = json.dumps(next)        


async def send_realtime(server: str, data: Dict):
    mqtt = MQTTClient()
    ret = await mqtt.connect(server)
    logging.debug("MQTT connect to {} -> {}".format(server, ret))
    for topic, msg in data.items():
        ret = await mqtt.publish(topic, msg.encode())
        logging.debug("Published to MQTT topic {} -> {}".format(topic, ret))
    await mqtt.disconnect()

if __name__ == "__main__":
    main()