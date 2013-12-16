# -*- encoding: utf-8 -*-
#
# Author: John Tran <jhtran@att.com>
#         Julien Danjou <julien@danjou.info>
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

"""SQLAlchemy storage backend."""

from __future__ import absolute_import

import operator
import os
import uuid
from sqlalchemy import func

from ceilometer.openstack.common import log
from ceilometer.openstack.common import timeutils
import ceilometer.openstack.common.db.sqlalchemy.session as sqlalchemy_session
from ceilometer.storage import base
from ceilometer.storage import models as api_models
from ceilometer.storage.sqlalchemy import migration
from ceilometer.storage.sqlalchemy.models import Alarm
from ceilometer.storage.sqlalchemy.models import Base
from ceilometer.storage.sqlalchemy.models import Event
from ceilometer.storage.sqlalchemy.models import Meter
from ceilometer.storage.sqlalchemy.models import Project
from ceilometer.storage.sqlalchemy.models import Resource
from ceilometer.storage.sqlalchemy.models import Source
from ceilometer.storage.sqlalchemy.models import Trait
from ceilometer.storage.sqlalchemy.models import UniqueName
from ceilometer.storage.sqlalchemy.models import User
from ceilometer import utils


LOG = log.getLogger(__name__)


class SQLAlchemyStorage(base.StorageEngine):
    """Put the data into a SQLAlchemy database.

    Tables::

        - user
          - { id: user uuid }
        - source
          - { id: source id }
        - project
          - { id: project uuid }
        - meter
          - the raw incoming data
          - { id: meter id
              counter_name: counter name
              user_id: user uuid            (->user.id)
              project_id: project uuid      (->project.id)
              resource_id: resource uuid    (->resource.id)
              resource_metadata: metadata dictionaries
              counter_type: counter type
              counter_unit: counter unit
              counter_volume: counter volume
              timestamp: datetime
              message_signature: message signature
              message_id: message uuid
              }
        - resource
          - the metadata for resources
          - { id: resource uuid
              resource_metadata: metadata dictionaries
              project_id: project uuid      (->project.id)
              user_id: user uuid            (->user.id)
              }
        - sourceassoc
          - the relationships
          - { meter_id: meter id            (->meter.id)
              project_id: project uuid      (->project.id)
              resource_id: resource uuid    (->resource.id)
              user_id: user uuid            (->user.id)
              source_id: source id          (->source.id)
              }
    """

    OPTIONS = []

    def register_opts(self, conf):
        """Register any configuration options used by this engine."""
        conf.register_opts(self.OPTIONS)

    @staticmethod
    def get_connection(conf):
        """Return a Connection instance based on the configuration settings.
        """
        return Connection(conf)


def make_query_from_filter(query, sample_filter, require_meter=True):
    """Return a query dictionary based on the settings in the filter.

    :param filter: SampleFilter instance
    :param require_meter: If true and the filter does not have a meter,
                          raise an error.
    """

    if sample_filter.meter:
        query = query.filter(Meter.counter_name == sample_filter.meter)
    elif require_meter:
        raise RuntimeError('Missing required meter specifier')
    if sample_filter.source:
        query = query.filter(Meter.sources.any(id=sample_filter.source))
    if sample_filter.start:
        ts_start = sample_filter.start
        query = query.filter(Meter.timestamp >= ts_start)
    if sample_filter.end:
        ts_end = sample_filter.end
        query = query.filter(Meter.timestamp < ts_end)
    if sample_filter.user:
        query = query.filter_by(user_id=sample_filter.user)
    if sample_filter.project:
        query = query.filter_by(project_id=sample_filter.project)
    if sample_filter.resource:
        query = query.filter_by(resource_id=sample_filter.resource)

    if sample_filter.metaquery:
        raise NotImplementedError('metaquery not implemented')

    return query


class Connection(base.Connection):
    """SqlAlchemy connection."""

    def __init__(self, conf):
        url = conf.database.connection
        if url == 'sqlite://':
            conf.database.connection = \
                os.environ.get('CEILOMETER_TEST_SQL_URL', url)

    def upgrade(self, version=None):
        session = sqlalchemy_session.get_session()
        migration.db_sync(session.get_bind(), version=version)

    def clear(self):
        session = sqlalchemy_session.get_session()
        engine = session.get_bind()
        for table in reversed(Base.metadata.sorted_tables):
            engine.execute(table.delete())

    @staticmethod
    def record_metering_data(data):
        """Write the data to the backend storage system.

        :param data: a dictionary such as returned by
                     ceilometer.meter.meter_message_from_counter
        """
        session = sqlalchemy_session.get_session()
        with session.begin():
            if data['source']:
                source = session.query(Source).get(data['source'])
                if not source:
                    source = Source(id=data['source'])
                    session.add(source)
            else:
                source = None

            # create/update user && project, add/update their sources list
            if data['user_id']:
                user = session.merge(User(id=str(data['user_id'])))
                if not filter(lambda x: x.id == source.id, user.sources):
                    user.sources.append(source)
            else:
                user = None

            if data['project_id']:
                project = session.merge(Project(id=str(data['project_id'])))
                if not filter(lambda x: x.id == source.id, project.sources):
                    project.sources.append(source)
            else:
                project = None

            # Record the updated resource metadata
            rmetadata = data['resource_metadata']

            resource = session.merge(Resource(id=str(data['resource_id'])))
            if not filter(lambda x: x.id == source.id, resource.sources):
                resource.sources.append(source)
            resource.project = project
            resource.user = user
            # Current metadata being used and when it was last updated.
            resource.resource_metadata = rmetadata

            # Record the raw data for the meter.
            meter = Meter(counter_type=data['counter_type'],
                          counter_unit=data['counter_unit'],
                          counter_name=data['counter_name'], resource=resource)
            session.add(meter)
            if not filter(lambda x: x.id == source.id, meter.sources):
                meter.sources.append(source)
            meter.project = project
            meter.user = user
            meter.timestamp = data['timestamp']
            meter.resource_metadata = rmetadata
            meter.counter_volume = data['counter_volume']
            meter.message_signature = data['message_signature']
            meter.message_id = data['message_id']
            session.flush()

    @staticmethod
    def get_users(source=None):
        """Return an iterable of user id strings.

        :param source: Optional source filter.
        """
        session = sqlalchemy_session.get_session()
        query = session.query(User.id)
        if source is not None:
            query = query.filter(User.sources.any(id=source))
        return (x[0] for x in query.all())

    @staticmethod
    def get_projects(source=None):
        """Return an iterable of project id strings.

        :param source: Optional source filter.
        """
        session = sqlalchemy_session.get_session()
        query = session.query(Project.id)
        if source:
            query = query.filter(Project.sources.any(id=source))
        return (x[0] for x in query.all())

    @staticmethod
    def get_resources(user=None, project=None, source=None,
                      start_timestamp=None, end_timestamp=None,
                      metaquery={}, resource=None):
        """Return an iterable of api_models.Resource instances

        :param user: Optional ID for user that owns the resource.
        :param project: Optional ID for project that owns the resource.
        :param source: Optional source filter.
        :param start_timestamp: Optional modified timestamp start range.
        :param end_timestamp: Optional modified timestamp end range.
        :param metaquery: Optional dict with metadata to match on.
        :param resource: Optional resource filter.
        """
        session = sqlalchemy_session.get_session()
        query = session.query(Meter,).group_by(Meter.resource_id)
        if user is not None:
            query = query.filter(Meter.user_id == user)
        if source is not None:
            query = query.filter(Meter.sources.any(id=source))
        if start_timestamp:
            query = query.filter(Meter.timestamp >= start_timestamp)
        if end_timestamp:
            query = query.filter(Meter.timestamp < end_timestamp)
        if project is not None:
            query = query.filter(Meter.project_id == project)
        if resource is not None:
            query = query.filter(Meter.resource_id == resource)
        if metaquery:
            raise NotImplementedError('metaquery not implemented')

        for meter in query.all():
            yield api_models.Resource(
                resource_id=meter.resource_id,
                project_id=meter.project_id,
                source=meter.sources[0].id,
                user_id=meter.user_id,
                metadata=meter.resource_metadata,
                meter=[
                    api_models.ResourceMeter(
                        counter_name=m.counter_name,
                        counter_type=m.counter_type,
                        counter_unit=m.counter_unit,
                    )
                    for m in meter.resource.meters
                ],
            )

    @staticmethod
    def get_meters(user=None, project=None, resource=None, source=None,
                   metaquery={}):
        """Return an iterable of api_models.Meter instances

        :param user: Optional ID for user that owns the resource.
        :param project: Optional ID for project that owns the resource.
        :param resource: Optional ID of the resource.
        :param source: Optional source filter.
        :param metaquery: Optional dict with metadata to match on.
        """
        session = sqlalchemy_session.get_session()
        query = session.query(Resource)
        if user is not None:
            query = query.filter(Resource.user_id == user)
        if source is not None:
            query = query.filter(Resource.sources.any(id=source))
        if resource:
            query = query.filter(Resource.id == resource)
        if project is not None:
            query = query.filter(Resource.project_id == project)
        query = query.options(
            sqlalchemy_session.sqlalchemy.orm.joinedload('meters'))
        if metaquery:
            raise NotImplementedError('metaquery not implemented')

        for resource in query.all():
            meter_names = set()
            for meter in resource.meters:
                if meter.counter_name in meter_names:
                    continue
                meter_names.add(meter.counter_name)
                yield api_models.Meter(
                    name=meter.counter_name,
                    type=meter.counter_type,
                    unit=meter.counter_unit,
                    resource_id=resource.id,
                    project_id=resource.project_id,
                    source=resource.sources[0].id,
                    user_id=resource.user_id,
                )

    @staticmethod
    def get_samples(sample_filter, limit=None):
        """Return an iterable of api_models.Samples.

        :param sample_filter: Filter.
        :param limit: Maximum number of results to return.
        """
        if limit == 0:
            return

        session = sqlalchemy_session.get_session()
        query = session.query(Meter)
        query = make_query_from_filter(query, sample_filter,
                                       require_meter=False)
        if limit:
            query = query.limit(limit)
        samples = query.all()

        for s in samples:
            # Remove the id generated by the database when
            # the sample was inserted. It is an implementation
            # detail that should not leak outside of the driver.
            yield api_models.Sample(
                # Replace 'sources' with 'source' to meet the caller's
                # expectation, Meter.sources contains one and only one
                # source in the current implementation.
                source=s.sources[0].id,
                counter_name=s.counter_name,
                counter_type=s.counter_type,
                counter_unit=s.counter_unit,
                counter_volume=s.counter_volume,
                user_id=s.user_id,
                project_id=s.project_id,
                resource_id=s.resource_id,
                timestamp=s.timestamp,
                resource_metadata=s.resource_metadata,
                message_id=s.message_id,
                message_signature=s.message_signature,
            )

    @staticmethod
    def _make_volume_query(sample_filter, counter_volume_func):
        """Returns complex Meter counter_volume query for max and sum."""
        session = sqlalchemy_session.get_session()
        subq = session.query(Meter.id)
        subq = make_query_from_filter(subq, sample_filter, require_meter=False)
        subq = subq.subquery()
        mainq = session.query(Resource.id, counter_volume_func)
        mainq = mainq.join(Meter).group_by(Resource.id)
        return mainq.filter(Meter.id.in_(subq))

    @staticmethod
    def _make_stats_query(sample_filter):
        session = sqlalchemy_session.get_session()
        query = session.query(
            func.min(Meter.timestamp).label('tsmin'),
            func.max(Meter.timestamp).label('tsmax'),
            func.avg(Meter.counter_volume).label('avg'),
            func.sum(Meter.counter_volume).label('sum'),
            func.min(Meter.counter_volume).label('min'),
            func.max(Meter.counter_volume).label('max'),
            func.count(Meter.counter_volume).label('count'))

        return make_query_from_filter(query, sample_filter)

    @staticmethod
    def _stats_result_to_model(result, period, period_start, period_end):
        duration = (timeutils.delta_seconds(result.tsmin, result.tsmax)
                    if result.tsmin is not None and result.tsmax is not None
                    else None)
        return api_models.Statistics(
            count=int(result.count),
            min=result.min,
            max=result.max,
            avg=result.avg,
            sum=result.sum,
            duration_start=result.tsmin,
            duration_end=result.tsmax,
            duration=duration,
            period=period,
            period_start=period_start,
            period_end=period_end,
        )

    def get_meter_statistics(self, sample_filter, period=None):
        """Return an iterable of api_models.Statistics instances containing
        meter statistics described by the query parameters.

        The filter must have a meter value set.

        """
        if not period or not sample_filter.start or not sample_filter.end:
            res = self._make_stats_query(sample_filter).all()[0]

        if not period:
            yield self._stats_result_to_model(res, 0, res.tsmin, res.tsmax)
            return

        query = self._make_stats_query(sample_filter)
        # HACK(jd) This is an awful method to compute stats by period, but
        # since we're trying to be SQL agnostic we have to write portable
        # code, so here it is, admire! We're going to do one request to get
        # stats by period. We would like to use GROUP BY, but there's no
        # portable way to manipulate timestamp in SQL, so we can't.
        for period_start, period_end in base.iter_period(
                sample_filter.start or res.tsmin,
                sample_filter.end or res.tsmax,
                period):
            q = query.filter(Meter.timestamp >= period_start)
            q = q.filter(Meter.timestamp < period_end)
            r = q.all()[0]
            # Don't return results that didn't have any data.
            if r.count:
                yield self._stats_result_to_model(
                    result=r,
                    period=int(timeutils.delta_seconds(period_start,
                                                       period_end)),
                    period_start=period_start,
                    period_end=period_end,
                )

    @staticmethod
    def _row_to_alarm_model(row):
        return api_models.Alarm(alarm_id=row.id,
                                enabled=row.enabled,
                                name=row.name,
                                description=row.description,
                                timestamp=row.timestamp,
                                counter_name=row.counter_name,
                                user_id=row.user_id,
                                project_id=row.project_id,
                                comparison_operator=row.comparison_operator,
                                threshold=row.threshold,
                                statistic=row.statistic,
                                evaluation_periods=row.evaluation_periods,
                                period=row.period,
                                state=row.state,
                                state_timestamp=row.state_timestamp,
                                ok_actions=row.ok_actions,
                                alarm_actions=row.alarm_actions,
                                insufficient_data_actions=
                                row.insufficient_data_actions,
                                matching_metadata=row.matching_metadata)

    @staticmethod
    def _alarm_model_to_row(alarm, row=None):
        if row is None:
            row = Alarm(id=str(uuid.uuid1()))
        row.update(alarm.as_dict())
        return row

    def get_alarms(self, name=None, user=None,
                   project=None, enabled=True, alarm_id=None):
        """Yields a lists of alarms that match filters
        :param user: Optional ID for user that owns the resource.
        :param project: Optional ID for project that owns the resource.
        :param enabled: Optional boolean to list disable alarm.
        :param alarm_id: Optional alarm_id to return one alarm.
        """
        session = sqlalchemy_session.get_session()
        query = session.query(Alarm)
        if name is not None:
            query = query.filter(Alarm.name == name)
        if enabled is not None:
            query = query.filter(Alarm.enabled == enabled)
        if user is not None:
            query = query.filter(Alarm.user_id == user)
        if project is not None:
            query = query.filter(Alarm.project_id == project)
        if alarm_id is not None:
            query = query.filter(Alarm.id == alarm_id)

        return (self._row_to_alarm_model(x) for x in query.all())

    def update_alarm(self, alarm):
        """update alarm

        :param alarm: the new Alarm to update
        """
        session = sqlalchemy_session.get_session()
        with session.begin():
            if alarm.alarm_id:
                alarm_row = session.merge(Alarm(id=alarm.alarm_id))
                self._alarm_model_to_row(alarm, alarm_row)
            else:
                session.merge(User(id=alarm.user_id))
                session.merge(Project(id=alarm.project_id))

                alarm_row = self._alarm_model_to_row(alarm)
                session.add(alarm_row)

            session.flush()
        return self._row_to_alarm_model(alarm_row)

    @staticmethod
    def delete_alarm(alarm_id):
        """Delete a alarm

        :param alarm_id: ID of the alarm to delete
        """
        session = sqlalchemy_session.get_session()
        with session.begin():
            session.query(Alarm).filter(Alarm.id == alarm_id).delete()
            session.flush()

    @staticmethod
    def _get_unique(session, key):
        return session.query(UniqueName).filter(UniqueName.key == key).first()

    def _get_or_create_unique_name(self, key, session=None):
        """Find the UniqueName entry for a given key, creating
           one if necessary.

           This may result in a flush.
        """
        if session is None:
            session = sqlalchemy_session.get_session()
        with session.begin(subtransactions=True):
            unique = self._get_unique(session, key)
            if not unique:
                unique = UniqueName(key=key)
                session.add(unique)
                session.flush()
        return unique

    def _make_trait(self, trait_model, event, session=None):
        """Make a new Trait from a Trait model.

        Doesn't flush or add to session.
        """
        name = self._get_or_create_unique_name(trait_model.name,
                                               session=session)
        value_map = Trait._value_map
        values = {'t_string': None, 't_float': None,
                  't_int': None, 't_datetime': None}
        value = trait_model.value
        if trait_model.dtype == api_models.Trait.DATETIME_TYPE:
            value = utils.dt_to_decimal(value)
        values[value_map[trait_model.dtype]] = value
        return Trait(name, event, trait_model.dtype, **values)

    def _record_event(self, session, event_model):
        """Store a single Event, including related Traits.
        """
        with session.begin(subtransactions=True):
            unique = self._get_or_create_unique_name(event_model.event_name,
                                                     session=session)

            generated = utils.dt_to_decimal(event_model.generated)
            event = Event(unique, generated)
            session.add(event)

            new_traits = []
            if event_model.traits:
                for trait in event_model.traits:
                    t = self._make_trait(trait, event, session=session)
                    session.add(t)
                    new_traits.append(t)

        # Note: we don't flush here, explicitly (unless a new uniquename
        # does it). Otherwise, just wait until all the Events are staged.
        return (event, new_traits)

    def record_events(self, event_models):
        """Write the events to SQL database via sqlalchemy.

        :param event_models: a list of model.Event objects.

        Flush when they're all added, unless new UniqueNames are
        added along the way.
        """
        session = sqlalchemy_session.get_session()
        with session.begin():
            events = [self._record_event(session, event_model)
                      for event_model in event_models]
            session.flush()

        # Update the models with the underlying DB ID.
        for model, actual in zip(event_models, events):
            actual_event, actual_traits = actual
            model.id = actual_event.id
            if model.traits and actual_traits:
                for trait, actual_trait in zip(model.traits, actual_traits):
                    trait.id = actual_trait.id

    def get_events(self, event_filter):
        """Return an iterable of model.Event objects.

        :param event_filter: EventFilter instance
        """

        start = utils.dt_to_decimal(event_filter.start)
        end = utils.dt_to_decimal(event_filter.end)
        session = sqlalchemy_session.get_session()
        with session.begin():
            sub_query = session.query(Event.id)\
                .join(Trait, Trait.event_id == Event.id)\
                .filter(Event.generated >= start, Event.generated <= end)

            if event_filter.event_name:
                event_name = self._get_unique(session, event_filter.event_name)
                sub_query = sub_query.filter(Event.unique_name == event_name)

            if event_filter.traits:
                for key, value in event_filter.traits.iteritems():
                    if key == 'key':
                        key = self._get_unique(session, value)
                        sub_query = sub_query.filter(Trait.name == key)
                    elif key == 't_string':
                        sub_query = sub_query.filter(Trait.t_string == value)
                    elif key == 't_int':
                        sub_query = sub_query.filter(Trait.t_int == value)
                    elif key == 't_datetime':
                        dt = utils.dt_to_decimal(value)
                        sub_query = sub_query.filter(Trait.t_datetime == dt)
                    elif key == 't_float':
                        sub_query = sub_query.filter(Trait.t_datetime == value)

            sub_query = sub_query.subquery()

            all_data = session.query(Trait)\
                .join(sub_query, Trait.event_id == sub_query.c.id)

            # Now convert the sqlalchemy objects back into Models ...
            event_models_dict = {}
            for trait in all_data.all():
                event = event_models_dict.get(trait.event_id)
                if not event:
                    generated = utils.decimal_to_dt(trait.event.generated)
                    event = api_models.Event(trait.event.unique_name.key,
                                             generated, [])
                    event_models_dict[trait.event_id] = event
                value = trait.get_value()
                trait_model = api_models.Trait(trait.name.key, trait.t_type,
                                               value)
                event.append_trait(trait_model)

        event_models = event_models_dict.values()
        return sorted(event_models, key=operator.attrgetter('generated'))
