# -*- encoding: utf-8 -*-
#
# Copyright © 2013 New Dream Network, LLC (DreamHost)
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
"""Model classes for use in the storage API.
"""


class Model(object):
    """Base class for storage API models.
    """

    def __init__(self, **kwds):
        self.fields = list(kwds)
        for k, v in kwds.iteritems():
            setattr(self, k, v)

    def as_dict(self):
        d = {}
        for f in self.fields:
            v = getattr(self, f)
            if isinstance(v, Model):
                v = v.as_dict()
            elif isinstance(v, list) and v and isinstance(v[0], Model):
                v = [sub.as_dict() for sub in v]
            d[f] = v
        return d

    def __eq__(self, other):
        return self.as_dict() == other.as_dict()


class Event(Model):
    """A raw event from the source system. Events have Traits.

       Metrics will be derived from one or more Events.
    """
    def __init__(self, event_name, generated, traits):
        """Create a new event.

        :param event_name:  Name of the event.
        :param generated:   UTC time for when the event occured.
        :param traits:      list of Traits on this Event.
        """
        Model.__init__(self, event_name=event_name, generated=generated,
                       traits=traits)

    def append_trait(self, trait_model):
        self.traits.append(trait_model)

    def __repr__(self):
        trait_list = [str(trait) for trait in self.traits]
        return "<Event: %s, %s %s>" % \
            (self.event_name, self.generated, " ".join(trait_list))


class Trait(Model):
    """A Trait is a key/value pair of data on an Event. The value is variant
    record of basic data types (int, date, float, etc).
    """

    TEXT_TYPE = 1
    INT_TYPE = 2
    FLOAT_TYPE = 3
    DATETIME_TYPE = 4

    def __init__(self, name, dtype, value):
        Model.__init__(self, name=name, dtype=dtype, value=value)

    def __repr__(self):
        return "<Trait: %s %d %s>" % (self.name, self.dtype, self.value)


class Resource(Model):
    """Something for which sample data has been collected.
    """

    def __init__(self, resource_id, project_id, source, user_id, metadata,
                 meter):
        """Create a new resource.

        :param resource_id: UUID of the resource
        :param project_id:  UUID of project owning the resource
        :param source:      the identifier for the user/project id definition
        :param user_id:     UUID of user owning the resource
        :param metadata:    most current metadata for the resource (a dict)
        :param meter:       list of the meters reporting data for the resource,
        """
        Model.__init__(self,
                       resource_id=resource_id,
                       project_id=project_id,
                       source=source,
                       user_id=user_id,
                       metadata=metadata,
                       meter=meter,
                       )


class ResourceMeter(Model):
    """The definitions of the meters for which data has been collected
    for a resource.

    See Resource.meter field.
    """

    def __init__(self, counter_name, counter_type, counter_unit):
        """Create a new resource meter.

        :param counter_name: the name of the counter updating the resource
        :param counter_type: one of gauge, delta, cumulative
        :param counter_unit: official units name for the sample data
        """
        Model.__init__(self,
                       counter_name=counter_name,
                       counter_type=counter_type,
                       counter_unit=counter_unit,
                       )


class Meter(Model):
    """Definition of a meter for which sample data has been collected.
    """

    def __init__(self, name, type, unit, resource_id, project_id, source,
                 user_id):
        """Create a new meter.

        :param name: name of the meter
        :param type: type of the meter (guage, counter)
        :param unit: unit of the meter
        :param resource_id: UUID of the resource
        :param project_id: UUID of project owning the resource
        :param source: the identifier for the user/project id definition
        :param user_id: UUID of user owning the resource
        """
        Model.__init__(self,
                       name=name,
                       type=type,
                       unit=unit,
                       resource_id=resource_id,
                       project_id=project_id,
                       source=source,
                       user_id=user_id,
                       )


class Sample(Model):
    """One collected data point.
    """
    def __init__(self,
                 source,
                 counter_name, counter_type, counter_unit, counter_volume,
                 user_id, project_id, resource_id,
                 timestamp, resource_metadata,
                 message_id,
                 message_signature,
                 ):
        """Create a new sample.

        :param source: the identifier for the user/project id definition
        :param counter_name: the name of the measurement being taken
        :param counter_type: the type of the measurement
        :param counter_unit: the units for the measurement
        :param counter_volume: the measured value
        :param user_id: the user that triggered the measurement
        :param project_id: the project that owns the resource
        :param resource_id: the thing on which the measurement was taken
        :param timestamp: the time of the measurement
        :param resource_metadata: extra details about the resource
        :param message_id: a message identifier
        :param message_signature: a hash created from the rest of the
                                  message data
        """
        Model.__init__(self,
                       source=source,
                       counter_name=counter_name,
                       counter_type=counter_type,
                       counter_unit=counter_unit,
                       counter_volume=counter_volume,
                       user_id=user_id,
                       project_id=project_id,
                       resource_id=resource_id,
                       timestamp=timestamp,
                       resource_metadata=resource_metadata,
                       message_id=message_id,
                       message_signature=message_signature)


class Statistics(Model):
    """Computed statistics based on a set of sample data.
    """
    def __init__(self,
                 min, max, avg, sum, count,
                 period, period_start, period_end,
                 duration, duration_start, duration_end):
        """Create a new statistics object.

        :param min: The smallest volume found
        :param max: The largest volume found
        :param avg: The average of all volumes found
        :param sum: The total of all volumes found
        :param count: The number of samples found
        :param period: The length of the time range covered by these stats
        :param period_start: The timestamp for the start of the period
        :param period_end: The timestamp for the end of the period
        :param duration: The total time for the matching samples
        :param duration_start: The earliest time for the matching samples
        :param duration_end: The latest time for the matching samples
        """
        Model.__init__(self,
                       min=min, max=max, avg=avg, sum=sum, count=count,
                       period=period, period_start=period_start,
                       period_end=period_end, duration=duration,
                       duration_start=duration_start,
                       duration_end=duration_end)


class Alarm(Model):
    ALARM_INSUFFICIENT_DATA = 'insufficient data'
    ALARM_OK = 'ok'
    ALARM_ALARM = 'alarm'
    """
    An alarm to monitor.

    :param alarm_id: UUID of the alarm
    :param name: The Alarm name
    :param description: User friendly description of the alarm
    :param enabled: Is the alarm enabled
    :param state: Alarm state (alarm/nodata/ok)
    :param counter_name: The counter that the alarm is based on
    :param comparison_operator: How to compare the samples and the threshold
    :param threshold: the value to compare to the samples
    :param statistic: the function from Statistic (min/max/avg/count)
    :param user_id: the owner/creator of the alarm
    :param project_id: the project_id of the creator
    :param evaluation_periods: the number of periods
    :param period: the time period in seconds
    :param timestamp: the timestamp when the alarm was last updated
    :param state_timestamp: the timestamp of the last state change
    :param ok_actions: the list of webhooks to call when entering the ok state
    :param alarm_actions: the list of webhooks to call when entering the
                          alarm state
    :param insufficient_data_actions: the list of webhooks to call when
                                      entering the insufficient data state
    :param matching_metadata: the key/values of metadata to match on.
    """
    def __init__(self, name, counter_name,
                 comparison_operator, threshold, statistic,
                 user_id, project_id,
                 evaluation_periods=1,
                 period=60,
                 alarm_id=None,
                 enabled=True,
                 description='',
                 timestamp=None,
                 state=ALARM_INSUFFICIENT_DATA,
                 state_timestamp=None,
                 ok_actions=[],
                 alarm_actions=[],
                 insufficient_data_actions=[],
                 matching_metadata={}
                 ):
        if not description:
            # make a nice user friendly description by default
            description = 'Alarm when %s is %s a %s of %s over %s seconds' % (
                counter_name, comparison_operator,
                statistic, threshold, period)

        Model.__init__(
            self,
            alarm_id=alarm_id,
            enabled=enabled,
            name=name,
            description=description,
            timestamp=timestamp,
            counter_name=counter_name,
            user_id=user_id,
            project_id=project_id,
            comparison_operator=comparison_operator,
            threshold=threshold,
            statistic=statistic,
            evaluation_periods=evaluation_periods,
            period=period,
            state=state,
            state_timestamp=state_timestamp,
            ok_actions=ok_actions,
            alarm_actions=alarm_actions,
            insufficient_data_actions=
            insufficient_data_actions,
            matching_metadata=matching_metadata)
