from odoo import models, fields

class Dashboard(models.Model):
    _inherit = 'dashboard.dashboard'

    enable_global_filter = fields.Boolean(string="Enable Global Date Filter", default=False)

    def get_charts_details(self):
        res = super(Dashboard, self).get_charts_details()
        # Ensure we attach the boolean explicitly to the end of the payload
        if isinstance(res, list):
            res.append(self.enable_global_filter)
        return res

class DashboardChart(models.Model):
    _inherit = 'dashboard.chart'

    def get_chart_data(self, chart_type, name, isDirty=False, data=False, extra_action=False, print_options=False):
        if not isDirty and isinstance(data, dict) and data.get("date_filter_option") == "custom":
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            # Bind our dates to environment context safely
            self = self.with_context(global_filter_start=start_date, global_filter_end=end_date)
            # Wipe data out so the original unpatched method doesn't trip on unexpected formats
            data = False
        return super(DashboardChart, self).get_chart_data(chart_type, name, isDirty, data, extra_action, print_options)

    def _init_configuration(self):
        conf, domain = super(DashboardChart, self)._init_configuration()
        start_date = self.env.context.get("global_filter_start")
        end_date = self.env.context.get("global_filter_end")
        
        if start_date and end_date:
            if self.date_filter_field_id:
                date_field = self.date_filter_field_id.name
                conf.domain.append((date_field, ">=", start_date))
                conf.domain.append((date_field, "<=", end_date))
                domain.append((date_field, ">=", start_date))
                domain.append((date_field, "<=", end_date))
                conf.date_filter_option = 'none'
                
            if hasattr(self, 'kpi_date_filter_field_id') and self.kpi_date_filter_field_id:
                kpi_field = self.kpi_date_filter_field_id.name
                conf.kpi_domain.append((kpi_field, ">=", start_date))
                conf.kpi_domain.append((kpi_field, "<=", end_date))
                conf.kpi_date_filter_option = 'none'
                
        return conf, domain
