from typing import Dict
import sys
import argparse
import logging
import asyncio
import signal

import Configuration
import Dispatcher

def setup_dispatcher(config: Configuration, loop: asyncio.AbstractEventLoop):
    """Setup dispatcher"""
    dispatcher = Dispatcher(config, loop)
    for service, sconfig in config.service.items():
        logging.debug("Add dispatcher service %s", service)
        dispatcher.add_service(service, sconfig)
    return dispatcher

def main():
    """ Main function"""

    parser = argparse.ArgumentParser(description='Bobcat Feeder')

    parser.add_argument('--config',
                        dest='config',
                        metavar='filename',
                        help='Bobcat Validator configuration file',
                        default='/etc/bobcat/feeder.yaml')
    parser.add_argument('--debug',
                        dest='debug',
                        action='store_true',
                        help="Enable debugging")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    try:
        config = Configuration.create_from_config_file(args.config)
    except Exception as exc:
        logging.critical("Fatal error reading configuration: %s", exc)
        sys.exit(-1)

    loop = asyncio.get_event_loop()

    try:
        dispatcher = setup_dispatcher(config, loop)
    except Exception as exc:
        logging.debug("Dispatcher setup exception: %s", str(exc))
        logging.critical("Fatal error during setup")
        sys.exit(-1)
    dispatcher.run()

if __name__ == "__main__":
    main()