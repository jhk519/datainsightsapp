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
#                "appends_list": ["cancel_data","return_data"],
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
                "match_on_key": "sku_code"
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
                
                
                "주문자휴대전화": "customer_phone_number",
                "주문자ID": "customer_id",
                
                "취소구분":"cancel_status",
        
                "상품구매금액(KRW)": "product_price",
                "상품별추가할인금액": "product_standard_discount",
                "수량": "product_quantity",
                
                "주문상품명": "product_name",
                "상품코드": "product_cafe24_code",
                "상품옵션":"product_option"
            },
#            "cancel_data": {
#                "주문번호": "order_id",
#                "품목별주문번호": "order_part_id",
#                "취소접수구분": "reason_cancelled",
#                "취소접수일": "date_cancelled"
#            },
#            "return_data": {
#                "주문번호": "order_id",
#                "품목별주문번호": "order_part_id",
#                "환불완료일": "date_returned"
#            },
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
                "product_code": "product_code",
                "option_text": "option_text",
                "main_image_url": "main_image_url",
                "sku_image_url": "sku_image_url",
                "category": "category",
#                "상품공급처명": "vendor_name",
#                "사입상품명": "vendor_code",
                "sku_code": "sku_code",     
#                "원가": "vendor_price",                      
            },
                    
            "customer_data": {
                "주문자휴대전화": "customer_phone",
                "주문자명": "customer_name"
            },
        }              
    },
            
#            "extra":self.extra_var.get(),
#            "x_axis_label": self.x_axis_type.get(),
#            "mirror_days": self.mirror_days_var.get(),            
#            "left": {
#                "gtype":self.axis_panels["left"]["gtype"],
#                "db-type": self.axis_panels["left"]["dbtype"],
#                "metric": self.axis_panels["left"]["metric"],
#                "queries": left_comp,
#            },
#            "right": {
#                "gtype":self.axis_panels["right"]["gtype"],
#                "db-type": self.axis_panels["right"]["dbtype"],
#                "metric": self.axis_panels["right"]["metric"],
#                "queries": right_comp,
#                #selected_query_pack = [stvar, label, choose_color, delete]      
#            }, 
#            "start": self.start_date,
#            "end": self.end_date,
#            "hold_y": self.hold_y_var.get()                
            

            
    "productviewer":{
        "automatic export location":".//exports//product_customer_lists"
    },
            
    "analysispage":{     
        "automatic search export": True,
        "automatic export location": "exports\search_results",
        "auto_name_exports": True,  
        "auto_query": True,        
    },

    "querypanel":{
        "setdates_on_load": True,
        "setdates_gap":"14",
        "setdates_from_date":"20180128",             
        "colors_preferred": "firebrick-dodgerblue-seagreen-darkorchid-gray-yellow-salmon-deeppink-coral",
        "categories": ["Orders","Cashflow","Traffic","Logistics","Product Rankings","Cancels"],
        
        "queries_ref": {
            "Average Order Size":{
            	"category": "Orders",
            	"x-axis-label": "Date",
            	"y-axis-label": "Order Size (Part-Orders)",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "odb"
            },
            "Average Order Value":{
            	"category": "Orders",
            	"x-axis-label": "Date",
            	"y-axis-label": "Order Value (KRW)",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "odb"
            },
            "Orders By App":{
            	"category": "Orders",
            	"x-axis-label": "Date",
            	"y-axis-label": "Quantity (Orders)",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "tdb"
            },
            "Orders By PC":{
            	"category": "Orders",
            	"x-axis-label": "Date",
            	"y-axis-label": "Quantity (Orders)",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "tdb"
            },
            "Orders By Mobile":{
            	"category": "Orders",
            	"x-axis-label": "Date",
            	"y-axis-label": "Quantity (Orders)",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "tdb"
            },
            "Orders By All Devices":{
            	"category": "Orders",
            	"x-axis-label": "Date",
            	"y-axis-label": "Quantity (Orders)",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "tdb"
            },
            "Total Orders By Item":{
            	"category": "Orders",
            	"x-axis-label": "Date",
            	"y-axis-label": "Quantity (Part-Orders)",
            	"can_filter":"pcode",
            	"gtype": "line",
            	"db-req": "odb"
            },
            "Total Cancels By Item":{
            	"category": "Orders",
            	"x-axis-label": "Date",
            	"y-axis-label": "Quantity (Part-Orders)",
            	"can_filter":"pcode",
            	"gtype": "line",
            	"db-req": "odb"
            },
            "Total Returns By Item":{
            	"category": "Orders",
            	"x-axis-label": "Date",
            	"y-axis-label": "Quantity (Part-Orders)",
            	"can_filter":"pcode",
            	"gtype": "line",
            	"db-req": "odb"
            },
            "Revenue By All Devices":{
            	"category": "Cashflow",
            	"x-axis-label": "Date",
            	"y-axis-label": "Cash (KRW)",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "tdb"
            },
            "Revenue By App":{
            	"category": "Cashflow",
            	"x-axis-label": "Date",
            	"y-axis-label": "Cash (KRW)",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "tdb"
            },
            "Revenue By PC":{
            	"category": "Cashflow",
            	"x-axis-label": "Date",
            	"y-axis-label": "Cash (KRW)",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "tdb"
            },
            "Revenue By Mobile":{
            	"category": "Cashflow",
            	"x-axis-label": "Date",
            	"y-axis-label": "Cash (KRW)",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "tdb"
            },
            "Revenue By Kooding":{
            	"category": "Cashflow",
            	"x-axis-label": "Date",
            	"y-axis-label": "Cash (KRW)",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "tdb"
            },
            "Net Discount Given":{
            	"category": "Cashflow",
            	"x-axis-label": "Date",
            	"y-axis-label": "Cash (KRW)",
            	"can_filter":"pcode",
            	"gtype": "line",
            	"db-req": "odb"
            },
            "Net Payments Received":{
            	"category": "Cashflow",
            	"x-axis-label": "Date",
            	"y-axis-label": "Cash (KRW)",
            	"can_filter":"pcode",
            	"gtype": "line",
            	"db-req": "odb"
            },
            "Total Pageviews":{
            	"category": "Traffic",
            	"x-axis-label": "Date",
            	"y-axis-label": "Pageviews",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "tdb"
            },
            "Visitors By All Devices":{
            	"category": "Traffic",
            	"x-axis-label": "Date",
            	"y-axis-label": "Visitors",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "tdb"
            },
            "Visitors By Mobile":{
            	"category": "Traffic",
            	"x-axis-label": "Date",
            	"y-axis-label": "Visitors",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "tdb"
            },
            "Visitors By PC":{
            	"category": "Traffic",
            	"x-axis-label": "Date",
            	"y-axis-label": "Visitors",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "tdb"
            },
            "Visitors By App":{
            	"category": "Traffic",
            	"x-axis-label": "Date",
            	"y-axis-label": "Visitors",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "tdb"
            },
            "Unsent Orders Days to Ship":{
            	"category": "Logistics",
            	"x-axis-label": "Duration in Days",
            	"y-axis-label": "Quantity (Part-Orders)",
            	"can_filter":"pcode",
            	"gtype": "bar",
            	"db-req": "odb"
            },
            "Sent Orders Days To Ship":{
            	"category": "Logistics",
            	"x-axis-label": "Duration in Days",
            	"y-axis-label": "Quantity (Part-Orders)",
            	"can_filter":"pcode",
            	"gtype": "bar",
            	"db-req": "odb"
            },
            "Top 10 By Orders":{
            	"category": "Product Rankings",
            	"x-axis-label": "Product Codes",
            	"y-axis-label": "Quantity (Part-Orders)",
            	"can_filter":None,
            	"gtype": "bar",
            	"db-req": "odb"
            },
            
            "Top 10 By Returns":{
            	"category": "Product Rankings",
            	"x-axis-label": "Product Codes",
            	"y-axis-label": "Quantity (Part-Orders)",
            	"can_filter":None,
            	"gtype": "bar",
            	"db-req": "odb"
            },
            "Cancel Reasons":{
            	"category": "Cancels",
            	"x-axis-label": "Reasons",
            	"y-axis-label": "Quantity (Part-Orders)",
            	"can_filter":"pcode",
            	"gtype": "bar",
            	"db-req": "odb"
            },
            "Conversion Rate":{
            	"category": "Traffic",
            	"x-axis-label": "Date",
            	"y-axis-label": "Conversion Rate (Purchases / Visitors)",
            	"can_filter":None,
            	"gtype": "line",
            	"db-req": "tdb"
            },
        }
    },
    "multigrapher":{
        "automatic export location":"exports\multigrapher",
        "presetpages":[
#                PAGE 1
            {
                "pagename":"PAGE1",
                "slots": [
                 ]
             }
        ]
    }            
}
    
           