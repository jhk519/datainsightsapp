# -*- coding: utf-8 -*-
"""
Created on Fri Jun 22 00:58:46 2018

@author: Justin H Kim
"""

#import reportlab
#import datetime

#   Settings are divided based on their related page. For settings that users can
# directly modify, they must be listed in the user_settings.ini file under a 
# section header that exactly matches the key in the backend_settings dict. 
#   This is handled by the settingsmanager Engine. As such, if the Section and/or 
# specific setting is not on the .ini file, it will not appear at all in settingsmanager.

backend_settings = {
    "settingsmanager":{
            "dbmanager": {
                "proper_title": "Database Manager",
                "settings":{
                    "loaddb_on_load": {
                        "proper_title": "Auto-load Databases On Startup",
                        "description": "If ON, app will automatically load the database on start-up.",
                        "type":"bool"
                    },
                    "loaddb_loc": {
                        "proper_title": "File Location for DB auto-load.",
                        "description": "For automatic loading on app startup, will use the file at this location.",
                        "type": "fileloc",
                    },
                    "automatic db export": {
                        "proper_title": "Auto-choose File Location for DB Export",
                        "description": "If ON, app will automatically export Databases. \nIf OFF, app will prompt user for name and location for export.",
                        "type": "bool",
                    },
                    "automatic export location": {
                        "proper_title": "Folder Location for Auto-choose DB Export",
                        "description": "If automatic db export is ON, will use this folder location for export.",
                        "type": "dirloc",
                    }
                }
            },
            "analysispage": {
                "proper_title": "Analysis Page",
                "settings":{
                    "automatic search export": {
                        "proper_title": "Auto-choose File Location for Results Exports",
                        "description":  "If ON, app will automatically choose location and filename of search result exports. \nIf OFF, app will prompt user for name and location for export.",
                        "type": "bool",
                    },
                    "automatic export location": {
                        "proper_title": "Folder Location for Auto-Choose Results Exports",
                        "description":  "If automatic db export is ON, will use this folder location for export.",
                        "type": "dirloc",
                    },

                    "automatically open excel exports":  {
                        "proper_title": "Open Excels After Results Exports",
                        "description": "If ON, Excel search result exports will automatically open.",
                        "type": "bool"
                    },
                    "event_list":  {
                        "proper_title": "List of Events",
                        "description": "List of Events to be used in search results.",
                        "type": "event_dates",
                    },
                    "breakdown colors":  {
                        "proper_title": "Colors for Multi-Line Breakdowns",
                        "description": "When splitting data into multiple breakdowns, will use the following colors in order.",
                        "type": "colors"
                    },
                    "ignore_numbers": {
                        "proper_title":"Customer Phone Numbers to Ignore",
                        "description":"When applying metrics involving 'Customer's Nth Order', orders using these numbers will be ignored and set aside separately.",
                        "type":"phone_numbers",
                    },
                }
            },
            "querypanel": {
                "proper_title": "Query Panel",
                "settings":{
                    "setdates_gap":  {
                        "proper_title": "Number of Days for Auto-Setting of Dates",
                        "description": "If Set Dates on Start-up is ON, will set this many days between Start and End Dates.",
                        "type": "int",
                    },
                    "setdates_from_date": {
                        "proper_title": "End Date for Dates Auto-Setting",
                        "description":  "If Sets Dates on Start-up is ON, will use this date as the END date.",
                        "type": "date",
                    },
                    "setdates_on_load": {
                        "proper_title": "Set Dates on Start-up",
                        "description":  "If ON, will set dates automatically on app start-up. If OFF, date will be Yesterday.",
                        "type": "bool",
                    },
                }
            },
            "productviewer": {
                "proper_title": "Product Viewer",
                "settings":{
                    "automatic export location":  {
                        "proper_title": "Folder Location for Data Exports",
                        "description": "Folder location for exporting data from Product Viewer.",
                        "type": "dirloc",
                    }
                }
            }
    },
            
    "dbmanager":{
        "URL for Online DB Download":"https://furyoo.pythonanywhere.com/static/DH_DBS.pickle",
        "automatic db export": True,        
        "automatic export location":".//exports//databases",
        "loaddb_on_load": True, 
        "loaddb_loc": "databases//DH_DBS.pickle",
        
        "db_build_config": {
            "odb": {
                "data": None,
                "proper_title": "Order Database",
                "core": "order_data",
                "appends_list":[],
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
            "pdb": {
                "data": None,
                "proper_title":"Product Database",
                "core": "product_data",
                "appends_list": [],
                "match_on_key": "sellmate_barcode"
            },
            
            "cdb":{
                "data":None,
                "proper_title":"Customer Database",
                "core":"customer_data",
                "appends_list":[],
                "match_on_key":"customer_phone"
            }
        },
            
        "header_ref" :{
            "order_data": {
                "주문번호": "order_id",
                "품목별주문번호": "order_part_id",
        
                "주문일시": "date",
                "배송시작일":"date_shipping",
                "결제일시(입금확인일)": "date_payment",
                "총주문금액(KRW)": "total_original_price",
                "총배송비(KRW)": "original_shipping_fee",
                "총결제금액(KRW)": "total_net_price",
                
                "회원등급추가할인금액": "total_membership_level_discount",
                "사용한적립금액": "total_membership_points_discount",
                "예치금": "total_cash_credit_discount",
                "쿠폰할인금액": "total_coupon_discount",
                "결제수단": "payment_method",
                "매출경로": "shopping_platform",
                "주문경로(PC/모바일)": "pc_or_mobile_platform",
                
                
                "주문자휴대전화": "customer_phone_number",
                "주문자ID": "customer_id",
                "카데고리": "category",
                
                "취소구분":"cancel_status",
        
                "상품구매금액(KRW)": "product_price",
                "상품별추가할인금액": "product_standard_discount",
                "수량": "product_quantity",
                
                "주문상품명": "product_name",
                "상품코드": "product_cafe24_code",
                "상품자체코드": "product_hcode",
                "상품옵션":"product_option"
            },
            "traffic_data": {
                "날짜": "date",
                "신규방문자": "new_visitors_count",
                "재방문자": "returning_visitors_count",
        
                "총PC방문자수": "pc_visitors_count",
                "모바일웹방문자수": "mobile_visitors_count",
                "앱방문자수": "app_visitors_count",
        
                "페이지뷰": "total_pageviews",
        
                "쿠딩매출": "kooding_revenue",
                "PC매출(쿠딩제외)": "pc_revenue",
                "모바일웹매출": "mobile_revenue",
                "지그재그매출": "zigzag_revenue",
                "앱매출": "app_revenue",
        
                "PC주문건수": "pc_orders_count",
                "모바일웹주문건수": "mobile_orders_count",
                "앱주문건수": "app_orders_count",
            },
                
            "referral_data": {
                "날짜": "date",
                "방문채널": "source_channel",
        
                "방문자": "visitors_count",
                "구매건수": "order_count",
                "매출": "revenue"
            },
            "product_data": {
                "바코드번호": "sku_sellmate_code",
                "상품분류": "product_brand",
                "상품명": "product_name",
                "옵션내용": "sku_option_text",
                "대표이미지주소": "product_img_url",
                "상품코드": "product_cafe24_code",
                "상품등록일자": "upload_date",
                "상품메모1": "product_h_code",
                "옵션메모3": "sku_h_code",                        
            },
                    
            "customer_data": {
                "주문자휴대전화": "customer_phone",
                "주문자명": "customer_name"
            },
        }              
    },        
            
    "productviewer":{
        "automatic export location":".//exports//product_customer_lists"
    },
            
    "analysispage":{     
        "automatic search export": True,
        "automatic export location": "exports\search_results", 
        "automatically open excel exports": True,
        "event_list":"04/29 Sale,20180429,20180429%%05/01-05/06 Event,20180501,20180506%%05/01-05/06 Event,20180517,20180520",
        "breakdown colors": "#008080-#004993-#fc5f7a-#00ff40-#d7d700-#888888-#8000ff-#f5010a-#fee0e6-#180105-#ff8040-#3c9dff",
        "ignore_numbers": "010-0000-0000%%000-0000-0000%%010-000-0000%%010-1111-1111%%010-111-1111%%010-0000-0000%%nan%%0",
    },
    "querypanel":{
        "setdates_on_load": True,
        "setdates_gap":"14",
        "setdates_from_date":"20180401",                 
        "queries":{
            "order_data-date_series": {
                "proper_title": "Order Data-Date Series",
                "x_axis_type":"date_series",
                "data_filters": ["start_end_dates","platform","category_or_product",],
                "metrics": {
                    "count_of_items": {
                        "proper_title": "Count Of Items",
                        "metric_types": ["Include Cancelled Items", "Exclude Cancelled Items"],
                        "data_types": ["Sum","Percentage"],
                        "breakdown_types": ["None", "Top Products", "Top Categories", "Gen. Platform","Spec. Platform"]
                    },
                    "revenue_by_item":{
                        "proper_title": "Revenue By Item",
                        "metric_types": ["Before Discount", "After Discount"],
                        "data_types": ["Sum","Percentage","Average"],
                        "breakdown_types": ["None", "Top Products", "Top Categories", "Gen. Platform","Spec. Platform"]
                    },
                    "count_of_orders":{
                        "proper_title": "Count Of Orders",
                        "metric_types": ["Include Fully Cancelled Orders", "Exclude Fully Cancelled Orders"],
                        "data_types": ["Sum","Percentage"],
                        "breakdown_types": ["None", "Gen. Platform","Spec. Platform","Customer's Nth Order"]                        
                    },
                    "revenue_by_order":{
                        "proper_title": "Revenue By Order",
                        "metric_types": ["Orig. Price, Incl. Cncld Orders", 
                                         "Net. Price, Incl. Cncld Orders",
                                         "Orig. Price, Excl. Cncld Orders",
                                         "Net. Price, Excl. Cncld Orders"],
                        "data_types": ["Sum","Percentage","Average"],
                        "breakdown_types": ["None","Gen. Platform","Spec. Platform"]                     
                    },
                    "order_size":{
                        "proper_title": "Order Size",
                        "metric_types": ["Include Cancelled Items", "Exclude Cancelled Items"],
                        "data_types": ["Sum","Average"],
                        "breakdown_types": ["None","Gen. Platform","Spec. Platform"]                        
                    },
                    "count_of_cancels_by_item":{
                        "proper_title": "Count of Cancels By Item",
                        "metric_types": ["Include Full Order Cancels", "Exclude Full Order Cancels"],
                        "data_types": ["Sum","Percentage","% of Total Sales (BETA)"],
                        "breakdown_types": ["None","Top Products","Top Categories","Gen. Platform","Spec.Platform"]
                    }
                }
            },
            "traffic_data-date_series": {
                "proper_title": "Traffic Data-Date Series",
                "x_axis_type": "date_series",
                "data_filters": ["start_end_dates"],
                "metrics": {
                    "count_of_pageviews": {
                        "proper_title": "Count Of Pageviews",
                        "metric_types": ["None"],
                        "data_types": ["Sum"],
                        "breakdown_types": ["None"]
                    },
                    "count_of_visitors": {
                        "proper_title": "Count Of Visitors",
                        "metric_types": ["None"],
                        "data_types": ["Sum","Percentage"],
                        "breakdown_types": ["None","Device","New/Returning"]
                    },                
                }
            }
        }
    },
            
    "multigrapher":{
        "automatic export location":"exports\multigrapher",
        "presetpages":[
            {
                "pagename":"PAGE1",
                "request_packs": []
            }
        ]
    },
    "graphframe":{
        "event_colors":"firebrick-dodgerblue-seagreen-darkorchid-gray-yellow-salmon-deeppink"
    },
    "datatable":{
        "gg":"hh"
    }
}
    
           