# -*- coding: utf-8 -*-
"""
Created on Wed May  2 22:27:37 2018

@author: Justin H Kim
"""
# Standard Modules
import os
from pprint import pprint

# Non-Standard Modules
import pandas as pd
import datetime
from openpyxl import load_workbook

def add_data(curr_df,dir_loc,ext,hr_dict,req_excels_tpl,match_on_key):
    append_df= gen_single_db_from_excels(dir_loc,ext,hr_dict,req_excels_tpl,
        match_on_key)
    new_df = pd.concat([curr_df, append_df], axis=0, ignore_index = True,
                       join = "outer")  
    return sanitize_df(new_df)
    
def gen_single_db_from_excels(dir_loc,ext,hr_dict,req_excels_tpl,
        match_on_key):       
    core_req_exc = req_excels_tpl[0]
    append_excs_list = req_excels_tpl[1]
    
    loc = dir_loc + "/" + core_req_exc+ ext
    print("Starting with Core: ", core_req_exc, "at ", loc)
    if os.path.isfile(loc):    
        temp_df = gen_core_db(loc, hr_dict[core_req_exc])
    else: 
        print("NO EXCEL EXISTS AT ", loc)
        return
    for adb in append_excs_list:
        print("Appending Secondary Data: ",adb)
        loc = dir_loc + "/" + adb + ext
        if os.path.isfile(loc):  
            temp_df = append_columns(
                temp_df,
                loc,
                hr_dict[adb],
                match_on_key)
        else:
            print("NO APPEND")
    return sanitize_df(temp_df)

def gen_core_db(excel_loc, required_headers_dict):
    init_df = pd.read_excel(excel_loc, 0)
    init_df.rename(
        columns=lambda x: x.strip().replace(
            " ", "").replace(
            "\n", ""), inplace=True)
    for header in list(init_df):
        if header not in required_headers_dict:
#            init_df = init_df.drop(labels=header, axis=1)
            if header not in required_headers_dict.values():
                init_df = init_df.drop(labels=header, axis=1)
        else:
            continue
    init_df.rename(columns=required_headers_dict, inplace=True)
    return init_df

def append_columns(starting_df, excel_loc, required_headers_dict, match_key):
    init_df = pd.read_excel(excel_loc, 0)
    init_df.rename(columns=lambda x: x.strip().replace(" ", ""), inplace=True)
    for header in list(init_df):
        if header not in required_headers_dict:
            init_df = init_df.drop(labels=header, axis=1)
    init_df.rename(columns=required_headers_dict, inplace=True)
    new_df = pd.merge(starting_df, init_df, on=match_key, how='left',indicator=False)
    return new_df

def sanitize_df(df):
    print("Sanitizing...")
    temp = df.copy(deep=True)
    temp = temp.fillna(0) 
    for column_name in temp.columns:
        if "date" in column_name:
            temp[column_name] = temp[column_name].apply(lambda x: convert_to_date(x))
               
    return temp        

def convert_to_date(data_point, debugdb = ""):
    if type(data_point) == datetime.datetime or type(data_point) == pd._libs.tslib.Timestamp:
        return_val = data_point.date()
        if str(return_val) == "1970-01-01":
            return_val = 0        
    else:
        return_val = data_point
    return return_val


    
