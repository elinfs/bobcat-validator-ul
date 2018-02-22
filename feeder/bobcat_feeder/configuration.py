from typing import cast, Any, Dict, List, Union
import os
import sys
import logging
import json
import glob
import jsonschema
from deepmerge import Merger
import yaml

DEFAULT_CONF = '/etc/bobcat/feeder.yaml'

def dict_merge(orig_dict: Dict, new_dict: Dict) -> Dict:
    result = orig_dict.copy()
    MERGER.merge(result, new_dict)
    return result


class Configuration:
    """Bobcat Feeder Configuration"""

    def __init__(self, conf: Dict[str, Any], base_dir: str) -> None:
        self.base_dir = base_dir        

        self.logging = conf.get('logging')
        self.logger = logging.getLogger(__name__).getChild(self.__class__.__name__)
        self.device = conf['device']  # type: Dict[str, Dict]                        
        self.service = conf.get('service', {})
        self.load_external_data()

    def filename(self, file):
        """Add base path to relative file names"""
        return os.path.join(self.base_dir, file)

    def load_external_data(self) -> None:
        """Reload dynamic configuration"""

        # if 'stops_file' in self.realtime:
        #     filename = self.filename(self.realtime['stops_file'])
        #     self.realtime['stops'] = TransportStopCollection(self.read_external_data_list(filename, 'stops'))
        #     self.logger.info("Loaded %d stops from %s",
        #                      self.realtime['stops'].count(),
        #                      self.realtime['stops_file'])

    @classmethod
    def create_from_config_file(cls, filename: str=DEFAULT_CONF):
        """Load configuration as YAML"""
        logging.debug("Reading configuration from %s", filename)
        with open(filename, "rt", encoding='utf-8') as file:
            config_dict = yaml.load(file)
        base_dir = os.path.dirname(filename)
        for pathname in config_dict.get('includes', []):
            logging.debug("Including %s", pathname)
            for filename in glob.glob(pathname, recursive=False):
                logging.debug("Reading partial configuration from %s", filename)
                with open(filename, "rt", encoding='utf-8') as file:
                    data = yaml.load(file)
                    dict_merge(config_dict, data)
        return cls(config_dict, base_dir)