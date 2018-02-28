from azure.storage.blob import BlockBlobService
import json
import yaml
import logging
import argparse

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

        generator = block_blob_service.list_blobs(config.STORAGE_CONTAINER)
        for blob in generator:
            print(blob.name)
            try:
                data = json.load(block_blob_service.get_blob_to_text(config.STORAGE_CONTAINER, blob.name))
                self.schema.validate(data, blob.name[:4])
                with open(DYNAMIC_FILES_LOCAL_PATH + blob.name, 'w+') as file:
                    file.write(json.dumps(data))
            except json.decoder.JSONDecodeError:
                self.logger.critical("Error loading JSON data from %s", filename)            
            except jsonschema.exceptions.ValidationError as e:
                self.logger.critical("Syntax error parsing %s: %s", filename, e.message)                
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