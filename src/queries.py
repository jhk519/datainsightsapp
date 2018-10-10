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


def main(rpack, di_dbs,breakdown_keys=None,ignore_numbers=None):
    raw_metrics_ref = {
        "Count Of Items": [count_of_items,"odb"],
        "Revenue By Item": [revenue_by_item,"odb"],
        "Count Of Orders": [count_of_orders,"odb"],
        "Revenue By Order": [revenue_by_order,"odb"],
        "Order Size": [order_size,"odb"],
        "Count Of Pageviews": [count_of_pageviews,"tdb"],
        "Count Of Visitors": [count_of_visitors,"tdb"],
        "Count of Cancels By Item": [count_of_cancels_by_item,"odb"]
    }    
    xtype = rpack["x_axis_type"]
    data_cfg = rpack["data_filters"]
    metric_cfg = rpack["metric_options"]
    
    raw_metric_str = metric_cfg["metric"]
    try:
        raw_metric_func = raw_metrics_ref[raw_metric_str][0]
    except KeyError:
        BUG("Metric string in metric_cfg arg not found in raw_metrics_ref: {}".format(raw_metric_str))
    req_db = raw_metrics_ref[raw_metric_str][1] 
    
    # FILTER DBS
    filtered_db = get_filtered_dbs(di_dbs,req_db,data_cfg,xtype)
    
    # GATHER RAW METRIC DATA
    if xtype == "date_series":
        raw_date_list = _gen_dates_list(data_cfg["start_datetime"], data_cfg["end_datetime"])
        date_list, result_dict = raw_metric_func(filtered_db,
                                                 raw_date_list,
                                                 metric_cfg,
                                                 breakdown_keys,
                                                 ignore_numbers=ignore_numbers)
        return  date_list, result_dict
    
def count_of_cancels_by_item(odb,date_list,mcfg,breakdown_keys,**args):
    LOG("Starting Cancels by Items")
    metric = mcfg["metric"]
    mtype = mcfg["metric_type"]
    datatype = mcfg["data_type"]
    breakdown = mcfg["breakdown"]
    n_breakdown = mcfg["number_of_rankings"]  
    
    """    
        "proper_tile": "Count of Cancels By Item (BETA)",
        "metric_types": ["Include Full Order Cancels", "Exclude Full Order Cancels"],
        "data_types": ["Sum","Percentage","% of Total Sales BETA"],
        "breakdown_types": ["None","Top Products","Top Categories","Gen. Platform","Spec.Platform"]  
    """

    odb = odb.loc[odb['cancel_status'] != "취소안함"]

    # METRIC TYPE FILTERING 
    if mtype == "Include Full Order Cancels":
        LOG("No masking needed, because fully cancelled orders included.")
    elif mtype == "Exclude Full Order Cancels":
        LOG("Masking DB to only include non-cancelled items.")
        odb = odb.loc[odb['cancel_status'] == "취소"]
    else:
        BUG("Metric Type {} is not compatible with Metric: {}".format(mtype,metric)) 
        
    top_counts,bkdwn_column_str,odb = get_top_counts_and_bkdwn_column_str(odb,
                                                                          breakdown,
                                                                          n_breakdown,
                                                                          breakdown_keys,
                                                                          topby="line_orders")       
    
    if top_counts == []:
        BUG("Breakdown type: {} is not compatible with Metric {}".format(breakdown,metric))   
    result_dict = gen_result_dict(top_counts,date_list)     
    LOG("Iterating Over Rows")           
    for row_tuple in odb.itertuples():
        date_index =  date_list.index(row_tuple.date)
        val_to_add = 1
        
        if not breakdown == "None":
            result_dict_key = getattr(row_tuple, bkdwn_column_str)
        else:
            result_dict_key = "All"
            
        result_dict = update_result_dict(result_dict,result_dict_key,date_index,val_to_add)           
                
    LOG("DONE")        
        
           
    if datatype == "Percentage":
        return convert_to_percentages(date_list,result_dict)
    
    return date_list, result_dict        

def count_of_items(odb, date_list, mcfg,breakdown_keys,**args):
    LOG("Starting Count of Items")
    metric = mcfg["metric"]
    mtype = mcfg["metric_type"]
    datatype = mcfg["data_type"]
    breakdown = mcfg["breakdown"]
    n_breakdown = mcfg["number_of_rankings"]
    
    # METRIC TYPE FILTERING 
    if mtype == "Include Cancelled Items":
        LOG("No masking needed, because cancelled items included.")
    elif mtype == "Exclude Cancelled Items":
        LOG("Masking DB to only include non-cancelled items.")
        odb = odb.loc[odb['cancel_status'] == "취소안함"]
    else:
        BUG("Metric Type {} is not compatible with Metric: {}".format(mtype,metric))     

        
    top_counts,bkdwn_column_str,odb = get_top_counts_and_bkdwn_column_str(odb,
                                                                          breakdown,
                                                                          n_breakdown,
                                                                          breakdown_keys,
                                                                          topby="line_orders")
        
    if top_counts == []:
        BUG("Breakdown type: {} is not compatible with Metric {}".format(breakdown,metric))
        
    result_dict = gen_result_dict(top_counts,date_list)

    LOG("Iterating Over Rows")           
    for row_tuple in odb.itertuples():
        date_index =  date_list.index(row_tuple.date)
        val_to_add = 1
        
        if not breakdown == "None":
            result_dict_key = getattr(row_tuple, bkdwn_column_str)
        else:
            result_dict_key = "All"
            
        result_dict = update_result_dict(result_dict,result_dict_key,date_index,val_to_add)           
                
    LOG("DONE")
        
    if datatype == "Percentage":
        return convert_to_percentages(date_list,result_dict)
    
    return date_list, result_dict

def revenue_by_item(odb, date_list, mcfg,breakdown_keys,**args):
    metric = mcfg["metric"]
    mtype = mcfg["metric_type"]
    datatype = mcfg["data_type"]
    breakdown = mcfg["breakdown"]
    n_breakdown = mcfg["number_of_rankings"]    
    
    # METRIC TYPE FILTERING
    if mtype == "Before Discount":
        beforedisc = True
    elif mtype == "After Discount":
        beforedisc = False
    else:
        BUG("Metric Type {} is not compatible with Metric: {}".format(mtype,metric))
        
    top_counts,bkdwn_column_str,odb = get_top_counts_and_bkdwn_column_str(odb,
                                                                          breakdown,
                                                                          n_breakdown,
                                                                          breakdown_keys,
                                                                          topby="revenue")   

    if top_counts == []:
        BUG("Breakdown type: {} is not compatible with Metric {}".format(breakdown,metric))
        
    result_dict = gen_result_dict(top_counts,date_list)
            
    LOG("Iterating Over Rows")           
    for row_tuple in odb.itertuples():
        date_index =  date_list.index(row_tuple.date)
        if beforedisc:
            val_to_add = row_tuple.product_price
        else:
            val_to_add = row_tuple.product_price - row_tuple.product_standard_discount

        if not breakdown == "None":
            result_dict_key = getattr(row_tuple, bkdwn_column_str)
        else:
            result_dict_key = "All"
            
        result_dict = update_result_dict(result_dict,result_dict_key,date_index,val_to_add)              
                
    LOG("DONE")
        
    if datatype == "Percentage":
        LOG("Converting to Percentages")
        return convert_to_percentages(date_list,result_dict)
    
    elif datatype == "Average":
        return convert_to_averages(date_list,result_dict)
    
    return date_list, result_dict

#def count_of_orders(odb,date_list, mcfg, breakdown_keys,**args): 
def count_of_orders(odb,date_list, mcfg,breakdown_keys, **args): 
   
    metric = mcfg["metric"]
    mtype = mcfg["metric_type"]
    datatype = mcfg["data_type"]
    breakdown = mcfg["breakdown"]
    n_breakdown = mcfg["number_of_rankings"]   
    
    ignore_numbers = args["ignore_numbers"]
    if ignore_numbers is None:
        ignore_numbers = []
#    ignore_numbers = []
        
    odb = odb.drop_duplicates(subset="order_id")
    
    # METRIC TYPE FILTERING 
    if mtype == "Include Fully Cancelled Orders":
        LOG("No masking needed, because cancelled items included.")
    elif mtype == "Exclude Fully Cancelled Orders":
        LOG("Masking DB to only include non-cancelled items.")
        odb = odb.loc[odb['cancel_status'] != "취소"]
    else:
        BUG("Metric Type {} is not compatible with Metric: {}".format(mtype,metric))      
    
    top_counts,bkdwn_column_str,odb = get_top_counts_and_bkdwn_column_str(odb,
                                                                          breakdown,
                                                                          n_breakdown,
                                                                          breakdown_keys,
                                                                          topby="line_orders")         

    if top_counts == []:
        BUG("Breakdown type: {} is not compatible with Metric {}".format(breakdown,metric))
        
    result_dict = gen_result_dict(top_counts,date_list)
        
    LOG("Iterating Over Rows") 
    
    for row_tuple in odb.itertuples():
        date_index =  date_list.index(row_tuple.date)
        val_to_add = 1
        
        if breakdown == "None":
            result_dict_key = "All"        
        else:                
            if breakdown == "Customer's Nth Order":
                try: 
                    nth_order = int(getattr(row_tuple, "order_count") )
                except ValueError: 
                    continue  
                phone_number = str(getattr(row_tuple, "customer_phone_number"))
                
                if phone_number in ignore_numbers:
                    result_dict_key = "IGNORE_NUMBER"  
                elif nth_order >= n_breakdown:
                    result_dict_key = str(top_counts[n_breakdown-1])
                else:
                    result_dict_key= str(nth_order) 
            else:
                result_dict_key = getattr(row_tuple, bkdwn_column_str)
                
        result_dict = update_result_dict(result_dict,result_dict_key,date_index,val_to_add)       
        
    LOG("DONE")
        
    if datatype == "Percentage":
        return convert_to_percentages(date_list,result_dict)
    
    return date_list, result_dict

def revenue_by_order(odb, date_list, mcfg,breakdown_keys,**args):    
    metric = mcfg["metric"]
    mtype = mcfg["metric_type"]
    datatype = mcfg["data_type"]
    breakdown = mcfg["breakdown"]
    n_breakdown = mcfg["number_of_rankings"] 
    
    odb = odb.drop_duplicates(subset="order_id") 
    
    # METRIC TYPE FILTERING 
    if mtype == "Orig. Price, Incl. Cncld Orders":
        LOG("No masking needed, because cancelled orders included.")
        beforedisc = True
    elif mtype == "Net. Price, Incl. Cncld Orders":
        LOG("No masking needed, because cancelled orders included. Revenue after discount.")
        beforedisc = False
    elif mtype == "Orig. Price, Excl. Cncld Orders":   
        LOG("Masking DB to only include non-cancelled orders.")
        beforedisc = True
        odb = odb.loc[odb['cancel_status'] != "취소"]        
    elif mtype ==  "Net. Price, Excl. Cncld Orders":
        LOG("Masking DB to only include non-cancelled orders. Revenue after discount.")
        beforedisc = False
        odb = odb.loc[odb['cancel_status'] != "취소"]
    else:
        BUG("Metric Type {} is not compatible with Metric: {}".format(mtype,metric))     
        
    top_counts,bkdwn_column_str,odb = get_top_counts_and_bkdwn_column_str(odb,
                                                                          breakdown,
                                                                          n_breakdown,
                                                                          breakdown_keys,
                                                                          topby="line_orders") 
    if top_counts == []:
        BUG("Breakdown type: {} is not compatible with Metric {}".format(breakdown,metric))
        
    result_dict = gen_result_dict(top_counts,date_list)
        
    LOG("Iterating Over Rows")           
    for row_tuple in odb.itertuples():
        date_index =  date_list.index(row_tuple.date)
        
        if beforedisc: val_to_add = row_tuple.total_original_price
        else: val_to_add = row_tuple.total_net_price   
        
        if not breakdown == "None":
            result_dict_key = getattr(row_tuple, bkdwn_column_str)
        else:
            result_dict_key = "All"            
        
        result_dict = update_result_dict(result_dict,result_dict_key,date_index,val_to_add)
            
    if datatype == "Percentage":
        return convert_to_percentages(date_list,result_dict)
    elif datatype == "Average":
        return convert_to_averages(date_list,result_dict)
    
    return date_list, result_dict            
            
def order_size(odb,date_list, mcfg,breakdown_keys,**args):    
    metric = mcfg["metric"]
    mtype = mcfg["metric_type"]
    datatype = mcfg["data_type"]
    breakdown = mcfg["breakdown"]
    n_breakdown = mcfg["number_of_rankings"] 
    
    # METRIC TYPE FILTERING 
    if mtype == "Include Cancelled Items":
        LOG("No masking needed, because cancelled items included.")
    elif mtype == "Exclude Cancelled Items":
        LOG("Masking DB to only include non-cancelled items.")
        odb = odb.loc[odb['cancel_status'] == "취소안함"]
    else:
        BUG("Metric Type {} is not compatible with Metric: {}".format(mtype,metric)) 
        
    order_sizes_by_order_id = odb["order_id"].value_counts()       
    odb = odb.drop_duplicates(subset="order_id")
        
    top_counts,bkdwn_column_str,odb = get_top_counts_and_bkdwn_column_str(odb,
                                                                          breakdown,
                                                                          n_breakdown,
                                                                          breakdown_keys,
                                                                          topby="line_orders")      
    
    if top_counts == []:
        BUG("Breakdown type: {} is not compatible with Metric {}".format(breakdown,metric))
        
    result_dict = gen_result_dict(top_counts,date_list)    
        
    LOG("Iterating Over Rows")           
    for row_tuple in odb.itertuples():
        date_index =  date_list.index(row_tuple.date)
        val_to_add = order_sizes_by_order_id.get(getattr(row_tuple, "order_id"))
            
        if not breakdown == "None":
            result_dict_key = getattr(row_tuple, bkdwn_column_str)
        else:
            result_dict_key = "All"            
        
        result_dict = update_result_dict(result_dict,result_dict_key,date_index,val_to_add)
            
    if datatype == "Percentage":
        return convert_to_percentages(date_list,result_dict)
    elif datatype == "Average":
        return convert_to_averages(date_list,result_dict)
    
    return date_list, result_dict  

def count_of_pageviews(tdb, date_list, mcfg, breakdown_keys,**args):
    metric = mcfg["metric"]
    mtype = mcfg["metric_type"]
    datatype = mcfg["data_type"]
    breakdown = mcfg["breakdown"]
    n_breakdown = mcfg["number_of_rankings"] 
    
    top_counts = ["All"]
    result_dict = gen_result_dict(top_counts,date_list)
    
    LOG("Iterating Over Rows")           
    for row_tuple in tdb.itertuples():
        date_index =  date_list.index(row_tuple.date)
        val_to_add = getattr(row_tuple, "total_pageviews")
        result_dict_key = "All"            
        
        result_dict = update_result_dict(result_dict,result_dict_key,date_index,val_to_add)
            
    if datatype == "Percentage":
        return convert_to_percentages(date_list,result_dict)
    elif datatype == "Average":
        return convert_to_averages(date_list,result_dict)        
    return date_list, result_dict 

def count_of_visitors(tdb, date_list, mcfg, breakdown_keys,**args):
    metric = mcfg["metric"]
    mtype = mcfg["metric_type"]
    datatype = mcfg["data_type"]
    breakdown = mcfg["breakdown"]
    n_breakdown = mcfg["number_of_rankings"] 
    
    top_counts,bkdwn_column_str,tdb = get_top_counts_and_bkdwn_column_str(tdb,
                                                                          breakdown,
                                                                          n_breakdown,
                                                                          breakdown_keys,
                                                                          topby="visitors")     
    result_dict = gen_result_dict(top_counts,date_list)
    
    LOG("Iterating Over Rows")           
    for row_tuple in tdb.itertuples():
        date_index =  date_list.index(row_tuple.date)
        if breakdown == "None":
            result_dict_key = "All"    
            val_to_add = getattr(row_tuple, "new_visitors_count") + getattr(row_tuple, "returning_visitors_count")
            result_dict = update_result_dict(result_dict,result_dict_key,date_index,val_to_add)
            
        elif breakdown == "Device":
            for top_str in top_counts:
                result_dict_key = top_str
                if result_dict_key == "PC":
                    val_to_add = getattr(row_tuple, "pc_visitors_count")
                elif result_dict_key == "Mobile":
                    val_to_add = getattr(row_tuple, "mobile_visitors_count")
                elif result_dict_key == "App":
                    val_to_add = getattr(row_tuple, "app_visitors_count")
                result_dict = update_result_dict(result_dict,result_dict_key,date_index,val_to_add)
                    
        elif breakdown == "New/Returning":
            for top_str in top_counts:
                result_dict_key = top_str
                if result_dict_key == "New":
                    val_to_add = getattr(row_tuple, "new_visitors_count")
                elif result_dict_key == "Returning":
                    val_to_add = getattr(row_tuple, "returning_visitors_count") 
                result_dict = update_result_dict(result_dict,result_dict_key,date_index,val_to_add)

    if datatype == "Percentage":
        return convert_to_percentages(date_list,result_dict)
    elif datatype == "Average":
        return convert_to_averages(date_list,result_dict)        
    return date_list, result_dict 

def gen_result_dict(result_dict_keys,date_list):
#    LOG("Generating result_dict with result_dict_keys: {}".format(result_dict_keys))
    result_dict = {
            "total": {"count": [ 0 for date in date_list],
                      "data": [ 0 for date in date_list]},
            "lines":{}
    }    
            
    for result_dict_key in result_dict_keys:
        result_dict["lines"][result_dict_key] = {
            "count": [ 0 for date in date_list],
            "data": [ 0 for date in date_list]
        }
        
    return result_dict

def update_result_dict(result_dict,result_dict_key, date_index,val_to_add):
    result_dict["total"]["count"][date_index] += 1
    result_dict["total"]["data"][date_index] += val_to_add

    try: 
        result_dict["lines"][result_dict_key]
    except KeyError:
        pass
    else:
        result_dict["lines"][result_dict_key]["count"][date_index] += 1  
        result_dict["lines"][result_dict_key]["data"][date_index] += val_to_add 
        
    return result_dict

def get_top_counts_and_bkdwn_column_str(db_prime,breakdown,n_breakdown,force_top_count,topby):
    top_counts = []
    bkdwn_column = None
 
    # DETERMINE BREAKDOWN COLUMN STRING IF NEEDED
    if breakdown == "Gen. Platform":
        bkdwn_column = "pc_or_mobile_platform"      
    elif breakdown == "Top Products":
        bkdwn_column = "product_cafe24_code"
    elif breakdown == "Top Categories":
        bkdwn_column = "category"
    elif breakdown == "Spec. Platform":
        bkdwn_column = "shopping_platform"
    
    # GENERATE TOP BREAKDOWN KEYS 
    if not bkdwn_column is None:
        if topby == "line_orders":
            top_counts = db_prime[bkdwn_column].value_counts().head(n_breakdown).index.values  
        elif topby == "revenue":
            groups = db_prime.groupby([bkdwn_column])['product_price'].agg('sum')
            top_counts = list(groups.nlargest(n_breakdown).index.values)        
        
    elif bkdwn_column is None:
        # SPECIAL FORCED OR MANUAL TOP_COUNTS
#        if not force_top_count is None:
#            top_counts = force_top_count
        if breakdown == "None":
            top_counts = ["All"]    
        elif breakdown == "Device":
            top_counts = ["PC","Mobile","App"]
        elif breakdown == "New/Returning":
            top_counts = ["New","Returning"] 
        elif breakdown == "Customer's Nth Order":
            top_counts = [str(num) for num in range(1,n_breakdown+1)]
            top_counts[-1] += "+"
            top_counts.append("IGNORE_NUMBER")
            
    if not force_top_count is None:
        top_counts = force_top_count            
        
    return top_counts,bkdwn_column,db_prime

def convert_to_averages(date_list,result_dict):
    for index in range(0,len(date_list)):
        for k in result_dict["lines"].keys():
            count_on_day = result_dict["lines"][k]["count"][index]
            if count_on_day > 0:
                total_on_day = result_dict["lines"][k]["data"][index]
                avg = total_on_day/count_on_day
                result_dict["lines"][k]["data"][index] = avg  
    return date_list, result_dict    

def convert_to_percentages(date_list,result_dict):
    for index in range(0,len(date_list)):
        total = result_dict["total"]["data"][index]
        if total > 0:
            for k in result_dict["lines"].keys():
                perc = 100 * float(result_dict["lines"][k]["data"][index])/float(total)
                result_dict["lines"][k]["data"][index] = perc  
    return date_list, result_dict
    
def get_filtered_dbs(di_dbs,req_db,filters,xtype):
#    PRETTYPRINT(filters)
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
            LOG("User chose {} produdt/category filter.".format(entryinput))
            the_db = apply_product_mask(the_db,c_or_p_choice,entryinput)
    else:
        LOG("This metric cannot apply a category or product mask.")
        
    platform_choice = filters["platform"]   
    if not platform_choice == "DEFAULT_IGNORE":           
        if platform_choice == "All":
            LOG("User chose no platform filter.")
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
    # INCREDIBLY IMPORTANT TO NOTICE THE USE OF COPY.DEEPCOPY HERE
    # BEFORE THIS, WE WOULD GET MANY DATES REFERENCING THE SAME LIST
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
    if filtertype == "Product Code":
        if "," in value:
            values_iter = value.split(",")
#            print(values_iter)
            db = db.loc[db['product_cafe24_code'].isin(values_iter)]
#            df.loc[df['column_name'].isin(some_values)]
        else:
            db = db.loc[db['product_cafe24_code'] == value]
    elif filtertype == "Category":
#        print(filtertype)
        if "," in value:
            values_iter = value.split(",")
#            print(va)
#            print(values_iter)
            db = db.loc[db['category'].isin(values_iter)]        
        else:
#            print(value)
            db = db.loc[db['category'] == value] 
    return db

def apply_platform_mask(db,filtertype):
    if filtertype == "PC":
        db = db.loc[db['pc_or_mobile_platform'] == "PC"]
    elif filtertype == "Mobile":
        db = db.loc[db['pc_or_mobile_platform'] == "모바일"]
    return db  