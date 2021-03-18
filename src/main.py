#!/usr/bin/env python3
import argparse
import asyncio

import consumer
import db.init
import producer

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', required=True, choices=['consumer', 'producer', 'init'])

    arguments, _ = parser.parse_known_args()

    module_mapping = {
        'producer': producer,
        'consumer': consumer,
        'init': db.init
    }

    module = module_mapping[arguments.mode]
    subparser = module.configure_parser(parser)
    parsed = subparser.parse_args()
    asyncio.get_event_loop().run_until_complete(module.main(parsed))
