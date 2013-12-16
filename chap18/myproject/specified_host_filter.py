from nova.scheduler import filters
from nova.openstack.common import log as logging

LOG = logging.getLogger(__name__)

class SpecifiedHostFilter(filters.BaseHostFilter):
    def __init__(self):
        LOG.info("SpecifiedHostFilter is initialized!")

    def host_passes(self, host_state, filter_properties):
        scheduler_hints = filter_properties.get('scheduler_hints', {})
        requested_host = scheduler_hints.get('requested_host', None)

        if requested_host:
            return requested_host == host_state.host
        return True
