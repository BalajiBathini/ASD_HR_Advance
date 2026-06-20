{
    "name": "ASD Dashboard Drilldown",
    "version": "1.0",
    "summary": "KPI and Tile drilldown enhancements for ASD Dashboard",
    "author": "Balaji Bathini",
    "sequence":1,
    "category": "web",
    "depends": ["asd_cust_dashboard"],
    "data": [
    ],
    "assets": {
        "web.assets_backend": [
            "asd_dashboard_drilldown/static/src/js/kpi_view.js",
            "asd_dashboard_drilldown/static/src/js/tile_view.js",
            "asd_dashboard_drilldown/static/src/xml/kpi_layout.xml",
            "asd_dashboard_drilldown/static/src/xml/tile_layout.xml",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
