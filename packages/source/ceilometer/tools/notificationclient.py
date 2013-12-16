#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
#
# Author: Doug Hellmann <doug.hellmann@dreamhost.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Command line tool for recording notification messages and replaying
them later.
"""

import argparse
import logging
import cPickle as pickle
import sys

#from nova import utils
from oslo.config import cfg

from ceilometer.openstack.common import rpc

LOG = logging.getLogger(__name__)


def record_messages(connection, topic, output):
    """Listen to notification.info messages and pickle them to output."""
    def process_event(body):
        print ('%s: %s' %
               (body.get('timestamp'),
                body.get('event_type', 'unknown event'),
                ))
        pickle.dump(body, output)

    connection.declare_topic_consumer(topic, process_event)
    try:
        connection.consume()
    except KeyboardInterrupt:
        pass


def monitor_messages(connection, topic):
    """Listen to notification.info messages and print them."""
    def process_event(msg):
        body = msg['args']['data']
        if 'resource_id' in body:
            print ('%s: %s/%-15s: %s' %
                   (body.get('timestamp'),
                    body.get('resource_id'),
                    body.get('event_type'),
                    body.get('counter_volume'),
                    ))
        else:
            print ('%s: %s' %
                   (body.get('timestamp'),
                    body.get('event_type'),
                    ))

    connection.declare_topic_consumer(topic, process_event)
    try:
        connection.consume()
    except KeyboardInterrupt:
        pass


def send_messages(connection, topic, input):
    """Read messages from the input and send them to the AMQP queue."""
    while True:
        try:
            body = pickle.load(input)
        except EOFError:
            break
        print('%s: %s' %
              (body.get('timestamp'),
               body.get('event_type', 'unknown event'),
               ))
        connection.topic_send(topic, body)


def main():
    rpc.register_opts(cfg.CONF)
    cfg.CONF.register_opts([
            cfg.StrOpt('datafile',
                       default=None,
                       help='Data file to read or write',
                       ),
            cfg.BoolOpt('record',
                        help='Record events',
                        ),
            cfg.BoolOpt('replay',
                        help='Replay events',
                        ),
            ])

    remaining_args = cfg.CONF(sys.argv)
    utils.monkey_patch()

    parser = argparse.ArgumentParser(
        description='record or play back notification events',
        )
    parser.add_argument('mode',
                        choices=('record', 'replay', 'monitor'),
                        help='operating mode',
                        )
    parser.add_argument('data_file',
                        default='msgs.dat',
                        nargs='?',
                        help='the data file to read or write',
                        )
    parser.add_argument('--topic',
                        default='notifications.info',
                        help='the exchange topic to listen for',
                        )
    args = parser.parse_args(remaining_args[1:])

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    root_logger = logging.getLogger('')
    root_logger.addHandler(console)
    root_logger.setLevel(logging.DEBUG)

    connection = rpc.create_connection()
    try:
        if args.mode == 'replay':
            with open(args.data_file, 'rb') as input:
                send_messages(connection, args.topic, input)
        elif args.mode == 'record':
            with open(args.data_file, 'wb') as output:
                record_messages(connection, args.topic, output)
        elif args.mode == 'monitor':
            monitor_messages(connection, args.topic)
    finally:
        connection.close()

    return 0

if __name__ == '__main__':
    main()
