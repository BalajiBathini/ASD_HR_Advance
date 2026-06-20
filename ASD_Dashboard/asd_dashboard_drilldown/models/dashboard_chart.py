from odoo import models

class DashboardChart(models.Model):
    _inherit = 'dashboard.chart'

    def get_tile_data(self, conf_obj, previous=0):
        res = super(DashboardChart, self).get_tile_data(conf_obj, previous=previous)
        if isinstance(res, dict) and res.get('type') != 'error':
            res.update({
                'drilldown_model': conf_obj.model,
                'drilldown_domain': conf_obj.domain,
                'drilldown_action_id': self.item_action_id.id if self.item_action_id else False
            })
        return res

    def get_kpi_data(self, conf_obj):
        res = super(DashboardChart, self).get_kpi_data(conf_obj)
        if isinstance(res, dict) and res.get('type') != 'error':
            res.update({
                'drilldown_model': conf_obj.kpi_model if conf_obj.kpi_model else conf_obj.model,
                'drilldown_domain': conf_obj.kpi_domain if hasattr(conf_obj, 'kpi_domain') and conf_obj.kpi_domain else conf_obj.domain,
                'drilldown_action_id': self.item_action_id.id if self.item_action_id else False
            })
        return res
