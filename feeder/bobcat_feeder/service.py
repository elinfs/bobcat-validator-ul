from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union
from datetime import datetime, timedelta, timezone
import json
import logging
from .protobuf.journey_pb2 import JourneyInfo, Stop
from .data_packet import DataPacket
from . import dispatcher

class Service:
    def __init__(self, config: Dict) -> None:
        self.config = config

    def register_channels(self, dispatcher:'dispatcher.Dispatcher') -> None:
        dispatcher.register_channel_function('service', self.channel_service)

    def channel_service(self, data: DataPacket, dispatcher: 'dispatcher.Dispatcher') -> None:
        """Receive journey information"""
        if data.format == 'json':
            service = json.loads(data.as_str())            
        else:
            raise RuntimeError("Service: Unknown format: {}".format(data.format))
        try:
            self.logger.debug("Got service: %s", service)
            get_route_for_service(data.data)
            dispatcher.do_output(data.outputs, data)
        except KeyError as ke:
            self.logger.error("Missing service data for %s", journey, exc_info=ke)

    def get_route_for_service(self, service: str) -> None:
        self.logger.info("Got route for service: " + service)