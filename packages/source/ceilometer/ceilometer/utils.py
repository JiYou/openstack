# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Justin Santa Barbara

# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Utilities and helper functions."""

import calendar
import datetime
import decimal

from ceilometer.openstack.common import timeutils


def recursive_keypairs(d):
    """Generator that produces sequence of keypairs for nested dictionaries.
    """
    for name, value in sorted(d.iteritems()):
        if isinstance(value, dict):
            for subname, subvalue in recursive_keypairs(value):
                yield ('%s:%s' % (name, subname), subvalue)
        elif isinstance(value, (tuple, list)):
            # When doing a pair of JSON encode/decode operations to the tuple,
            # the tuple would become list. So we have to generate the value as
            # list here.
            yield name, list(map(lambda x: unicode(x).encode('utf-8'),
                                 value))
        else:
            yield name, value


def dt_to_decimal(utc):
    """Datetime to Decimal.

    Some databases don't store microseconds in datetime
    so we always store as Decimal unixtime.
    """
    decimal.getcontext().prec = 30
    return decimal.Decimal(str(calendar.timegm(utc.utctimetuple()))) + \
        (decimal.Decimal(str(utc.microsecond)) /
         decimal.Decimal("1000000.0"))


def decimal_to_dt(dec):
    """Return a datetime from Decimal unixtime format.
    """
    if dec is None:
        return None
    integer = int(dec)
    micro = (dec - decimal.Decimal(integer)) * decimal.Decimal(1000000)
    daittyme = datetime.datetime.utcfromtimestamp(integer)
    return daittyme.replace(microsecond=int(round(micro)))


def sanitize_timestamp(timestamp):
    """Return a naive utc datetime object."""
    if not timestamp:
        return timestamp
    if not isinstance(timestamp, datetime.datetime):
        timestamp = timeutils.parse_isotime(timestamp)
    return timeutils.normalize_time(timestamp)
