# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 15:57:26 2018

@author: user
"""

#import request_tools
#import webbrowser
import requests
#import K_CONST
#import easygui
#import base64
from requests.auth import HTTPBasicAuth
from pprint import pprint as PRETTYPRINT
import pandas as pd
import time
import logging
import datetime
from os import system
import json

REDIRECT_URI =  "https://ppbapps.com/"        
CLIENT_ID = "bz1WjcWBEFFnbNyZFQbUiD"     
CLIENT_SECRET = "l6LBt2mCOtlvE0abK4xWYC"  
SCOPES = "mall.read_application,mall.write_application,mall.read_category,mall.read_customer,mall.read_order,mall.read_product,mall.read_salesreport"        
AUTHORIZATION_BASE_URL = "https://chuukr.cafe24api.com/api/v2/oauth/authorize?"        
AUTHORIZATION_PARAMS = "response_type=code&client_id={}&redirect_uri={}&scope={}".format(CLIENT_ID,REDIRECT_URI,SCOPES)
FINAL_URL = AUTHORIZATION_BASE_URL + AUTHORIZATION_PARAMS

LOG = logging.getLogger(__name__).info
LOG("{} Init.".format(__name__))    
BUG = logging.getLogger(__name__).debug 

def main(call_key,token,kwarg_dict):
    LOG("Main called for {}".format(call_key))
    LOG("Keyword Arg Dict:{}".format(kwarg_dict))
    call_ref = {
        "new_access": (get_new_access_token,""),
        "new_refresh": (refresh_access,""),
        "get_orders": (get_orders,"orders"),
        "get_order_items": (get_order_items,"items"),
        "get_product": (get_product,"products"),
        "get_sales_volume": (get_sales_volume,"salesvolume"),
        "get_customer": (getcustomer,"customers"),
        "get_categories": (getcategories,"categories"),
        "get_order_count": (get_count_of_orders_in_range,"count")
    }        
    
    call_func = call_ref[call_key][0]
    response_keyword = call_ref[call_key][1]
    
    LOG("Requesting data...")
    response = call_func(token,**kwarg_dict)
    LOG("Received data response.")
#    if response.headers["X-Api-Call-Limit"][0:2] == "29":
#        time.sleep(1)
    if not response.status_code == "200" and not response.status_code == 200:
        
        if response.status_code == 404:
            print(response.text)
            error_msg = "404!"
        elif response.status_code == "429" or response.status_code == 429:
            error_msg = "Call limit reached! {}".format(response.headers["X-Api-Call-Limit"])
#            print(response.headers["X-Api-Call-Limit"][0:2])
        else:    
            error = response.json()["error"]["message"]
            if "주문번호" in error:
                error_msg = "ERROR! Should not request order_item_id!"
            elif "API를 찾을" in error:
                error_msg = "ERROR! Cannot find this order_id"
            else:
                error_msg = "ERROR! UNKNOWN!"
                print(response.text)
        return error_msg
    else:
        if response_keyword == "":
            return response.json()
        else:
#            PRETTYPRINT(response.json())
            return response.json()[response_keyword]   

def get_new_access_token(auth_code,**kwargs):
    token_host = "https://chuukr.cafe24api.com/api/v2/oauth/token?"
    response = requests.post(
        token_host, 
        headers={"Content-Type":"application/x-www-form-urlencoded"},
        data={"redirect_uri":"https://ppbapps.com/",
              "state":"1212",                   
              "grant_type":"authorization_code",
              "code":auth_code},
        auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)) 
    
    print("-------")
#    PRETTYPRINT(response.json())
    print("-------")
    return response

def refresh_access(refresh_token,**kwargs):
    response = requests.post("https://chuukr.cafe24api.com/api/v2/oauth/token?", 
          headers={"Content-Type":"application/x-www-form-urlencoded"},
          data={"refresh_token":refresh_token,               
                "grant_type":"refresh_token",
                },
          auth=HTTPBasicAuth('bz1WjcWBEFFnbNyZFQbUiD', 'l6LBt2mCOtlvE0abK4xWYC')
    )    
    
#    PRETTYPRINT(response.text)
    print("-------")
#    PRETTYPRINT(response.json())
    print("-------")
    return response

def get_count_of_orders_in_range(access_token,start_date="2018-07-15",end_date="2018-07-15"):
    temp_parameters = {"start_date":start_date,
                       "end_date":end_date,
                       "date_type":"order_date",
#                       "order_status":"N00,N10,N20,N21,N22,N30,N40",
                       }  
    url = __generate_request_url('https://chuukr.cafe24api.com/api/v2/admin/orders/count?',
                                             temp_parameters)
    return requests.get(url,headers={"Content-Type":"application/json",
                                     "Authorization": "Bearer {}".format(access_token)})
    
def get_orders(access_token,order_ids=None,offset=0,start_date="2018-08-01",end_date="2018-08-01"):
    
    temp_parameters = {"start_date":start_date,
                       "end_date":end_date,
                       "limit": 500,
                       "date_type":"order_date",
#                       "order_status":"N00,N10,N20,N21,N22,N30,N40",
                       "offset":offset,
                       "embed":"items",
                       }    
    if not order_ids is None:
        if type(order_ids) is str: 
            temp_parameters["order_id"] = order_ids
        elif type(order_ids) is list: 
            temp_parameters["order_id"] = ",".join(order_ids)
        else: 
            return "Invalid order_ids"
        
    url = __generate_request_url('https://chuukr.cafe24api.com/api/v2/admin/orders?',
                                 temp_parameters)
    
    return requests.get(url, headers={"Content-Type":"application/json",
                                      "Authorization": "Bearer {}".format(access_token)})             

def get_order_items(access_token,order_id="20180716-0000141"):
    url = "https://chuukr.cafe24api.com/api/v2/admin/orders/{}/items".format(order_id)
    return requests.get(url, headers={"Content-Type":"application/json",
                                      "Authorization": "Bearer {}".format(access_token)})    
        
def get_product(access_token,product_code="P000BFFF"):
    temp_parameters = {"product_code":product_code}
    url = __generate_request_url("https://chuukr.cafe24api.com/api/v2/admin/products?",
                                             temp_parameters)
    return requests.get(url, headers={"Content-Type":"application/json",
                                      "Authorization": "Bearer {}".format(access_token)})    
    
def get_sales_volume(access_token,product_no="21092",start_date="2018-08-01",end_date="2018-08-01"):
    temp_parameters = {"product_no":str(product_no),
                       "start_date":start_date,
                       "end_date":end_date}
    url = __generate_request_url("https://chuukr.cafe24api.com/api/v2/admin/reports/salesvolume?",
                                             temp_parameters)
    return requests.get(url,headers={"Content-Type":"application/json",
                                  "Authorization": "Bearer {}".format(access_token)})      
    
def getcustomer(access_token,customer_phone="000-000-000"):
    temp_parameters = {"cellphone":str(customer_phone)}
    url = __generate_request_url("https://chuukr.cafe24api.com/api/v2/admin/customers?",
                                             temp_parameters)
    return requests.get(url,headers={"Content-Type":"application/json",
                                  "Authorization": "Bearer {}".format(access_token)} )    
    
def getcategories(access_token,**kwargs):
    temp_parameters = {"limit":100}
    url = __generate_request_url("https://chuukr.cafe24api.com/api/v2/admin/categories?",
                                             temp_parameters)
    return requests.get(url,headers={"Content-Type":"application/json",
                                     "Authorization": "Bearer {}".format(access_token)})    



def __generate_request_url(url,parameter_dict):
    url_total_string = ""
    for key,value in parameter_dict.items():
        url_total_string = url_total_string + "&" + str(key) + "=" + str(value) 
    finalurl = url + url_total_string
    LOG(finalurl)
    return finalurl    

