# -*- coding: utf-8 -*-
"""
Created on Fri Mar 23 18:25:30 2018
@author: Justin H Kim
 """
import reportlab
import datetime


backend_settings = {


    "db_ref": {
        "odb": {
            "data": None,
            "proper_title": "Order Database",
            "core": "order_data",
            "appends_list": ["cancel_data", "shipping_data", "return_data"],
            "match_on_key": "order_part_id"
        },
        "tdb": {
            "data": None,
            "proper_title":"Traffic Database",
            "core": "traffic_data",
            "appends_list": [],
            "match_on_key": "date"
        },
        "rdb": {
            "data": None,
            "proper_title":"Referral Database",
            "core": "referral_data",
            "appends_list": [],
            "match_on_key": "date"
        },
        "sm_odb": {
            "data": None,
            "proper_title":"Sellmate Order Database",
            "core": "sellmate_order_excel",
            "appends_list": [
                "sellmate_cancel_excel",
                "sellmate_shipping_excel",
            ],
            "match_on_key": "sellmateIndex"
        },
        "pdb": {
            "data": None,
            "proper_title":"Product Database",
            "core": "product_data",
            "appends_list": [],
            "match_on_key": "sku_code"
        },
        "sm_stdb": {
            "date": None,
            "proper_title":"Sellmate Stock Database",
            "core": "sellmate_stock_excel",
            "appends_list": [],
            "match_on_key": "sellmateBarcode"
        }
    },

    "accounts_to_pages_ref": {
        "admin": {
            "pages": [
                "Graph",
            ]
        }
    },

    "axis_panel_names": {
        "titles": [
            "Left Axis",
            "Right Axis"
        ],
    },

    "pages_to_scopes_ref": {
        "Graph": [
            "General",
            "Filter By Product",
            "Product Rankings"
        ]
    },

    "scopes_to_metrics_ref": {
        "Filter By Product": {
            "metrics": [
                "Order Lifecycle",
                "Days To Ship",
                "Days Waiting To Ship",
                "Cancel Reasons",
                "Sales - Payment and Discount",
            ],
            "extra": {
                "use": True,
                "text": "Cafe24 Code",
                "type": "entry",
                "fill": "P0000PGG"
            }

        },
        "General": {
            "metrics": [
                "Visitors By Device",
                "Revenue By Device",
                "Orders By Device",
                "Total Pageviews",
                "AOV",
                "AOS"
            ],
            "extra": {
                "use": False,
                "text": "NO_TEXT",
                "type": "text"
            }
        },
        "Product Rankings": {
            "metrics": [
                "Top 10 By Orders",
                "Top 10 By Returns",
            ],
            "extra": {
                "use": False,
                "text": "NO_TEXT",
                "type": "text"
            }
        }
    },

    # Queries represent a single line, or specifically data-list.
    # Metrics differentiate whether a secondary axis is possible, help to isolate
    #   loner queries, and most importantly (in relation to the first point), they
    #   group queries in a way that ensures they can share a Y-axis.
    # Note that whether or not an XAXIS can be shared is not defined by being in the same
    # Metric group.
    "metrics_to_queries_ref": {
        "Top 10 By Orders": {
            "queries": [
                "Top 10 By Orders",
            ],
            "type": "bar",
            "exclude": True,
            "xaxis_label": "Product Code",
            "yaxis_label": "Order Quantity"
        },
        "Top 10 By Returns": {
            "queries": [
                "Top 10 By Returns",
            ],
            "type": "bar",
            "exclude": True,
            "xaxis_label": "Product Code",
            "yaxis_label": "Quantity"
        },
        "Order Lifecycle": {
            "queries": ["total_order_quantity",
                        "total_cancel_quantity",
                        "total_return_quantity"
                        ],
            "type": "line",
            "exclude": False,
            "xaxis_label": "Date",
            "yaxis_label": "Quantity"
        },
        "Cancel Reasons": {
            "queries": ["cancel_reasons"],
            "type": "string-bar",
            "exclude": True,
            "xaxis_label": "Reasons",
            "yaxis_label": "Quantity",
        },
        "Sales - Payment and Discount": {
            "queries": ["net_payment", "net_discount"],
            "exclude": False,
            "type": "line",
            "xaxis_label": "Date",
            "yaxis_label": "Total KRW",
        },
        "Visitors By Device": {
            "queries": ["visitors_mobile",
                        "visitors_pc",
                        "visitors_app",
                        "visitors_all"],
            "exclude": False,
            "type": "line",
            "xaxis_label": "Date",
            "yaxis_label": "Visitors",
        },
        "Revenue By Device": {
            "queries": [
                "revenue_all",
                "revenue_app",
                "revenue_pc",
                "revenue_mobile",
                "revenue_kooding",
            ],
            "exclude": False,
            "xaxis_label": "Date",
            "type": "line",
            "yaxis_label": "Total KRW",
        },
        "Orders By Device": {
            "queries": [
                "orders_app",
                "orders_pc",
                "orders_mobile",
                "orders_all",
            ],
            "exclude": False,
            "xaxis_label": "Date",
            "type": "line",
            "yaxis_label": "Quantity",
        },

        "Total Pageviews": {
            "queries": ["total_pageviews"],
            "exclude": False,
            "xaxis_label": "Date",
            "type": "line",
            "yaxis_label": "Pageviews",
        },
        "AOV": {
            "queries": ["average_order_value"],
            "exclude": False,
            "xaxis_label": "Date",
            "type": "line",
            "yaxis_label": "Value KRW",
        },
        "AOS": {
            "queries": ["average_order_size"],
            "exclude": False,
            "xaxis_label": "Date",
            "type": "line",
            "yaxis_label": "Quantity",
        },
        "Days Waiting To Ship": {
            "queries": ["days_unsent"],
            "exclude": True,
            "xaxis_label": "Number of Days",
            "yaxis_label": "Quantity",
            "type": "pie",
        },
        "Days To Ship": {
            "queries": ["days_to_ship"],
            "exclude": True,
            "xaxis_label": "Number of Days",
            "type": "pie",
            "yaxis_label": "Quantity",
        },
    }
}
