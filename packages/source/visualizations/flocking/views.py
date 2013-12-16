import json

from django import http
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard.dashboards.visualizations.flocking import utils
from .tables import FlockingInstancesTable
from .tabs import FlockingTabs


class IndexView(tabs.TabbedTableView):
    tab_group_class = FlockingTabs
    table_class = FlockingInstancesTable
    template_name = 'visualizations/flocking/index.html'

    def get(self, request, *args, **kwargs):
        if self.request.is_ajax() and self.request.GET.get("json", False):
            try:
                instances = utils.get_instances_data(self.request)
                # Uncomment the following line to use fake test data.
                #instances = utils.get_fake_instances_data(self.request)
            except:
                instances = []
                exceptions.handle(request,
                                  _('Unable to retrieve instance list.'))
            data = json.dumps([i._apiresource._info for i in instances])
            return http.HttpResponse(data)
        else:
            return super(IndexView, self).get(request, *args, **kwargs)
