# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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

"""Monitor base exception handling.

Includes decorator for re-raising Monitor-type exceptions.

SHOULD include dedicated exception logging.

"""

from oslo.config import cfg
import webob.exc

from monitor import flags
from monitor.openstack.common import log as logging

LOG = logging.getLogger(__name__)

exc_log_opts = [
    cfg.BoolOpt('fatal_exception_format_errors',
                default=False,
                help='make exception message format errors fatal'),
]

FLAGS = flags.FLAGS
FLAGS.register_opts(exc_log_opts)


class ConvertedException(webob.exc.WSGIHTTPException):
    def __init__(self, code=0, title="", explanation=""):
        self.code = code
        self.title = title
        self.explanation = explanation
        super(ConvertedException, self).__init__()


class ProcessExecutionError(IOError):
    def __init__(self, stdout=None, stderr=None, exit_code=None, cmd=None,
                 description=None):
        self.exit_code = exit_code
        self.stderr = stderr
        self.stdout = stdout
        self.cmd = cmd
        self.description = description

        if description is None:
            description = _('Unexpected error while running command.')
        if exit_code is None:
            exit_code = '-'
        message = _('%(description)s\nCommand: %(cmd)s\n'
                    'Exit code: %(exit_code)s\nStdout: %(stdout)r\n'
                    'Stderr: %(stderr)r') % locals()
        IOError.__init__(self, message)


class Error(Exception):
    pass


class DBError(Error):
    """Wraps an implementation specific exception."""
    def __init__(self, inner_exception=None):
        self.inner_exception = inner_exception
        super(DBError, self).__init__(str(inner_exception))


def wrap_db_error(f):
    def _wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except UnicodeEncodeError:
            raise InvalidUnicodeParameter()
        except Exception, e:
            LOG.exception(_('DB exception wrapped.'))
            raise DBError(e)
    _wrap.func_name = f.func_name
    return _wrap


class MonitorException(Exception):
    """Base Monitor Exception

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.

    """
    message = _("An unknown exception occurred.")
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.message % kwargs

            except Exception as e:
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                LOG.exception(_('Exception in string format operation'))
                for name, value in kwargs.iteritems():
                    LOG.error("%s: %s" % (name, value))
                if FLAGS.fatal_exception_format_errors:
                    raise e
                else:
                    # at least get the core message out if something happened
                    message = self.message

        super(MonitorException, self).__init__(message)


class GlanceConnectionFailed(MonitorException):
    message = _("Connection to glance failed") + ": %(reason)s"


class NotAuthorized(MonitorException):
    message = _("Not authorized.")
    code = 403


class AdminRequired(NotAuthorized):
    message = _("User does not have admin privileges")


class PolicyNotAuthorized(NotAuthorized):
    message = _("Policy doesn't allow %(action)s to be performed.")


class ImageNotAuthorized(MonitorException):
    message = _("Not authorized for image %(image_id)s.")


class Invalid(MonitorException):
    message = _("Unacceptable parameters.")
    code = 400


class InvalidSnapshot(Invalid):
    message = _("Invalid snapshot") + ": %(reason)s"


class ServiceManageAttached(Invalid):
    message = _("ServiceManage %(servicemanage_id)s is still attached, detach servicemanage first.")


class SfJsonEncodeFailure(MonitorException):
    message = _("Failed to load data into json format")


class InvalidRequest(Invalid):
    message = _("The request is invalid.")


class InvalidResults(Invalid):
    message = _("The results are invalid.")


class InvalidInput(Invalid):
    message = _("Invalid input received") + ": %(reason)s"


class InvalidServiceManageType(Invalid):
    message = _("Invalid servicemanage type") + ": %(reason)s"


class InvalidServiceManage(Invalid):
    message = _("Invalid servicemanage") + ": %(reason)s"


class InvalidPortRange(Invalid):
    message = _("Invalid port range %(from_port)s:%(to_port)s. %(msg)s")


class InvalidContentType(Invalid):
    message = _("Invalid content type %(content_type)s.")


class InvalidUnicodeParameter(Invalid):
    message = _("Invalid Parameter: "
                "Unicode is not supported by the current database.")


# Cannot be templated as the error syntax varies.
# msg needs to be constructed when raised.
class InvalidParameterValue(Invalid):
    message = _("%(err)s")


class ServiceUnavailable(Invalid):
    message = _("Service is unavailable at this time.")


class MonitorServiceUnavailable(ServiceUnavailable):
    message = _("Monitor service is unavailable at this time.")


class ImageUnacceptable(Invalid):
    message = _("Image %(image_id)s is unacceptable: %(reason)s")


class InvalidUUID(Invalid):
    message = _("Expected a uuid but received %(uuid).")


class NotFound(MonitorException):
    message = _("Resource could not be found.")
    code = 404
    safe = True


class PersistentServiceManageFileNotFound(NotFound):
    message = _("ServiceManage %(servicemanage_id)s persistence file could not be found.")



class ServiceManageNotFound(NotFound):
    message = _("ServiceManage %(servicemanage_id)s could not be found.")


class SfAccountNotFound(NotFound):
    message = _("Unable to locate account %(account_name)s on "
                "Solidfire device")


class ServiceManageNotFoundForInstance(ServiceManageNotFound):
    message = _("ServiceManage not found for instance %(instance_id)s.")


class ServiceManageMetadataNotFound(NotFound):
    message = _("ServiceManage %(servicemanage_id)s has no metadata with "
                "key %(metadata_key)s.")


class InvalidServiceManageMetadata(Invalid):
    message = _("Invalid metadata") + ": %(reason)s"


class InvalidServiceManageMetadataSize(Invalid):
    message = _("Invalid metadata size") + ": %(reason)s"


class SnapshotMetadataNotFound(NotFound):
    message = _("Snapshot %(snapshot_id)s has no metadata with "
                "key %(metadata_key)s.")


class InvalidSnapshotMetadata(Invalid):
    message = _("Invalid metadata") + ": %(reason)s"


class InvalidSnapshotMetadataSize(Invalid):
    message = _("Invalid metadata size") + ": %(reason)s"


class ServiceManageTypeNotFound(NotFound):
    message = _("ServiceManage type %(servicemanage_type_id)s could not be found.")


class ServiceManageTypeNotFoundByName(ServiceManageTypeNotFound):
    message = _("ServiceManage type with name %(servicemanage_type_name)s "
                "could not be found.")


class ServiceManageTypeExtraSpecsNotFound(NotFound):
    message = _("ServiceManage Type %(servicemanage_type_id)s has no extra specs with "
                "key %(extra_specs_key)s.")


class SnapshotNotFound(NotFound):
    message = _("Snapshot %(snapshot_id)s could not be found.")


class ServiceManageIsBusy(MonitorException):
    message = _("deleting servicemanage %(servicemanage_name)s that has snapshot")


class SnapshotIsBusy(MonitorException):
    message = _("deleting snapshot %(snapshot_name)s that has "
                "dependent servicemanages")


class ISCSITargetNotFoundForServiceManage(NotFound):
    message = _("No target id found for servicemanage %(servicemanage_id)s.")


class ISCSITargetCreateFailed(MonitorException):
    message = _("Failed to create iscsi target for servicemanage %(servicemanage_id)s.")


class ISCSITargetAttachFailed(MonitorException):
    message = _("Failed to attach iSCSI target for servicemanage %(servicemanage_id)s.")


class ISCSITargetRemoveFailed(MonitorException):
    message = _("Failed to remove iscsi target for servicemanage %(servicemanage_id)s.")


class DiskNotFound(NotFound):
    message = _("No disk at %(location)s")


class InvalidImageRef(Invalid):
    message = _("Invalid image href %(image_href)s.")


class ImageNotFound(NotFound):
    message = _("Image %(image_id)s could not be found.")


class ServiceNotFound(NotFound):
    message = _("Service %(service_id)s could not be found.")


class HostNotFound(NotFound):
    message = _("Host %(host)s could not be found.")


class MonitorHostNotFound(HostNotFound):
    message = _("Monitor host %(host)s could not be found.")

class OsdNotFound(NotFound):
    message = _("Osd %(osd)s could not be found.")

class MonitorOsdNotFound(OsdNotFound):
    message = _("Osd %(osd)s could not be found.")

class SchedulerHostFilterNotFound(NotFound):
    message = _("Scheduler Host Filter %(filter_name)s could not be found.")


class SchedulerHostWeigherNotFound(NotFound):
    message = _("Scheduler Host Weigher %(weigher_name)s could not be found.")


class HostBinaryNotFound(NotFound):
    message = _("Could not find binary %(binary)s on host %(host)s.")


class InvalidReservationExpiration(Invalid):
    message = _("Invalid reservation expiration %(expire)s.")


class InvalidQuotaValue(Invalid):
    message = _("Change would make usage less than 0 for the following "
                "resources: %(unders)s")


class QuotaNotFound(NotFound):
    message = _("Quota could not be found")


class QuotaResourceUnknown(QuotaNotFound):
    message = _("Unknown quota resources %(unknown)s.")


class ProjectQuotaNotFound(QuotaNotFound):
    message = _("Quota for project %(project_id)s could not be found.")


class QuotaClassNotFound(QuotaNotFound):
    message = _("Quota class %(class_name)s could not be found.")


class QuotaUsageNotFound(QuotaNotFound):
    message = _("Quota usage for project %(project_id)s could not be found.")


class ReservationNotFound(QuotaNotFound):
    message = _("Quota reservation %(uuid)s could not be found.")


class OverQuota(MonitorException):
    message = _("Quota exceeded for resources: %(overs)s")


class MigrationNotFound(NotFound):
    message = _("Migration %(migration_id)s could not be found.")


class MigrationNotFoundByStatus(MigrationNotFound):
    message = _("Migration not found for instance %(instance_id)s "
                "with status %(status)s.")


class FileNotFound(NotFound):
    message = _("File %(file_path)s could not be found.")


class ClassNotFound(NotFound):
    message = _("Class %(class_name)s could not be found: %(exception)s")


class NotAllowed(MonitorException):
    message = _("Action not allowed.")


#TODO(bcwaldon): EOL this exception!
class Duplicate(MonitorException):
    pass


class KeyPairExists(Duplicate):
    message = _("Key pair %(key_name)s already exists.")


class ServiceManageTypeExists(Duplicate):
    message = _("ServiceManage Type %(id)s already exists.")


class MigrationError(MonitorException):
    message = _("Migration error") + ": %(reason)s"


class MalformedRequestBody(MonitorException):
    message = _("Malformed message body: %(reason)s")


class ConfigNotFound(NotFound):
    message = _("Could not find config at %(path)s")


class PasteAppNotFound(NotFound):
    message = _("Could not load paste app '%(name)s' from %(path)s")


class NoValidHost(MonitorException):
    message = _("No valid host was found. %(reason)s")


class WillNotSchedule(MonitorException):
    message = _("Host %(host)s is not up or doesn't exist.")


class QuotaError(MonitorException):
    message = _("Quota exceeded") + ": code=%(code)s"
    code = 413
    headers = {'Retry-After': 0}
    safe = True


class ServiceManageSizeExceedsAvailableQuota(QuotaError):
    message = _("Requested servicemanage or snapshot exceeds "
                "allowed Gigabytes quota")


class ServiceManageSizeExceedsQuota(QuotaError):
    message = _("Maximum servicemanage/snapshot size exceeded")


class ServiceManageLimitExceeded(QuotaError):
    message = _("Maximum number of servicemanages allowed (%(allowed)d) exceeded")


class SnapshotLimitExceeded(QuotaError):
    message = _("Maximum number of snapshots allowed (%(allowed)d) exceeded")


class DuplicateSfServiceManageNames(Duplicate):
    message = _("Detected more than one servicemanage with name %(vol_name)s")


class Duplicate3PARHost(MonitorException):
    message = _("3PAR Host already exists: %(err)s.  %(info)s")


class ServiceManageTypeCreateFailed(MonitorException):
    message = _("Cannot create servicemanage_type with "
                "name %(name)s and specs %(extra_specs)s")


class SolidFireAPIException(MonitorException):
    message = _("Bad response from SolidFire API")


class SolidFireAPIDataException(SolidFireAPIException):
    message = _("Error in SolidFire API response: data=%(data)s")


class UnknownCmd(Invalid):
    message = _("Unknown or unsupported command %(cmd)s")


class MalformedResponse(Invalid):
    message = _("Malformed response to command %(cmd)s: %(reason)s")


class BadHTTPResponseStatus(MonitorException):
    message = _("Bad HTTP response status %(status)s")


class FailedCmdWithDump(MonitorException):
    message = _("Operation failed with status=%(status)s. Full dump: %(data)s")


class ZadaraServerCreateFailure(MonitorException):
    message = _("Unable to create server object for initiator %(name)s")


class ZadaraServerNotFound(NotFound):
    message = _("Unable to find server object for initiator %(name)s")


class ZadaraVPSANoActiveController(MonitorException):
    message = _("Unable to find any active VPSA controller")


class ZadaraAttachmentsNotFound(NotFound):
    message = _("Failed to retrieve attachments for servicemanage %(name)s")


class ZadaraInvalidAttachmentInfo(Invalid):
    message = _("Invalid attachment info for servicemanage %(name)s: %(reason)s")


class InstanceNotFound(NotFound):
    message = _("Instance %(instance_id)s could not be found.")


class ServiceManageBackendAPIException(MonitorException):
    message = _("Bad or unexpected response from the storage servicemanage "
                "backend API: %(data)s")


class NfsException(MonitorException):
    message = _("Unknown NFS exception")


class NfsNoSharesMounted(NotFound):
    message = _("No mounted NFS shares found")


class NfsNoSuitableShareFound(NotFound):
    message = _("There is no share which can host %(servicemanage_size)sG")


class GlusterfsException(MonitorException):
    message = _("Unknown Gluster exception")


class GlusterfsNoSharesMounted(NotFound):
    message = _("No mounted Gluster shares found")


class GlusterfsNoSuitableShareFound(NotFound):
    message = _("There is no share which can host %(servicemanage_size)sG")


class GlanceMetadataExists(Invalid):
    message = _("Glance metadata cannot be updated, key %(key)s"
                " exists for servicemanage id %(servicemanage_id)s")


class ImageCopyFailure(Invalid):
    message = _("Failed to copy image to servicemanage")


class BackupNotFound(NotFound):
    message = _("Backup %(backup_id)s could not be found.")


class InvalidBackup(Invalid):
    message = _("Invalid backup: %(reason)s")


class SwiftConnectionFailed(MonitorException):
    message = _("Connection to swift failed") + ": %(reason)s"

# Exceptions for MonitorService

class MonitorServiceNotFound(NotFound):
    message = _("Not Found: %(monitor_service)s")
