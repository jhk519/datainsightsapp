# -*- coding: utf-8 -*-
"""
Created on Sat Sep 29 13:21:44 2018

@author: Justin H Kim
"""

# Standard Modules 
from pprint import pprint as PRETTYPRINT
import collections
import copy
from datetime import datetime, timedelta
import logging

# Non-Standard Modules
import workdays
import pandas as pd

LOG = logging.getLogger(__name__).info
LOG("{} Init.".format(__name__))    
BUG = logging.getLogger(__name__).debug  

"""
        {'data_filters': {'category_or_product': 'All',
                          'category_or_product_entry': 'P0000BHV',
                          'end_datetime': datetime.date(2018, 5, 15),
                          'platform': 'All',
                          'start_datetime': datetime.date(2018, 4, 15)},
         'graph_options': {'axis': 'right',
                           'color': '#0000ff',
                           'custom_name': 'P0000BHV-Revenue',
                           'line_style': '--'},
         'metric_options': {'breakdown': 'Platform',
                            'data_type': 'Sum',
                            'metric': 'Revenue By Item',
                            'number_of_rankings': 2,
                            'metric_type': 'Before Discount'},
         'result_options': {'aggregation_period': 'Weekly',
                            'aggregation_type': 'Average',
                            'compare_to_days': '365',
                            }}
"""


def main(rpack, di_dbs,mirror_breakdown=None):
    raw_metrics_ref = {
        "Count of Items": [count_of_items,"odb","pdb"],
#        "revenue_by_item": [revenue_by_item,"odb","pdb"],
#        "count_of_orders": [count_of_orders,"odb","pdb"],
#        "revenue_by_order": [revenue_by_order,"odb","pdb"],
#        "order_size": [order_size,"odb","pdb"],
#        "pageviews": [pageviews,"tdb",None],
#        "visitors": [visitors,"tdb",None],
    }    
    xtype = rpack["x_axis_type"]
    data_cfg = rpack["data_filters"]
    metric_cfg = rpack["metric_options"]
    result_cfg = rpack["result_options"]
    graph_cfg = rpack["graph_options"]
    
    raw_metric_str = metric_cfg["metric"]
    raw_metric_func = raw_metrics_ref[raw_metric_str][0]
    req_db = raw_metrics_ref[raw_metric_str][1] 
    
    # FILTER DBS
    filtered_db = get_filtered_dbs(di_dbs,req_db,data_cfg,xtype)
    aux_db = di_dbs[raw_metrics_ref[raw_metric_str][2]]
    
    # GATHER RAW METRIC DATA
    if xtype == "date_series":
#        date_list = _gen_dates(data_cfg["start_datetime"], data_cfg["end_datetime"] )
        date_list = _gen_dates_list(data_cfg["start_datetime"], data_cfg["end_datetime"])
        return raw_metric_func(filtered_db,aux_db,date_list,metric_cfg,mirror_breakdown)
    
def count_of_items(odb, pdb, date_list, mcfg,mirror_breakdown=None):
    LOG("Starting Count of Items")
    """
    "proper_title": "Count of Items",
    "metric_types": ["Include Cancelled Items", "Exclude Cancelled Items"],
    "data_types": ["Sum","Percentage"],
    "breakdown_types": ["None", "Top Products", "Top Categories", "Platform"]
    
    'metric_options': {'breakdown': 'Platform',
                        'data_type': 'Sum',
                        'metric': 'Revenue By Item',
                        'metric_type': 'Before Discount'
                        'number_of_rankings': 2},    
    """
    mtype = mcfg["metric_type"]
    datatype = mcfg["data_type"]
    breakdown = mcfg["breakdown"]
    n_breakdown = mcfg["number_of_rankings"]
    
    if mcfg["metric_type"] == "Include Cancelled Items":
        LOG("No masking needed, because cancelled items included.")
    elif mcfg["metric_type"] == "Exclude Cancelled Items":
        LOG("Masking DB to only include non-cancelled items.")
        odb = odb.loc[odb['cancel_status'] == "취소안함"]
    else:
        BUG("Metric Type {} is not compatible with Metric: {}".format(mtype,mcfg))
        
#    odb.to_excel("orig.xlsx")
    
    LOG("Getting top {} elements for breakdown type: {}".format(n_breakdown,breakdown))
    top_counts = []
    
    if breakdown == "Gen. Platform":
        bkdwn_column = "pc_or_mobile_platform"
        top_counts = ["모바일","PC"]  
    else:
        if breakdown == "None":
            bkdwn_column = None
            top_counts = []
        else:
            if breakdown == "Top Products":
                bkdwn_column = "product_cafe24_code"
            elif breakdown == "Top Categories":
                bkdwn_column = "category"
                odb = pd.merge(odb, pdb.drop_duplicates(subset="product_cafe24_code"), on="product_cafe24_code", right_index=False,
                               how='left', sort=False)
            elif breakdown == "Spec. Platform":
                bkdwn_column = "shopping_platform"
            
            if not mirror_breakdown is None:
                top_counts = mirror_breakdown
            else:
                top_counts = odb[bkdwn_column].value_counts().head(n_breakdown).index.values
    if top_counts == []:
        BUG("Breakdown type: {} is not compatible with Metric {}".format(breakdown,mcfg))
    LOG("Generating result_dict.")
    result_dict = {"All":[ 0 for date in date_list],"breakdown":{}}    
    for thing_name in top_counts:
        result_dict["breakdown"][thing_name] = [ 0 for date in date_list]
        
    LOG("Iterating Over Rows")
    for index,row in odb.iterrows():
        date_index =  date_list.index(row["date"])
        result_dict["All"][date_index] += 1
        if not breakdown == "None":
            result_dict_key = row[bkdwn_column]
            try: 
                result_dict["breakdown"][result_dict_key]
            except KeyError:
                pass
            else:
                result_dict["breakdown"][result_dict_key][date_index] += 1
    LOG("DONE")
        
    if datatype == "Percentage":
        for index in range(0,len(date_list)):
            total = result_dict["All"][index]
            for k in result_dict["breakdown"].keys():
                perc = 100 * float(result_dict["breakdown"][k][index])/float(total)
                result_dict["breakdown"][k][index] = perc            
                
#    PRETTYPRINT(result_dict)
    return date_list, result_dict
    
def get_filtered_dbs(di_dbs,req_db,filters,xtype):
    the_db = di_dbs[req_db].copy()
    
    if xtype == "date_series":   
        LOG("x_axis_type is date_series, applying time_mask.")
        the_db = apply_time_mask(the_db,filters["start_datetime"],filters["end_datetime"])
    else:
        LOG("Time Mask Not Required for x_axis_type: {}".format(xtype))

    c_or_p_choice = filters["category_or_product"]
    entryinput = filters["category_or_product_entry"]     
    if not c_or_p_choice == "DEFAULT_IGNORE":           
        if c_or_p_choice == "All":
            LOG("User chose no category/product filter.")
        elif c_or_p_choice == "Product Code" or c_or_p_choice == "Category":
            the_db = apply_product_mask(the_db,c_or_p_choice,entryinput)
    else:
        LOG("This metric cannot apply a category or product mask.")
        
    platform_choice = filters["platform"]   
#    print(platform_choice)
    if not platform_choice == "DEFAULT_IGNORE":           
        if platform_choice == "All":
            LOG("User chose no category/product filter.")
        elif platform_choice == "Mobile" or platform_choice == "PC":
            LOG("User chose {} platform filter.".format(platform_choice))
            the_db = apply_platform_mask(the_db,platform_choice)
    else:
        LOG("This metric cannot apply a category or product mask.")    
        
    return the_db    

def _gen_dates(start, end, init_kvs=[]):
    temp_keys = {}
    for k, v in init_kvs:
        if v == "list":
            temp_keys[k] = []
        else:
            temp_keys[k] = v
#            INCREDIBLY IMPORTANT TO NOTICE THE USE OF COPY.DEEPCOPY HERE
#            BEFORE THIS, WE WOULD GET MANY DATES REFERENCING THE SAME LIST
    temp_db = {start + timedelta(days=x): copy.deepcopy(temp_keys)
               for x in range((end - start).days + 1)}
    
    return collections.OrderedDict(sorted(temp_db.items()))

def _gen_dates_list(start,end):
    return [start + timedelta(days=x) for x in range((end - start).days + 1)]
    
def apply_time_mask(db,start,end):
    try:
        mask = (db['date'] >= start) & (
            db['date'] <= end)
    except KeyError:
        LOG("Requested DB has no date columns to mask on. Returning orig db")
        return db
    return db.loc[mask]     

def apply_product_mask(db,filtertype,value):
    if filtertype == "Product Code" or filtertype == "Category":
        db = db.loc[db['product_cafe24_code'] == value]
    elif filtertype == "Category":
        db = db.loc[db['category'] == value] 
    return db

def apply_platform_mask(db,filtertype):
    if filtertype == "PC":
        db = db.loc[db['pc_or_mobile_platform'] == "PC"]
    elif filtertype == "Mobile":
        db = db.loc[db['pc_or_mobile_platform'] == "모바일"]
    return db  