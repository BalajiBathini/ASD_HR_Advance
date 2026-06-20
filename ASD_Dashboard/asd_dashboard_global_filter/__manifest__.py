{
    "name": "ASD Dashboard Global Filter",
    "version": "1.1",
    "summary": "Global Date Filter for ASD Dashboard",
    "author": "Balaji Bathini tetet",
    "sequence":1,
    "category": "web",
    "depends": ["asd_cust_dashboard"],
    "data": [
        "views/dashboard_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "asd_dashboard_global_filter/static/src/js/dashboard_amcharts_extended.js",
            "asd_dashboard_global_filter/static/src/xml/dashboard_amcharts_extended.xml",
            "asd_dashboard_global_filter/static/src/css/global_filter.css",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
