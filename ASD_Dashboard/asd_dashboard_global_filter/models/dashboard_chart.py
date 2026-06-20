from odoo import models
from odoo.osv import expression
from datetime import datetime

class DashboardChart(models.Model):
    _inherit = 'dashboard.chart'

    def _handle_dirty_data(self, conf, data):
        super()._handle_dirty_data(conf, data)
        # Apply global custom date filter if specified
        if data.get('date_filter_option') == 'custom':
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            
            # We strictly enforce ISO strings or format to Odoo datetime bounds if necessary.
            # But the javascript overrides usually pass standard format '%Y-%m-%d %H:%M:%S' or iso.
            
            if start_date and end_date:
                # 1. Main model domain
                # Find the main field to filter on
                field_name = getattr(conf, 'date_filter_field', False)
                if not field_name:
                    field_name = self.date_filter_field_id.name
                
                if field_name:
                    custom_domain = [(field_name, '>=', start_date), (field_name, '<=', end_date)]
                    if isinstance(conf.domain, list):
                        conf.domain = expression.AND([conf.domain, custom_domain])
                
                # 2. KPI model domain
                kpi_field_name = self.kpi_date_filter_field_id.name
                if kpi_field_name and hasattr(conf, 'kpi_domain') and isinstance(conf.kpi_domain, list):
                    kpi_custom_domain = [(kpi_field_name, '>=', start_date), (kpi_field_name, '<=', end_date)]
                    conf.kpi_domain = expression.AND([conf.kpi_domain, kpi_custom_domain])
