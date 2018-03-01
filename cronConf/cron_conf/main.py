# -*- encoding: utf-8 -*-
from azure.storage.blob import BlockBlobService
import json
import yaml
import jsonschema
import logging
import argparse
from cron_conf.schema_validator import SchemaValidator

ALL_SCHEMAS = [    
    'blacklists',
    'stops',
    'services',
    'kdk_keyring',
    'issuer_keyring',
    'ticklemacros',
    'participants',
    'products'
]

class CronConf:
    def __init__(self):        
        self.logger = logging.getLogger(__name__).getChild(self.__class__.__name__)
        self.schema = SchemaValidator(ALL_SCHEMAS)

    def run(self):
        try:
            import config 
        except:
            raise ValueError('Please specify configuration settings in config.py.')
        
        block_blob_service = BlockBlobService(account_name=config.STORAGE_ACCOUNT_NAME, account_key=config.STORAGE_ACCOUNT_KEY)

        blobs = block_blob_service.list_blobs(config.STORAGE_CONTAINER)
        for blob in blobs:
            self.logger.debug('Blob name: ' + blob.name)
            try:
                data = block_blob_service.get_blob_to_text(config.STORAGE_CONTAINER, blob.name)
                self.logger.debug('Downloaded file: ' + blob.name)
                self.schema.validate(json.loads(data.content, encoding = 'utf-8'), blob.name[:-5])
                self.logger.debug('Schema is ok for: ' + blob.name)
                with open(config.DYNAMIC_FILES_LOCAL_PATH + blob.name, 'w+', encoding = 'utf-8') as file:
                    file.write(data.content)
                    self.logger.debug('File updated: ' + config.DYNAMIC_FILES_LOCAL_PATH + blob.name)
            except json.decoder.JSONDecodeError:
                self.logger.critical("Error loading JSON data from %s", blob.name)            
            except jsonschema.exceptions.ValidationError as e:
                self.logger.critical("Syntax error parsing %s: %s", blob.name, e.message)                
            except Exception as e:
                self.logger.critical("error reading json blob: " + blob.name + " | exception: " + str(e))

def main():
    parser = argparse.ArgumentParser(description='Cron conf')

    parser.add_argument('--debug',
                        dest='debug',
                        action='store_true',
                        help="Enable debugging")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    cronConf =CronConf()
    cronConf.run()

if __name__ == "__main__":
    main()