from django.utils.translation import ugettext_lazy as _

import horizon
from openstack_dashboard.dashboards.visualizations import dashboard


class Flocking(horizon.Panel):
    name = _("Flocking")
    slug = 'flocking'


dashboard.VizDash.register(Flocking)
