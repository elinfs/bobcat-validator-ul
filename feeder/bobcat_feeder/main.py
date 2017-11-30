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
    mqtt = MQTTClient()
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('192.168.1.3', 10110))
    serversocket.listen(5) # become a server socket, maximum 5 connections
    while True:
        print('loop')
        connection, address = serversocket.accept()
        print(address)
        rawGpsData = connection.recv(4096)
        data = get_mqtt_data(rawGpsData)        
        connection.close()
        await send_realtime(mqtt, "mqtt://127.0.0.1", data)
        await asyncio.sleep(5)

def get_gps_data(data: bytes):    
    datastring = str(data)
    print(datastring)
    datastring = datastring[datastring.find('$GPRMC'):]
    strArr = datastring.split('\\r\\n')
    print(strArr[0])
    return strArr[0]

def get_mqtt_data(rawGps: str):
    data = {}

    data['/service/v1/gps/rmc'] = get_gps_data(rawGps)

    time = {
            'iso8601': datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
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

    return data

async def send_realtime(mqtt, server: str, data: Dict):
    
    ret = await mqtt.connect(server)
    logging.debug("MQTT connect to {} -> {}".format(server, ret))
    print(str(data))
    for topic, msg in data.items():
        ret = await mqtt.publish(topic, msg.encode())
        logging.debug("Published to MQTT topic {} -> {}".format(topic, ret))
    await mqtt.disconnect()

if __name__ == "__main__":
    main()