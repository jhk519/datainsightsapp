# -*- coding: utf-8 -*-
"""
Created on Wed May  2 22:27:37 2018

@author: Justin H Kim
"""
# Standard Modules
import os
from pprint import pprint
import logging

# Non-Standard Modules
import pandas as pd
import datetime
from openpyxl import load_workbook


log = logging.getLogger(__name__).info
log("{} Init.".format(__name__))    
bug = logging.getLogger(__name__).debug       


def add_data(curr_df,dir_loc,ext,hr_dict,req_excels_tpl,match_on_key):
    log("Adding Data...")
    append_df = gen_single_db_from_excels(dir_loc,ext,hr_dict,req_excels_tpl,
        match_on_key)
    log("Append DF length: {} {}".format(append_df.shape[0],append_df.shape[1]))
    new_df = pd.concat([curr_df, append_df], axis=0, ignore_index = True,
                       join = "outer")  
    return sanitize_df(new_df)
    
def gen_single_db_from_excels(expath,ext,hr_dict,req_excels_tpl,
        match_on_key):       
    core_req_exc = req_excels_tpl[0]
    append_excs_list = req_excels_tpl[1]
    log("Starting with Core: {} at {}".format(core_req_exc,expath))
    if os.path.isfile(expath):    
        temp_df = gen_core_db(expath, hr_dict[core_req_exc])
    else: 
        bug("NO EXCEL EXISTS AT ", expath)
        return
    for adb in append_excs_list:
        log("Appending Secondary Data: ",adb)
        if os.path.isfile(expath):  
            temp_df = append_columns(
                temp_df,
                expath,
                hr_dict[adb],
                match_on_key)
        else:
            bug("NO APPEND")
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
    log("Sanitizing...")
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


    
