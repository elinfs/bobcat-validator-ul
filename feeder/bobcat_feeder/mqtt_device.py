from typing import Dict, List, Optional, Tuple
from types import CoroutineType, FunctionType
import functools
import json
import pynmea2

from datetime import datetime
from hbmqtt.client import MQTTClient, ClientException, ConnectException
from hbmqtt.mqtt.constants import QOS_0, QOS_1, QOS_2
from . import dispatcher
from .base_device import BaseDevice
from .data_packet import DataPacket

OPTIONAL_STATUS_KEYS = ['eventQueueLength', 'statusMessageTerse', 'statusMessageVerbose']

class MQTTDevice(BaseDevice):

    def __init__(self, config: Dict, dispatcher: 'dispatcher.Dispatcher') -> None:
        BaseDevice.__init__(self, config, dispatcher)        
        self.topic_func = {}  # type: Dict[str, List[Tuple[List[FunctionType], FunctionType]]]
        self.topic_subscribe = []  # type: List[Tuple[str, int]]
        if 'input' in config:
            for input_channel, input_config in config['input'].items():
                topic = input_config.get('topic')
                if topic:
                    func = functools.partial(DataPacket.create_data_packet,
                                             format=input_config.get('format', 'bytes'),
                                             output=input_config.get('output'))
                    qos = input_config.get('qos', QOS_1)
                    if topic in self.topic_func:
                        for s_topic, s_qos in self.topic_subscribe:
                            if s_topic == topic and s_qos != qos:
                                self.logger.error("Can not subscribe to same topic with different QoS, %s, %d != %d",
                                                  topic, s_qos, qos)
                    else:
                        self.topic_func[topic] = []
                        self.topic_subscribe.append((topic, qos))
                    self.topic_func[topic].append((self.get_channel_functions(input_channel), func))  # type: ignore
                else:
                    msg = "MQTT topic missing for: mqtt/input/{}".format(input_channel)
                    self.logger.error(msg)
        else:
            self.logger.debug('No MQTT input channels')
        if 'output' in config:
            for output_channel, output_config in config['output'].items():
                if 'topic' not in output_config:
                    self.logger.error("MQTT topic missing for: mqtt/output/%s", output_channel)
                self.register_channel_function(output_channel, output_config)
        else:
            self.logger.debug('No MQTT output channels')
        self.mqtt = None  # type: MQTTClient

    async def run(self) -> None:
        """Device message receive loop"""
        mqtt_server = self.config['server']
        mqtt_config = self.get_mqtt_config()
        while not self.done:
            try:
                self.mqtt = MQTTClient(config=mqtt_config)
                cret = await self.mqtt.connect(mqtt_server)
                self.logger.debug("Validate listener MQTT connect to %s -> %s", mqtt_server, cret)
                sret = await self.mqtt.subscribe(self.topic_subscribe)
                self.logger.debug("Validate listener subscribed to MQTT topics %s -> %s", self.topic_subscribe, sret)
                while not self.done:
                    message = await self.mqtt.deliver_message()
                    topic = message.topic
                    for input_funcs, packet_func in self.topic_func[topic]:
                        for input_func in input_funcs:
                            task = None
                            try:
                                task = self.call_channel(input_func, packet_func(message.data))
                            except Exception as e:
                                self.logger.error("call to %s failed", input_func, exc_info=e)
                            if task:
                                self.loop.create_task(task)
                                self.logger.info("Got topic %s, task %s scheduled", topic, input_func)
            except ConnectException:
                self.logger.error("MQTT client failed to connect to %s", mqtt_server)
            except (ClientException, Exception) as ce:
                self.logger.error("MQTT client connected to %s failed", mqtt_server, exc_info=ce)
                if self.mqtt:
                    mqtt = self.mqtt
                    self.mqtt = None
                    await mqtt.disconnect()

    def get_qos(self, channel: str):
        qos = self.config['output'][channel].get('qos', 1)
        if qos == 0:
            return QOS_0
        elif qos == 1:
            return QOS_1
        elif qos == 2:
            return QOS_2
        else:
            raise RuntimeError("channel_{} illegal QoS setting: {}".format(channel, qos))

 
    def channel_mqtt_gps(self, data: DataPacket, dispatcher: 'dispatcher.Dispatcher', config: Dict) -> CoroutineType:
        if data.format == 'nmea_string':
            res = data.data
        else:
            raise RuntimeError("channel_mqtt_gps: Unknown input format: {}".format(data.format))
        self.logger.debug("gps message published: %s", res)
        output_format = self.config['output']['mqtt_gps']['format']
        if output_format == "json":
            out = json.dumps(res).encode()
        elif output_format == "protobuf":
            raise RuntimeError("channel_mqtt_gps: protobuf mqtt_gps output format not supported")
        else:
            raise RuntimeError("channel_mqtt_gps: Unknown output format: {}".format(output_format))
        qos = self.get_qos('mqtt_gps')
        return self.mqtt.publish(self.config['output']['mqtt_gps']['topic'], out, qos=qos)

    def channel_mqtt_time(self, data: DataPacket, dispatcher: 'dispatcher.Dispatcher', config: Dict) -> CoroutineType:
        if data.format == 'nmea_string':
            #convert gps to time iso8602
            nmeastring = pynmea2.parse(data.data)
            res = datetime.combine(nmeastring.datestamp, nmeastring.timestamp).strftime('%Y%m%dT%H%M%SZ')            
        else:
            raise RuntimeError("channel_mqtt_time: Unknown input format: {}".format(data.format))
        self.logger.debug("time message published: %s", res)
        output_format = self.config['output']['mqtt_time']['format']
        if output_format == "json":
            out = json.dumps(res).encode()
        elif output_format == "protobuf":
            raise RuntimeError("channel_mqtt_time: protobuf mqtt_time output format not supported")
        else:
            raise RuntimeError("channel_mqtt_time: Unknown output format: {}".format(output_format))
        qos = self.get_qos('mqtt_time')
        return self.mqtt.publish(self.config['output']['mqtt_time']['topic'], out, qos=qos)

    def channel_mqtt_journey(self, data: DataPacket, dispatcher: 'dispatcher.Dispatcher', config: Dict) -> CoroutineType:
        if data.format == 'str':
            res = data.data
        else:
            raise RuntimeError("channel_mqtt_journey: Unknown input format: {}".format(data.format))
        self.logger.debug("journey message published: %s", res)
        output_format = self.config['output']['mqtt_journey']['format']
        if output_format == "json":
            out = json.dumps(res).encode()
        elif output_format == "protobuf":
            raise RuntimeError("channel_mqtt_journey: protobuf mqtt_journey output format not supported")
        else:
            raise RuntimeError("channel_mqtt_journey: Unknown output format: {}".format(output_format))
        qos = self.get_qos('mqtt_journey')
        return self.mqtt.publish(self.config['output']['mqtt_journey']['topic'], out, qos=qos)

    def channel_mqtt_next_stop(self, data: DataPacket, dispatcher: 'dispatcher.Dispatcher', config: Dict) -> CoroutineType:
        if data.format == 'str':
            res = data.data
        else:
            raise RuntimeError("channel_mqtt_next_stop: Unknown input format: {}".format(data.format))
        self.logger.debug("next_stop message published: %s", res)
        output_format = self.config['output']['mqtt_next_stop']['format']
        if output_format == "json":
            out = json.dumps(res).encode()
        elif output_format == "protobuf":
            raise RuntimeError("channel_mqtt_next_stop: protobuf mqtt_next_stop output format not supported")
        else:
            raise RuntimeError("channel_mqtt_next_stop: Unknown output format: {}".format(output_format))
        qos = self.get_qos('mqtt_next_stop')
        return self.mqtt.publish(self.config['output']['mqtt_next_stop']['topic'], out, qos=qos)
    def channel_mqtt_last_stop(self, data: DataPacket, dispatcher: 'dispatcher.Dispatcher', config: Dict) -> CoroutineType:
        if data.format == 'str':
            res = data.data
        else:
            raise RuntimeError("channel_mqtt_last_stop: Unknown input format: {}".format(data.format))
        self.logger.debug("last_stop message published: %s", res)
        output_format = self.config['output']['mqtt_last_stop']['format']
        if output_format == "json":
            out = json.dumps(res).encode()
        elif output_format == "protobuf":
            raise RuntimeError("channel_mqtt_last_stop: protobuf mqtt_last_stop output format not supported")
        else:
            raise RuntimeError("channel_mqtt_last_stop: Unknown output format: {}".format(output_format))
        qos = self.get_qos('mqtt_last_stop')
        return self.mqtt.publish(self.config['output']['mqtt_last_stop']['topic'], out, qos=qos)
    
    def get_mqtt_config(self) -> dict:
        """Get MQTT client configuration"""
        mqtt_config = self.config.get('config', {}).copy()
        if 'will' in mqtt_config:
            if 'message' not in mqtt_config['will']:
                mqtt_config['will']['message'] = self.get_default_will().encode()
            else:
                mqtt_config['will']['message'] = mqtt_config['will']['message'].encode()
        self.logger.debug("MQTT Client configuration: %s", mqtt_config)
        return mqtt_config

    def get_default_will(self) -> str:
        """Get default will"""
        message = {            
            'ready': False,
            'statusMessageTerse': "Offline"
        }
        return json.dumps(message)
