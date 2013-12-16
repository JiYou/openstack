from django.utils.translation import ugettext_lazy as _

import horizon


class InstanceVisualizations(horizon.PanelGroup):
    slug = "instance_visualizations"
    name = _("Instance Visualizations")
    panels = ('flocking',)


class VizDash(horizon.Dashboard):
    name = _("Visualizations")
    slug = "visualizations"
    panels = (InstanceVisualizations,)
    default_panel = 'flocking'
    roles = ('admin',)


horizon.register(VizDash)
