# Standard Modules 
from pprint import pprint
import collections
import copy
from datetime import datetime, timedelta
import logging

# Non-Standard Modules
import workdays
import pandas as pd

log = logging.getLogger(__name__).info
log("{} Init.".format(__name__))    
bug = logging.getLogger(__name__).debug       

dates =  [
        "2018-01-01",
        "2018-02-15",
        "2018-02-16",
        "2018-02-17",
        "2018-03-01",
        "2018-05-05",
        "2018-05-07",
        "2018-05-22",
        "2018-06-06",
        "2018-06-13",
        "2018-08-15",
        "2018-09-23",
        "2018-09-24",
        "2018-09-25",
        "2018-09-26",
        "2018-10-03",
        "2018-10-09",
        "2018-12-25"
    ]

def main(st_query_name, di_dbs, start, end, extra=None, n_rankings=10):
    queries_ref = {
        "Total Orders By Item":[order_quantity,["odb",]],
        "Total Returns By Item":[return_quantity,["odb",]],
        "Total Cancels By Item":[cancel_quantity,["odb",]],
        "Cancel Reasons":[cancel_reasons,["odb",]],
        "Net Payments Received":[net_payment,["odb",]],
        "Net Discount Given":[net_discount,["odb",]],
        "Average Order Value":[aov,["odb",]],
        "Average Order Size":[aos,["odb",]],
        "Sent Orders Days To Ship":[days_to_ship,["odb",]],
        "Unsent Orders Days To Ship":[days_unsent,["odb",]],  
        "Top Products (Orders)":[topten_by_orders,["odb",]],
        "Top Products (Revenue)":[topten_by_returns,["odb",]],  
        "Daily Sales (Top Products)":[daily_sales_top_products,["odb",]],
        "Revenue By Mobile":[revenue_mobile,["tdb",]],
        "Revenue By All Devices":[revenue_all,["tdb",]],
        "Revenue By PC":[revenue_pc,["tdb",]],
        "Revenue By Kooding":[revenue_kooding,["tdb",]],
        "Revenue By App":[revenue_app,["tdb",]],
        "Total Pageviews":[pageviews,["tdb",]],
        "Visitors By Mobile":[visitors_mobile,["tdb",]],
        "Visitors By PC":[visitors_pc,["tdb",]],
        "Visitors By App":[visitors_app,["tdb",]],
        "Visitors By All Devices":[visitors_all,["tdb",]],
        "Orders By App":[orders_app,["tdb",]],
        "Orders By PC":[orders_pc,["tdb",]],
        "Orders By Mobile":[orders_mobile,["tdb",]],
        "Orders By All Devices":[orders_all,["tdb",]],   
        "Conversion Rate":[conversion_rate,["tdb",]],
        "Top Categories (Orders)":[top10_categories_orders,["odb","pdb"]],
        "Top Categories (Revenue)":[top10_categories_revenue,["odb","pdb"]],
    }
    log("Requesting query {} at start {} and end {}".format(st_query_name,start,end))
#    db = copy.deepcopy(di_dbs[queries_ref[st_query_name][1]])
    dbs_needed = queries_ref[st_query_name][1]
    db = None
    if len(dbs_needed) == 1:
        log("Queries using one db")
        db = di_dbs[dbs_needed[0]].copy()
        dbs = apply_mask(db,start,end)
        if dbs.shape[0] <= 1:
            return "No Date Data"
    elif len(dbs_needed) > 1:
        log("Queries using more than one db.")
        dbs = []
        for ind,db_str in enumerate(dbs_needed):
            db = di_dbs[db_str].copy()
            db = apply_mask(db,start,end)
            if db.shape[0] <= 1:
                bug("DB too small.")
                return "No Date Data"
            dbs.append(db)
    func = queries_ref[st_query_name][0]
    returnval = func(dbs, start, end, extra=extra,n_rankings=n_rankings)
    if returnval:
        return list(returnval)
    else:
        return None
    
def daily_sales_top_products(db, start, end, extra=None,n_rankings=3):
    count_db = db["product_cafe24_code"].value_counts().head(n_rankings)
    list_of_product_daily_sales = []
    for pcode,value in count_db.iteritems():
#        print(pcode,value)
        product_daily_sales = []
        temp_db = db.loc[db['product_cafe24_code'] == pcode] 
        date_dict = _gen_dates(start, end, init_kvs=[("net_payment", 0)])
        date_dict = collections.OrderedDict(sorted(date_dict.items()))
        
        for index, row in temp_db.iterrows():
            temp_date = row["date_payment"]
            if temp_date in date_dict:
                date_dict[temp_date]["net_payment"] += row["product_price"]   
        for date_obj in date_dict:
            product_daily_sales.append(date_dict[date_obj]["net_payment"])
        list_of_product_daily_sales.append((product_daily_sales,pcode))
                
    x_axis_labels = []
    
    for date_obj in date_dict:
        x_axis_labels.append(date_obj)
    return "MULTIPLE PLOTS", x_axis_labels, list_of_product_daily_sales   
    
def top10_categories_orders(dbs,start,end,extra=None,n_rankings=10):
    odb = dbs[0]
    pdb = dbs[1]
    new_df = pd.merge(odb, pdb, on="product_cafe24_code", how='left',indicator=False)
    count_db = new_df["category"].value_counts().head(n_rankings)
    x_axis_labels = []
    y_axis_values = []
    for cat,value in count_db.iteritems():
        x_axis_labels.append(cat)
        y_axis_values.append(value)
    return x_axis_labels, y_axis_values    

def top10_categories_revenue(dbs,start,end,extra=None,n_rankings=10):
    odb = dbs[0]
#    print(odb.head(15))
    pdb = dbs[1]
#    print(pdb.head(10))
#    odb["category"] = odb.product_cafe24_code.map(pdb.product_cafe24_code)
#    print(odb.category)
#    count_db = odb["category"].value_counts().head(10)
#    print("----")
#    print(count_db.head(10))
#    odb.merge(pdb, on='product_cafe24_code', how='left')
    new_df = pd.merge(odb, pdb, on="product_cafe24_code", how='left',indicator=False)   
    groups = new_df.groupby(['category'])['total_net_price'].agg('sum')
    topten = groups.nlargest(n_rankings)
    
    x_axis_labels = []
    y_axis_values = []
    for index,value in topten.iteritems():
        x_axis_labels.append(index)
        y_axis_values.append(value)
    return x_axis_labels, y_axis_values    
    
    

def cancel_quantity(db, start, end, extra=None,n_rankings=10):
    if extra is not None and not extra == "":
        db = db.loc[db['product_cafe24_code'] == extra]
        
    date_dict = _gen_dates(start, end, init_kvs=[("cancels", 0)])
    
    for index, row in db.iterrows():
        temp_date = row["date_payment"]
        temp_cancel = row["cancel_status"]
        if temp_date in date_dict:
            if temp_cancel == "부분취소" or temp_cancel == "취소":
                date_dict[temp_date]["cancels"] += 1

    date_list = []
    cancels_list = []

    for date_object in collections.OrderedDict(sorted(date_dict.items())):
        date_list.append(date_object)
        cancels_list.append(date_dict[date_object]["cancels"])
    return date_list, cancels_list


def return_quantity(db, start, end, extra=None,n_rankings=10):
    if extra is not None and not extra == "":
        db = db.loc[db['product_cafe24_code'] == extra]

    date_dict = _gen_dates(start, end, init_kvs=[("returns", 0)])
    for index, row in db.iterrows():
        temp_date = row["date_payment"]
        temp_return = row["date_returned"]
        if temp_date in date_dict:
            if not temp_return == 0:
                date_dict[temp_date]["returns"] += 1

    date_list, returns_list = [], []

    for date_object in collections.OrderedDict(sorted(date_dict.items())):
        date_list.append(date_object)
        returns_list.append(date_dict[date_object]["returns"])
    return date_list, returns_list


def order_quantity(db, start, end, extra=None,n_rankings=10):
    if extra is not None and not extra == "":
        db = db.loc[db['product_cafe24_code'] == extra]

    date_dict = _gen_dates(start, end, init_kvs=[("orders", 0)])
    for index, row in db.iterrows():
        temp_date = row["date_payment"]
        if temp_date in date_dict:
            date_dict[temp_date]["orders"] += 1
    date_list, orders_list = [], []
    for date_object in collections.OrderedDict(sorted(date_dict.items())):
        date_list.append(date_object)
        orders_list.append(date_dict[date_object]["orders"])
    return date_list, orders_list


def cancel_reasons(db, start, end, extra=None,n_rankings=10):

#    EXTRACT AND FILTER DB IF NECC.
    if extra is not None and not extra == "":
        db = db.loc[db['product_cafe24_code'] == extra]

    try:
        db = db["reason_cancelled"].value_counts()
    except KeyError:
        bug("Missing 'reason_cancelled in DB")
        return None
    list_of_unique_reasons = []
    counts_of_reasons = []
    total_non_sold_out = 0
    for x in db.iteritems():
        bug("cancel_reasons x[0] = {}, x[1] = {} END".format(x[0],x[1]))
        if x[0] == '품절':
            list_of_unique_reasons.append("Sold Out")
            counts_of_reasons.append(x[1])
        else:
            total_non_sold_out += x[1]
    list_of_unique_reasons.append("Customer Request")
    counts_of_reasons.append(total_non_sold_out)
    return list_of_unique_reasons, counts_of_reasons


def revenue_all(db, start, end, extra=None,n_rankings=10):
    date_list = []
    revenues_list = []
    for index, row in db.iterrows():
        date_list.append(row["date"])
        total = row["app_revenue"] + row["mobile_revenue"] + row["pc_revenue"] + row["kooding_revenue"]
        revenues_list.append(total)

    return date_list, revenues_list

def revenue_kooding(db, start, end, extra=None,n_rankings=10):
    date_list = []
    revenues_list = []
    for index, row in db.iterrows():
        date_list.append(row["date"])
        total = row["kooding_revenue"]
        revenues_list.append(total)

    return date_list, revenues_list


def revenue_pc(db, start, end, extra=None,n_rankings=10):
    date_list = []
    revenues_list = []
    for index, row in db.iterrows():
        date_list.append(row["date"])
        total = row["pc_revenue"]
        revenues_list.append(total)

    return date_list, revenues_list


def revenue_mobile(db, start, end, extra=None,n_rankings=10):
    date_list = []
    revenues_list = []
    for index, row in db.iterrows():
        date_list.append(row["date"])
        total = row["mobile_revenue"]
        revenues_list.append(total)

    return date_list, revenues_list


def revenue_app(db, start, end, extra=None,n_rankings=10):
    date_list = []
    revenues_list = []
    for index, row in db.iterrows():
        date_list.append(row["date"])
        total = row["app_revenue"]
        revenues_list.append(total)

    return date_list, revenues_list


def pageviews(db, start, end, extra=None,n_rankings=10):
    date_list = []
    pageviews_list = []
    for index, row in db.iterrows():
        date_list.append(row["date"])
        pageviews_list.append(row["total_pageviews"])
    return date_list, pageviews_list


def visitors_all(db, start, end, extra=None,n_rankings=10):
    date_list = []
    visitors_list = []
    types_of_visitors_list = [
        "app_visitors_count",
        "mobile_visitors_count",
        "pc_visitors_count"
    ]
    for index, row in db.iterrows():
        date_list.append(row["date"])
        total_visitors = 0
        for visitor_type in types_of_visitors_list:
            total_visitors += row[visitor_type]
        visitors_list.append(total_visitors)
    return date_list, visitors_list


def visitors_app(db, start, end, extra=None,n_rankings=10):
    date_list = []
    visitors_list = []
    for index, row in db.iterrows():
        date_list.append(row["date"])
        visitors_list.append(row["app_visitors_count"])
    return date_list, visitors_list


def visitors_mobile(db, start, end, extra=None,n_rankings=10):
    date_list = []
    visitors_list = []

    for index, row in db.iterrows():
        date_list.append(row["date"])
        visitors_list.append(row["mobile_visitors_count"])

    return date_list, visitors_list

def orders_mobile(db, start, end, extra=None,n_rankings=10):
    date_list = []
    ls_y_data = []

    for index, row in db.iterrows():
        date_list.append(row["date"])
        ls_y_data.append(row["mobile_orders_count"])

    return date_list, ls_y_data

def orders_app(db, start, end, extra=None,n_rankings=10):
    date_list = []
    ls_y_data = []

    for index, row in db.iterrows():
        date_list.append(row["date"])
        ls_y_data.append(row["app_orders_count"])

    return date_list, ls_y_data

def orders_pc(db, start, end, extra=None,n_rankings=10):
    date_list = []
    ls_y_data = []

    for index, row in db.iterrows():
        date_list.append(row["date"])
        ls_y_data.append(row["pc_orders_count"])

    return date_list, ls_y_data

def orders_all(db, start, end, extra=None,n_rankings=10):
    date_list = []
    total_data_list = []
    types_of_data_list = [
        "app_orders_count",
        "mobile_orders_count",
        "pc_orders_count"
    ]
    for index, row in db.iterrows():
        date_list.append(row["date"])
        total_sum = 0
        for data_type in types_of_data_list:
            total_sum += row[data_type]
        total_data_list.append(total_sum)
    return date_list, total_data_list


def visitors_pc(db, start, end, extra=None,n_rankings=10):
    date_list = []
    visitors_list = []

    for index, row in db.iterrows():
        date_list.append(row["date"])
        visitors_list.append(row["pc_visitors_count"])

    return date_list, visitors_list


def net_payment(db, start, end, extra=None,n_rankings=10):
    if extra is not None and not extra == "":
        db = db.loc[db['product_cafe24_code'] == extra]

# MUST DROP DUPLICATES BECAUSE DISCOUNT DATA IS BY ORDER BUT REPEATS PER
# ITEM
    db = db.drop_duplicates(subset="order_id")

    date_dict = _gen_dates(start, end, init_kvs=[("net_payment", 0)])
    date_dict = collections.OrderedDict(sorted(date_dict.items()))

    for index, row in db.iterrows():
        temp_date = row["date_payment"]
        if temp_date in date_dict:
            date_dict[temp_date]["net_payment"] += row["total_net_price"]

    x_axis_labels = []
    y_axis_values_1 = []

    for day in date_dict:
        x_axis_labels.append(day)
        y_axis_values_1.append(date_dict[day]["net_payment"])
    return x_axis_labels, y_axis_values_1


def net_discount(db, start, end, extra=None,n_rankings=10):
    if extra is not None and not extra == "":
        db = db.loc[db['product_cafe24_code'] == extra]
    
# MUST DROP DUPLICATES BECAUSE DISCOUNT DATA IS BY ORDER BUT REPEATS PER
# ITEM
    db = db.drop_duplicates(subset="order_id")

    date_dict = _gen_dates(start, end, init_kvs=[("net_discount", 0)])
    date_dict = collections.OrderedDict(sorted(date_dict.items()))

    for index, row in db.iterrows():
        temp_date = row["date_payment"]
        total_discount_value = 0
        list_of_discount_keys = [
            "total_membership_level_discount",
            "total_membership_points_discount",
            "total_coupon_discount",
            "total_cash_credit_discount"
        ]
        if temp_date in date_dict:
            for discount_key in list_of_discount_keys:
                total_discount_value += row[discount_key]
            date_dict[temp_date]["net_discount"] += total_discount_value

    x_axis_labels = []
    y_axis_values_1 = []

    for day in date_dict:
        x_axis_labels.append(day)
        y_axis_values_1.append(date_dict[day]["net_discount"])
    return x_axis_labels, y_axis_values_1


def aov(db, start, end, extra=None,n_rankings=10):
#   make a separate db without duplicate order_ids.
    db = db.drop_duplicates(subset="order_id")

    date_dict = _gen_dates(start, end, init_kvs=[("payments", "list")])
    date_dict = collections.OrderedDict(sorted(date_dict.items()))

    for index, row in db.iterrows():
        temp_date = row["date_payment"]
        if temp_date in date_dict:
            date_dict[temp_date]["payments"].append(row["total_net_price"])
    x_axis_labels = []
    y_axis_values_1 = []

    for diff_day in date_dict:
        x_axis_labels.append(diff_day)
        dd = date_dict[diff_day]
        try:
            pay_avg = sum(dd["payments"]) / float(len(dd["payments"]))
        except ZeroDivisionError:
            pay_avg = 0
        y_axis_values_1.append(pay_avg)
    return x_axis_labels, y_axis_values_1


def aos(db, start, end, extra=None,n_rankings=10):
# this gives us a reference of how many rows had this order_id giving us
# size of each order.
    count_db = db["order_id"].value_counts()
#   make a separate db without duplicate order_ids.
    single_order_db = db.drop_duplicates(subset="order_id")

    date_dict = _gen_dates(start, end, init_kvs=[("sizes", "list")])
    date_dict = collections.OrderedDict(sorted(date_dict.items()))

#    for each row, check if in date range, then append its size from count_db to
#    list of sizes for that date.
    for index, row in single_order_db.iterrows():
        temp_date = row["date_payment"]
        if temp_date in date_dict:
            ids = row["order_id"]
            size_of_order = count_db.get(ids)
            date_dict[temp_date]["sizes"].append(size_of_order)
    x_axis_labels = []
    y_axis_values_1 = []

    for diff_day in date_dict:
        x_axis_labels.append(diff_day)
        dd = date_dict[diff_day]
        try:
            size_avg = sum(dd["sizes"]) / float(len(dd["sizes"]))
        except ZeroDivisionError:
            size_avg = 0
        y_axis_values_1.append(size_avg)
    return x_axis_labels, y_axis_values_1


def days_to_ship(db, start, end, extra=None,n_rankings=10):
    if extra is not None and not extra == "":
        db = db.loc[db['product_cafe24_code'] == extra]

    holiday_datetimes = [datetime.strptime(
        holiday, "%Y-%m-%d").date() for holiday in dates]
    diff_days = []

    for index, col in db.iterrows():
        temp_date = col["date_payment"]
        temp_shipped = col["date_shipping"]
        temp_cancelled = col["date_cancelled"]
        if not temp_shipped == 0 and temp_cancelled == 0:
            diff = workdays.networkdays(temp_date, temp_shipped, holidays=holiday_datetimes)
            diff_days.append(diff)

    counter_dict_of_diffs = collections.Counter(diff_days)
    x_axis_labels = []
    y_axis_values = []
    for diff_day in counter_dict_of_diffs:
        x_axis_labels.append(diff_day)
        y_axis_values.append(counter_dict_of_diffs[diff_day])      
    return x_axis_labels, y_axis_values


def days_unsent(db, start, end, extra=None,n_rankings=10):

    if extra is not None and not extra == "":
        db = db.loc[db['product_cafe24_code'] == extra]      

    holiday_datetimes = [datetime.strptime(
        holiday, "%Y-%m-%d").date() for holiday in dates]
    diff_days = []

    temp_reference = datetime.today().date()

    for index, col in db.iterrows():
        temp_date = col["date_payment"]
        temp_shipped = col["date_shipping"]
        temp_cancelled = col["date_cancelled"]
       
#        THIS SHOULD CONSIDER CANCEL DATE AS WELL IN REFERENCE
        if temp_shipped == 0 and temp_cancelled == 0:       
            diff = workdays.networkdays(
                temp_date, temp_reference, holidays=holiday_datetimes)
            diff_days.append(diff)

    counter_dict_of_diffs = collections.Counter(diff_days)
    x_axis_labels = []
    y_axis_values = []
    for diff_day in counter_dict_of_diffs:
        x_axis_labels.append(diff_day)
        y_axis_values.append(counter_dict_of_diffs[diff_day])
    return x_axis_labels, y_axis_values

def conversion_rate(db,start,end,extra=None,n_rankings=10):
    date_dict = _gen_dates(start, end, init_kvs=[("cr",0)])
    date_dict = collections.OrderedDict(sorted(date_dict.items()))
    for index, row in db.iterrows():
        temp_date = row["date"]
        if temp_date in date_dict:
            visitors = row["returning_visitors_count"] + row["new_visitors_count"]
            orders = row["app_orders_count"]+row["mobile_orders_count"]+row["pc_orders_count"]
            cr = orders/visitors * 100
#            print()
            date_dict[temp_date]["cr"] = cr
    x_axis_labels = []
    y_axis_values_1 = []

    for date in date_dict:
        x_axis_labels.append(date)
        dd = date_dict[date]
        y_axis_values_1.append(dd["cr"])
    return x_axis_labels, y_axis_values_1    

def topten_by_orders(db, start, end, extra=None,n_rankings=10):
    count_db = db["product_cafe24_code"].value_counts().head(n_rankings)
    x_axis_labels = []
    y_axis_values = []
    for index,value in count_db.iteritems():
        x_axis_labels.append(index)
        y_axis_values.append(value)
    return x_axis_labels, y_axis_values

def topten_by_returns(db, start, end, extra=None,n_rankings=10):
    temp = {}
    for index,row in db.iterrows():
        
        if row["date_returned"] == 0:
            continue
        else:
            if row["product_cafe24_code"] in temp:
                x = temp[row["product_cafe24_code"]]
                x[0]  += 1
            else:
                temp[row["product_cafe24_code"]] = [1]
    
    temp_df = pd.DataFrame.from_dict(temp,orient="index")
    temp_df = temp_df.sort_values(0,ascending=False)
    temp_df = temp_df.head(n_rankings)
    
    x_axis_labels = []
    y_axis_values = []
    for index,row in temp_df.iterrows():
        x_axis_labels.append(index)
        y_axis_values.append(row[0])
    return x_axis_labels, y_axis_values
    
def apply_mask(source,start,end):
    db = source.copy(deep=True)
    try:
        mask = (db['date'] >= start) & (
            db['date'] <= end)
    except KeyError:
        log("Requested DB has no date columns to mask on. Returning orig db")
        return source
    return db.loc[mask]    

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
    return temp_db
