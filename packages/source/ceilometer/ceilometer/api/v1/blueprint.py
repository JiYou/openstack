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
"""Blueprint for version 1 of API.
"""

#############################################################################
#############################################################################
#
# NOTE(dhellmann): The V1 API is being deprecated during Havana, and
# as such it is feature-frozen. Only make bug-fix changes in this file.
#
#############################################################################
#############################################################################

# [ ] / -- information about this version of the API
#
# [ ] /extensions -- list of available extensions
# [ ] /extensions/<extension> -- details about a specific extension
#
# [ ] /sources -- list of known sources (where do we get this?)
# [ ] /sources/components -- list of components which provide metering
#                            data (where do we get this)?
#
# [x] /projects/<project>/resources -- list of resource ids
# [x] /resources -- list of resource ids
# [x] /sources/<source>/resources -- list of resource ids
# [x] /users/<user>/resources -- list of resource ids
#
# [x] /users -- list of user ids
# [x] /sources/<source>/users -- list of user ids
#
# [x] /projects -- list of project ids
# [x] /sources/<source>/projects -- list of project ids
#
# [ ] /resources/<resource> -- metadata
#
# [x] /meters -- list of meters
# [x] /projects/<project>/meters -- list of meters reporting for parent obj
# [x] /resources/<resource>/meters -- list of meters reporting for parent obj
# [x] /sources/<source>/meters -- list of meters reporting for parent obj
# [x] /users/<user>/meters -- list of meters reporting for parent obj
#
# [x] /projects/<project>/meters/<meter> -- samples
# [x] /resources/<resource>/meters/<meter> -- samples
# [x] /sources/<source>/meters/<meter> -- samples
# [x] /users/<user>/meters/<meter> -- samples
#
# [ ] /projects/<project>/meters/<meter>/duration -- total time for selected
#                                                    meter
# [x] /resources/<resource>/meters/<meter>/duration -- total time for selected
#                                                      meter
# [ ] /sources/<source>/meters/<meter>/duration -- total time for selected
#                                                  meter
# [ ] /users/<user>/meters/<meter>/duration -- total time for selected meter
#
# [ ] /projects/<project>/meters/<meter>/volume -- total or max volume for
#                                                  selected meter
# [x] /projects/<project>/meters/<meter>/volume/max -- max volume for
#                                                      selected meter
# [x] /projects/<project>/meters/<meter>/volume/sum -- total volume for
#                                                      selected meter
# [ ] /resources/<resource>/meters/<meter>/volume -- total or max volume for
#                                                    selected meter
# [x] /resources/<resource>/meters/<meter>/volume/max -- max volume for
#                                                        selected meter
# [x] /resources/<resource>/meters/<meter>/volume/sum -- total volume for
#                                                        selected meter
# [ ] /sources/<source>/meters/<meter>/volume -- total or max volume for
#                                                selected meter
# [ ] /users/<user>/meters/<meter>/volume -- total or max volume for selected
#                                            meter

import datetime

import flask

from ceilometer.openstack.common import log
from ceilometer.openstack.common import timeutils

from ceilometer import storage

from ceilometer.api import acl


LOG = log.getLogger(__name__)


blueprint = flask.Blueprint('v1', __name__,
                            template_folder='templates',
                            static_folder='static')


def request_wants_html():
    best = flask.request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'text/html' and \
        flask.request.accept_mimetypes[best] > \
        flask.request.accept_mimetypes['application/json']


def _get_metaquery(args):
    return dict((k, v)
                for (k, v) in args.iteritems()
                if k.startswith('metadata.'))


def check_authorized_project(project):
    authorized_project = acl.get_limited_to_project(flask.request.headers)
    if authorized_project and authorized_project != project:
        flask.abort(404)


## APIs for working with meters.


@blueprint.route('/meters')
def list_meters_all():
    """Return a list of meters.
    :param metadata.<key>: match on the metadata within the resource.
                           (optional)
    """
    rq = flask.request
    meters = rq.storage_conn.get_meters(
        project=acl.get_limited_to_project(rq.headers),
        metaquery=_get_metaquery(rq.args))
    return flask.jsonify(meters=[m.as_dict() for m in meters])


@blueprint.route('/resources/<resource>/meters')
def list_meters_by_resource(resource):
    """Return a list of meters by resource.

    :param resource: The ID of the resource.
    :param metadata.<key>: match on the metadata within the resource.
                           (optional)
    """
    rq = flask.request
    meters = rq.storage_conn.get_meters(
        resource=resource,
        project=acl.get_limited_to_project(rq.headers),
        metaquery=_get_metaquery(rq.args))
    return flask.jsonify(meters=[m.as_dict() for m in meters])


@blueprint.route('/users/<user>/meters')
def list_meters_by_user(user):
    """Return a list of meters by user.

    :param user: The ID of the owning user.
    :param metadata.<key>: match on the metadata within the resource.
                           (optional)
    """
    rq = flask.request
    meters = rq.storage_conn.get_meters(
        user=user,
        project=acl.get_limited_to_project(rq.headers),
        metaquery=_get_metaquery(rq.args))
    return flask.jsonify(meters=[m.as_dict() for m in meters])


@blueprint.route('/projects/<project>/meters')
def list_meters_by_project(project):
    """Return a list of meters by project.

    :param project: The ID of the owning project.
    :param metadata.<key>: match on the metadata within the resource.
                           (optional)
    """
    check_authorized_project(project)

    rq = flask.request
    meters = rq.storage_conn.get_meters(
        project=project,
        metaquery=_get_metaquery(rq.args))
    return flask.jsonify(meters=[m.as_dict() for m in meters])


@blueprint.route('/sources/<source>/meters')
def list_meters_by_source(source):
    """Return a list of meters by source.

    :param source: The ID of the owning source.
    :param metadata.<key>: match on the metadata within the resource.
                           (optional)
    """
    rq = flask.request
    meters = rq.storage_conn.get_meters(
        source=source,
        project=acl.get_limited_to_project(rq.headers),
        metaquery=_get_metaquery(rq.args))
    return flask.jsonify(meters=[m.as_dict() for m in meters])


## APIs for working with resources.

def _list_resources(source=None, user=None, project=None):
    """Return a list of resource identifiers.
    """
    rq = flask.request
    q_ts = _get_query_timestamps(rq.args)
    resources = rq.storage_conn.get_resources(
        source=source,
        user=user,
        project=project,
        start_timestamp=q_ts['start_timestamp'],
        end_timestamp=q_ts['end_timestamp'],
        metaquery=_get_metaquery(rq.args),
    )
    return flask.jsonify(resources=[r.as_dict() for r in resources])


@blueprint.route('/projects/<project>/resources')
def list_resources_by_project(project):
    """Return a list of resources owned by the project.

    :param project: The ID of the owning project.
    :param start_timestamp: Limits resources by last update time >= this value.
        (optional)
    :type start_timestamp: ISO date in UTC
    :param end_timestamp: Limits resources by last update time < this value.
        (optional)
    :type end_timestamp: ISO date in UTC
    :param metadata.<key>: match on the metadata within the resource.
                           (optional)
    """
    check_authorized_project(project)
    return _list_resources(project=project)


@blueprint.route('/resources')
def list_all_resources():
    """Return a list of all known resources.

    :param start_timestamp: Limits resources by last update time >= this value.
        (optional)
    :type start_timestamp: ISO date in UTC
    :param end_timestamp: Limits resources by last update time < this value.
        (optional)
    :type end_timestamp: ISO date in UTC
    :param metadata.<key>: match on the metadata within the resource.
                           (optional)
    """
    return _list_resources(
        project=acl.get_limited_to_project(flask.request.headers))


@blueprint.route('/sources/<source>')
def get_source(source):
    """Return a source details.

    :param source: The ID of the reporting source.
    """
    return flask.jsonify(flask.request.sources.get(source, {}))


@blueprint.route('/sources/<source>/resources')
def list_resources_by_source(source):
    """Return a list of resources for which a source is reporting
    data.

    :param source: The ID of the reporting source.
    :param start_timestamp: Limits resources by last update time >= this value.
        (optional)
    :type start_timestamp: ISO date in UTC
    :param end_timestamp: Limits resources by last update time < this value.
        (optional)
    :type end_timestamp: ISO date in UTC
    :param metadata.<key>: match on the metadata within the resource.
                           (optional)
    """
    return _list_resources(
        source=source,
        project=acl.get_limited_to_project(flask.request.headers),
    )


@blueprint.route('/users/<user>/resources')
def list_resources_by_user(user):
    """Return a list of resources owned by the user.

    :param user: The ID of the owning user.
    :param start_timestamp: Limits resources by last update time >= this value.
        (optional)
    :type start_timestamp: ISO date in UTC
    :param end_timestamp: Limits resources by last update time < this value.
        (optional)
    :type end_timestamp: ISO date in UTC
    :param metadata.<key>: match on the metadata within the resource.
                           (optional)
    """
    return _list_resources(
        user=user,
        project=acl.get_limited_to_project(flask.request.headers),
    )


## APIs for working with users.


def _list_users(source=None):
    """Return a list of user names.
    """
    # TODO(jd) it might be better to return the real list of users that are
    # belonging to the project, but that's not provided by the storage
    # drivers for now
    if acl.get_limited_to_project(flask.request.headers):
        users = [flask.request.headers.get('X-User-id')]
    else:
        users = flask.request.storage_conn.get_users(source=source)
    return flask.jsonify(users=list(users))


@blueprint.route('/users')
def list_all_users():
    """Return a list of all known user names.
    """
    return _list_users()


@blueprint.route('/sources/<source>/users')
def list_users_by_source(source):
    """Return a list of the users for which the source is reporting
    data.

    :param source: The ID of the source.
    """
    return _list_users(source=source)


## APIs for working with projects.


def _list_projects(source=None):
    """Return a list of project names.
    """
    project = acl.get_limited_to_project(flask.request.headers)
    if project:
        if source:
            if project in flask.request.storage_conn.get_projects(
                    source=source):
                projects = [project]
            else:
                projects = []
        else:
            projects = [project]
    else:
        projects = flask.request.storage_conn.get_projects(source=source)
    return flask.jsonify(projects=list(projects))


@blueprint.route('/projects')
def list_all_projects():
    """Return a list of all known project names.
    """
    return _list_projects()


@blueprint.route('/sources/<source>/projects')
def list_projects_by_source(source):
    """Return a list project names for which the source is reporting
    data.

    :param source: The ID of the source.
    """
    return _list_projects(source=source)


## APIs for working with samples.


def _list_samples(meter,
                  project=None,
                  resource=None,
                  source=None,
                  user=None):
    """Return a list of raw samples.

    Note: the API talks about "events" these are equivelent to samples.
    but we still need to return the samples within the "events" dict
    to maintain API compatibilty.
    """
    q_ts = _get_query_timestamps(flask.request.args)
    f = storage.SampleFilter(
        user=user,
        project=project,
        source=source,
        meter=meter,
        resource=resource,
        start=q_ts['start_timestamp'],
        end=q_ts['end_timestamp'],
        metaquery=_get_metaquery(flask.request.args),
    )
    samples = flask.request.storage_conn.get_samples(f)

    jsonified = flask.jsonify(events=[s.as_dict() for s in samples])
    if request_wants_html():
        return flask.templating.render_template('list_event.html',
                                                user=user,
                                                project=project,
                                                source=source,
                                                meter=meter,
                                                resource=resource,
                                                events=jsonified)
    return jsonified


@blueprint.route('/projects/<project>/meters/<meter>')
def list_samples_by_project(project, meter):
    """Return a list of raw samples for the project.

    :param project: The ID of the project.
    :param meter: The name of the meter.
    :param start_timestamp: Limits samples by timestamp >= this value.
        (optional)
    :type start_timestamp: ISO date in UTC
    :param end_timestamp: Limits samples by timestamp < this value.
        (optional)
    :type end_timestamp: ISO date in UTC
    """
    check_authorized_project(project)
    return _list_samples(project=project,
                         meter=meter,
                         )


@blueprint.route('/resources/<resource>/meters/<meter>')
def list_samples_by_resource(resource, meter):
    """Return a list of raw samples for the resource.

    :param resource: The ID of the resource.
    :param meter: The name of the meter.
    :param start_timestamp: Limits samples by timestamp >= this value.
        (optional)
    :type start_timestamp: ISO date in UTC
    :param end_timestamp: Limits samples by timestamp < this value.
        (optional)
    :type end_timestamp: ISO date in UTC
    """
    return _list_samples(
        resource=resource,
        meter=meter,
        project=acl.get_limited_to_project(flask.request.headers),
    )


@blueprint.route('/sources/<source>/meters/<meter>')
def list_samples_by_source(source, meter):
    """Return a list of raw samples for the source.

    :param source: The ID of the reporting source.
    :param meter: The name of the meter.
    :param start_timestamp: Limits samples by timestamp >= this value.
        (optional)
    :type start_timestamp: ISO date in UTC
    :param end_timestamp: Limits samples by timestamp < this value.
        (optional)
    :type end_timestamp: ISO date in UTC
    """
    return _list_samples(
        source=source,
        meter=meter,
        project=acl.get_limited_to_project(flask.request.headers),
    )


@blueprint.route('/users/<user>/meters/<meter>')
def list_samples_by_user(user, meter):
    """Return a list of raw samples for the user.

    :param user: The ID of the user.
    :param meter: The name of the meter.
    :param start_timestamp: Limits samples by timestamp >= this value.
        (optional)
    :type start_timestamp: ISO date in UTC
    :param end_timestamp: Limits samples by timestamp < this value.
        (optional)
    :type end_timestamp: ISO date in UTC
    """
    return _list_samples(
        user=user,
        meter=meter,
        project=acl.get_limited_to_project(flask.request.headers),
    )


## APIs for working with meter calculations.


def _get_query_timestamps(args={}):
    # Determine the desired range, if any, from the
    # GET arguments. Set up the query range using
    # the specified offset.
    # [query_start ... start_timestamp ... end_timestamp ... query_end]
    search_offset = int(args.get('search_offset', 0))

    start_timestamp = args.get('start_timestamp')
    if start_timestamp:
        start_timestamp = timeutils.parse_isotime(start_timestamp)
        start_timestamp = start_timestamp.replace(tzinfo=None)
        query_start = (start_timestamp -
                       datetime.timedelta(minutes=search_offset))
    else:
        query_start = None

    end_timestamp = args.get('end_timestamp')
    if end_timestamp:
        end_timestamp = timeutils.parse_isotime(end_timestamp)
        end_timestamp = end_timestamp.replace(tzinfo=None)
        query_end = end_timestamp + datetime.timedelta(minutes=search_offset)
    else:
        query_end = None

    return dict(query_start=query_start,
                query_end=query_end,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                search_offset=search_offset,
                )


@blueprint.route('/resources/<resource>/meters/<meter>/duration')
def compute_duration_by_resource(resource, meter):
    """Return the earliest timestamp, last timestamp,
    and duration for the resource and meter.

    :param resource: The ID of the resource.
    :param meter: The name of the meter.
    :param start_timestamp: ISO-formatted string of the
        earliest timestamp to return.
    :param end_timestamp: ISO-formatted string of the
        latest timestamp to return.
    :param search_offset: Number of minutes before
        and after start and end timestamps to query.
    """
    q_ts = _get_query_timestamps(flask.request.args)
    start_timestamp = q_ts['start_timestamp']
    end_timestamp = q_ts['end_timestamp']

    # Query the database for the interval of timestamps
    # within the desired range.
    f = storage.SampleFilter(
        meter=meter,
        project=acl.get_limited_to_project(flask.request.headers),
        resource=resource,
        start=q_ts['query_start'],
        end=q_ts['query_end'],
    )
    stats = flask.request.storage_conn.get_meter_statistics(f)
    min_ts, max_ts = stats.duration_start, stats.duration_end

    # "Clamp" the timestamps we return to the original time
    # range, excluding the offset.
    LOG.debug('start_timestamp %s, end_timestamp %s, min_ts %s, max_ts %s',
              start_timestamp, end_timestamp, min_ts, max_ts)
    if start_timestamp and min_ts and min_ts < start_timestamp:
        min_ts = start_timestamp
        LOG.debug('clamping min timestamp to range')
    if end_timestamp and max_ts and max_ts > end_timestamp:
        max_ts = end_timestamp
        LOG.debug('clamping max timestamp to range')

    # If we got valid timestamps back, compute a duration in minutes.
    #
    # If the min > max after clamping then we know the
    # timestamps on the samples fell outside of the time
    # range we care about for the query, so treat them as
    # "invalid."
    #
    # If the timestamps are invalid, return None as a
    # sentinal indicating that there is something "funny"
    # about the range.
    if min_ts and max_ts and (min_ts <= max_ts):
        duration = timeutils.delta_seconds(min_ts, max_ts)
    else:
        min_ts = max_ts = duration = None

    return flask.jsonify(start_timestamp=min_ts,
                         end_timestamp=max_ts,
                         duration=duration,
                         )


def _get_statistics(stats_type, meter=None, resource=None, project=None):
    q_ts = _get_query_timestamps(flask.request.args)

    f = storage.SampleFilter(
        meter=meter,
        project=project,
        resource=resource,
        start=q_ts['query_start'],
        end=q_ts['query_end'],
    )
    # TODO(sberler): do we want to return an error if the resource
    # does not exist?
    results = list(flask.request.storage_conn.get_meter_statistics(f))
    value = None
    if results:
        value = getattr(results[0], stats_type)  # there should only be one!

    return flask.jsonify(volume=value)


@blueprint.route('/resources/<resource>/meters/<meter>/volume/max')
def compute_max_resource_volume(resource, meter):
    """Return the max volume for a meter.

    :param resource: The ID of the resource.
    :param meter: The name of the meter.
    :param start_timestamp: ISO-formatted string of the
        earliest time to include in the calculation.
    :param end_timestamp: ISO-formatted string of the
        latest time to include in the calculation.
    :param search_offset: Number of minutes before and
        after start and end timestamps to query.
    """
    return _get_statistics(
        'max',
        meter=meter,
        resource=resource,
        project=acl.get_limited_to_project(flask.request.headers),
    )


@blueprint.route('/resources/<resource>/meters/<meter>/volume/sum')
def compute_resource_volume_sum(resource, meter):
    """Return the sum of samples for a meter.

    :param resource: The ID of the resource.
    :param meter: The name of the meter.
    :param start_timestamp: ISO-formatted string of the
        earliest time to include in the calculation.
    :param end_timestamp: ISO-formatted string of the
        latest time to include in the calculation.
    :param search_offset: Number of minutes before and
        after start and end timestamps to query.
    """
    return _get_statistics(
        'sum',
        meter=meter,
        resource=resource,
        project=acl.get_limited_to_project(flask.request.headers),
    )


@blueprint.route('/projects/<project>/meters/<meter>/volume/max')
def compute_project_volume_max(project, meter):
    """Return the max volume for a meter.

    :param project: The ID of the project.
    :param meter: The name of the meter.
    :param start_timestamp: ISO-formatted string of the
        earliest time to include in the calculation.
    :param end_timestamp: ISO-formatted string of the
        latest time to include in the calculation.
    :param search_offset: Number of minutes before and
        after start and end timestamps to query.
    """
    check_authorized_project(project)
    return _get_statistics('max', project=project, meter=meter)


@blueprint.route('/projects/<project>/meters/<meter>/volume/sum')
def compute_project_volume_sum(project, meter):
    """Return the total volume for a meter.

    :param project: The ID of the project.
    :param meter: The name of the meter.
    :param start_timestamp: ISO-formatted string of the
        earliest time to include in the calculation.
    :param end_timestamp: ISO-formatted string of the
        latest time to include in the calculation.
    :param search_offset: Number of minutes before and
        after start and end timestamps to query.
    """
    check_authorized_project(project)

    return _get_statistics(
        'sum',
        meter=meter,
        project=project,
    )
