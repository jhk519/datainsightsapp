# -*- coding: utf-8 -*-
"""
Created on Fri Jun 22 13:12:47 2018

@author: Justin H Kim
"""
import datetime
from pprint import pprint
import os
import urllib
import io
import pickle

import sqlite3
import pandas as pd
import PIL
import requests

import queries
import exceltodataframe as etdf

class DBManagerEngine:
    def __init__(self,init_config = None):
        self.engine_name = "default"
        self.__config = {}
        self.__dbvar = None
        if init_config:
            self.set_build_config(init_config)
            
        self.__dbsdata = {}
            
    def __str__(self):
        return "{}".format(self.engine_name)  

    def set_build_config(self,raw_config):
        self.__config = self._gen_build_config(raw_config)
            
    def _gen_build_config(self,raw_config):
        dt = {}
        for target in ["loaddb_on_load","auto_name_export","loaddb_loc","db_build_config","header_ref",
                       "online_db_url","export_db_loc"]:
            dt[target] = raw_config.get(target,None)
        return dt  
    
    def time_str(self,key="now"):
        if key == "now":
            return datetime.datetime.now().strftime("%y%m%d-%H%M")    
    
    def gen_bare_dbs(self):
        dbs = {}
        template = self.__config["db_build_config"]
        for key in template:
            dbs[key] = None
        return dbs
    
    def get_db_ref(self):
        return self.__config["db_build_config"]
    
    def get_auto_load_db(self):
        return self.__config["loaddb_on_load"]

    def get_auto_load_loc(self):
        return self.__config["loaddb_loc"]
    
    def get_dbsdata(self):
        return self.__dbsdata
    
    def set_dbsdata(self,new_dbsdata):
        self.__dbsdata = new_dbsdata
    
    def should_auto_name_export(self):
        return self.__config["auto_name_export"]
    
    def get_export_db_loc(self):
        return self.__config["export_db_loc"]
    
    def get_header_ref(self):
        return self.__config["header_ref"]
    
    def get_db_url(self):
        return self.__config["online_db_url"]
    
    def gen_single_db(self, db_str, dir_loc):
        db_ref = self.get_db_ref()[db_str]
        ext = ".xlsx"
        req_excels_tpl = (db_ref["core"], db_ref["appends_list"])
        match_on_key = db_ref["match_on_key"]
        new_df = etdf.gen_single_db_from_excels(dir_loc, ext, self.get_header_ref(),
                                                req_excels_tpl, match_on_key)
        return new_df
    
    def reset_and_gen_single_db(self,db_str, dir_loc):
        self.__dbsdata[db_str] = self.gen_single_db(db_str,dir_loc)

    def reset_and_gen_all_dbs(self,dir_loc):
        self.__dbsdata = self.gen_bare_dbs()
        for db_str in self.__dbsdata:
            self.reset_and_gen_single_db(db_str,dir_loc)  
            
    def update_single_db(self,db_str,dir_loc):
        print("Adding Data to: ", db_str)
        db_ref = self.get_db_ref()[db_str]
        curr_df = self.__dbsdata[db_str]

        ext = ".xlsx"
        req_excels_tpl = (db_ref["core"], db_ref["appends_list"])
        match_on_key = db_ref["match_on_key"]

        self.__dbsdata[db_str] = etdf.add_data(curr_df, dir_loc, ext, self.get_header_ref(), 
                               req_excels_tpl,match_on_key)

    def update_data_all_dbs(self,dir_loc):
        for db_str in self.__dbsdata:
            self.update_single_db(db_str,dir_loc) 
            
    def load_offline_dbs(self,dir_loc):
        with open(dir_loc, "rb") as dbfile:
            try:
                self.set_dbsdata(pickle.load(dbfile))
            except:
                print("Likely in-compatible DB file.")
            
    def load_online_dbs(self,counter=None,ticker=None):
        url = self.get_db_url()
        first_response = requests.get(url,stream=True)
        x=0
        with open('databases//DH_DBS.pickle', 'wb') as dbfile:
            for chunk in first_response.iter_content(chunk_size=1000000):
                if counter:
                    counter.set(counter.get()+1)
                    ticker.update()
                dbfile.write(chunk)
                x += 1
        with open('databases//DH_DBS.pickle', "rb") as dbfile:
            self.__dbsdata = pickle.load(dbfile)
            
    def save_all_dbs(self,save_type="pickled_dataframe"):
        if save_type == "pickled_dataframe":
            with open('databases//DH_DBS.pickle', 'wb') as dbfile:
                pickle.dump(self.__dbsdata, dbfile)     
                
    def get_export_full_name(self,db_str,ftype="excel"):
        if ftype == "excel":
            ext = ".xlsx"
        elif ftype =="image":
            ext = ".png"
        elif ftype =="sqlite":
            ext = ".db"
            
        outname = db_str + self.time_str() + ext
        outdir = self.get_export_db_loc()
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        fullname = os.path.join(outdir, outname)      
        return fullname
    
    def df2sqlite(self,db_str, db_name="import.sqlite", tbl_name="import"):
        print("Preparing conversion to sqlite for: ", db_name)
        dataframe = self.__dbsdata[db_str]
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
    
        wildcards = ','.join(['?'] * len(dataframe.columns))
        data = [tuple(x) for x in dataframe.values]
        count = 0
        for x in data[3]:
            print(count)
            print(type(x), " is ", x)
            count += 1
    
        cur.execute("drop table if exists %s" % tbl_name)
    
        col_str = '"' + '","'.join(dataframe.columns) + '"'
        cur.execute("create table %s (%s)" % (tbl_name, col_str))
        cur.executemany("insert into %s values(%s)" % (tbl_name, wildcards), data)
        conn.commit()
        conn.close()
        print("Export to Sqlite Completed")    
        
class ProductViewerEngine:
    def __init__(self,init_config = None,init_dbvar = None):
        self.engine_name = "default"
        self.__config = {}
        self.__dbvar = None
        if init_config:
            self.set_build_config(init_config)
        if init_dbvar:
            self.set_dbvar(init_dbvar)
            
    def __str__(self):
        return "{}".format(self.engine_name)  
    
    def set_dbvar(self, newref):
        self.__dbvar = newref

    def set_build_config(self,raw_config):
        self.__config = self._gen_build_config(raw_config)
            
    def _gen_build_config(self,raw_config):
        dt = {}
        for target in []:
            dt[target] = raw_config.get(target,None)
        return dt  
    
    def time_str(self,key="now"):
        if key == "now":
            return datetime.datetime.now().strftime("%y%m%d-%H%M")
        
    def get_pdb_data(self):
        return self.__dbvar["pdb"]
    
    def get_pdb_product_data(self,pcode):
        pdb = self.get_pdb_data()
        x = pdb.loc[pdb['product_code'] == pcode]  
        return x
        
    def search_product(self,code=None):
        if not code is None and not code == "":
            pdb = self.get_pdb_product_data(code)
        else:
            return "no_code_given"
            
        if pdb.shape[0] < 1:
            return "no_results"
             
        plist = pdb.to_dict(orient='records')
        
        final_dict = {
            "product_info": {
                "product_code": "DEFAULT PRODUCT CODE",
                "vendor_name": "DEFAULT VENDOR NAME",
                "vendor_code": "DEFAULT VENDOR CODE",
                "vendor_price": "DEFAULT VENDOR PRICE",
                "main_image_url": "DEFAULT URL",
                "category": "DEFAULT  CATEGORY"
            },
            "sku_list": []
        }
            
        for sku_dict in plist:
            final_dict["product_info"]["product_code"] = sku_dict["product_code"]
            final_dict["product_info"]["vendor_name"] = sku_dict["vendor_name"]
            final_dict["product_info"]["vendor_code"] = sku_dict["vendor_code"]
            final_dict["product_info"]["vendor_price"] = sku_dict["vendor_price"]
            final_dict["product_info"]["main_image_url"] = sku_dict["main_image_url"]
            final_dict["product_info"]["category"] = sku_dict["category"]
            
            sku_full_options_text_split = sku_dict["option_text"].split(",")
            sku_color = sku_full_options_text_split[0]
            sku_size = sku_full_options_text_split[1]
            
            final_dict["sku_list"].append(
                (sku_dict["sku_code"],sku_color,sku_size, sku_dict["sku_image_url"])   
            )
        return final_dict
            
    def get_PIL_image(self,url):
        try:        
            raw_data = urllib.request.urlopen(url).read()
            im = PIL.Image.open(io.BytesIO(raw_data))
        except ValueError:
            print("THIS IMAGE AT ",url," IS NOT WORKING!")
            return None
        except AttributeError:
            print("CANNOT READ URLOPEN FOR ", url)
            return None
        else:
            return im            
        
class AnalysisPageEngine:
    def __init__(self,init_config = None,init_dbvar = None):
        self.engine_name = "default"
        self.__config = {}
        self.__dbvar = None
        if init_config:
            self.set_build_config(init_config)
        if init_dbvar:
            self.set_dbvar(init_dbvar)
            
    def __str__(self):
        return "{}".format(self.engine_name)  
    
    def set_dbvar(self, newref):
        self.__dbvar = newref

    def set_build_config(self,raw_config):
        self.__config = self._gen_build_config(raw_config)
            
    def _gen_build_config(self,raw_config):
        dt = {}
        for target in ["auto_export_loc","auto_name_exports","auto_query",
                       "metric_graph_refs","controls_config"]:
            dt[target] = raw_config.get(target,None)
        return dt  
    
    def time_str(self,key="now"):
        if key == "now":
            return datetime.datetime.now().strftime("%y%m%d-%H%M")

    def get_controls_cfg(self):
        return self.__config["controls_config"] 
    
    def should_auto_export(self):
        return self.__config["auto_name_exports"]
    
    def get_auto_export_loc(self):
        return self.__config["auto_export_loc"]
    
    def get_export_full_name(self,title,ftype="excel"):
        if ftype == "excel":
            ext = ".xlsx"
        else:
            ext = ".png"
        outname = title.replace(".","") + self.time_str("now") + ext
        outdir = self.get_auto_export_loc()
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        fullname = os.path.join(outdir, outname)      
        return fullname
    
    def get_export_excel_pack(self,mrp):
        """
        merged_export_results_pack = {
            "start":start,
            "end":end,
            "title": title,
            "line_labels": labels,
            "data_list_of_lists": datas
        }
        """
        line_labels = mrp["line_labels"]
        data_list_of_lists  = mrp["data_list_of_lists"]

        constructor_dict = {}
        for x in range(0, len(line_labels)):
            constructor_dict[line_labels[x]] = data_list_of_lists[x]
        newdf = pd.DataFrame(constructor_dict)
        
        sheetname = str(mrp["start"]) + " to " + str(mrp["end"])
        
        if self.should_auto_export():
            fullname = self.get_export_full_name(mrp["title"])
        else:    
            fullname = None
        
        return fullname,sheetname,newdf
    
    def determine_left_right_axis(self,pack):
        prm = pack["prime"]
        sec = pack["secondary"]
        p_req = prm["queries_list"] and prm["enabled"]
        s_req = sec["queries_list"] and sec["enabled"]
        
        if p_req and s_req:
            return prm,sec
        elif p_req and not s_req:
            return prm,None
        elif not p_req and s_req:
            return sec,None
        return None,None          
    
    def get_metric_graph_ref(self,metric_str):
        return self.__config["metric_graph_refs"][metric_str]
    
    def get_results_packs(self,pack):
        """
        pack = {
                "start":start,
                "end":end,
                "prime":{
                    "enabled":self.bl_enabled,
                    "scope":scope,
                    "extra":extra,
                    "metric":metric,
                    "queries_list":[("query_str","red"),("query_str2","blue")]}
              "secondary":{
                    "enabled":self.bl_enabled,
                    "scope":scope,
                    "extra":extra,
                    "metric":metric,
                    "queries_list":[("query_str2","red"),("query_str2","blue")]}
        """        
        start = pack["start"]
        end = pack["end"]
        axes_select_packs = self.determine_left_right_axis(pack)
        axes_result_packs = [None,None]

        for ind,axis in enumerate(axes_select_packs):
            if axis:
                metric = axis["metric"]
                metric_graph_ref = self.get_metric_graph_ref(metric)
                ls_queries = []
                ls_x_axis_data = []
                ls_y_axis_data_lists = []
                ls_colors_to_plot = []
                
                for query_count,query_tuple in enumerate(axis["queries_list"]):
                    ls_queries.append(query_tuple[0])
                    ls_colors_to_plot.append(query_tuple[1])
                    queryx, queryy = list(queries.main(query_tuple[0],
                                                       self.__dbvar,
                                                       start,
                                                       end,
                                                       extra=axis["extra"]))  
                    if query_count == 0:
                        ls_x_axis_data = queryx
                    ls_y_axis_data_lists.append(queryy)
                    
                rp  = {
                    "start":start,
                    "end":end,
                    "met": metric,
                    "gtype": metric_graph_ref["type"],
                    "str_x": metric_graph_ref["xaxis_label"],
                    "str_y": metric_graph_ref["yaxis_label"],
                    "line_labels":ls_queries,
                    "x_data": ls_x_axis_data,
                    "y_data": ls_y_axis_data_lists,
                    "colors":ls_colors_to_plot,
                }
                axes_result_packs[ind] = rp          
        return axes_result_packs
    
    def _get_data_lists(self, ls_queries_to_plot, start, end, extra=None):
        ls_line_labels = []
        ls_x_axis_data = []
        ls_y_axis_data_lists = []
        for str_query in ls_queries_to_plot:
            count = 0
            ls_line_labels.append(str_query)
            queryx, queryy = list(queries.main(str_query,
                                               self.app.datahub.dbs,
                                               start,
                                               end,
                                               self.app.cfg,
                                               extra=extra))
# just take x-axis from first query. but you can take any theoretically.
            if count == 0:
                ls_x_axis_data = queryx
            ls_y_axis_data_lists.append(queryy)
            count += 1
        return ls_line_labels, ls_x_axis_data, ls_y_axis_data_lists          
        
class ControlPanelEngine:
    def __init__(self,init_config = None):
        self.engine_name = "default"
        self.__config = {}
        if init_config:
            self.set_build_config(init_config)
            
    def __str__(self):
        return "{}".format(self.engine_name)  

    def set_build_config(self,raw_config):
            self.__config = self._gen_build_config(raw_config)
        
    def _gen_build_config(self,raw_config):
        return {"axis_panel_names":raw_config.get("axis_panel_names",[]),
                "setdates_on_load":raw_config.get("setdates_on_load",None),
                "setdates_gap":raw_config.get("setdates_gap",None),
                "setdates_from_date":raw_config.get("setdates_from_date",None),
                "queries_config":raw_config.get("queries_config",{})
                }   
        
    def should_set_dates_on_load(self):
        return self.__config["setdates_on_load"]
        
    def get_set_date_config(self):
        return (self.__config["setdates_gap"],self.__config["setdates_from_date"])

    def get_query_panel_names(self):
        return self.__config["axis_panel_names"]   

    def get_queries_config(self):
        return self.__config["queries_config"]
    
    def set_end_date(self,date_cfg_pack):
        days_back = int(date_cfg_pack[0])
        from_what_day = date_cfg_pack[1]
        
        if from_what_day == "today":
            self.end_date = datetime.datetime.today().date()
        elif from_what_day == "yesterday":
            self.end_date = (
                datetime.datetime.today() -
                datetime.timedelta(1)).date()
        elif len(from_what_day) == 8:
            try:
                int(from_what_day)
            except ValueError:
                print("from_what_day in ._auto_test is not a valid date string.")
                return
            year = int(from_what_day[0:4])
            month = int(from_what_day[4:6])
            day = int(from_what_day[6:8]) 
            end_date = datetime.date(year, month, day)
            start_date = end_date - datetime.timedelta(days_back)
        return start_date,end_date


class QueryPanelEngine:
    def __init__(self,init_config = None):
        self.engine_name = "default"
        self.config = {}
        if init_config:
            self.set_build_config(init_config)
            
    def __str__(self):
        return "{}".format(self.engine_name)  

    def set_build_config(self,raw_config):
            self.config = self.gen_build_config(raw_config)
        
    def gen_build_config(self,raw_config):
        return {"pages_to_scopes_ref":raw_config.get("pages_to_scopes_ref",None),
                "scopes_to_metrics":raw_config.get("scopes_to_metrics_ref",None),
                "metrics_to_queries_ref":raw_config.get("metrics_to_queries_ref",None),
                "colors_preferred": raw_config.get("colors_preferred",[])}
        
    def get_scopes(self,page):
        a_list = []
        for key in self.config["pages_to_scopes_ref"][page]:
            a_list.append(key)
        return a_list
    
    def get_extra(self,scope):
        try:
            extra_details = self.config["scopes_to_metrics"].get(scope,None)["extra"]
        except TypeError:
            return False
        if extra_details:
            if extra_details["use"]:
                return extra_details
            else:
                return False
        else:
            raise KeyError
    
    def get_metrics(self,scope):
        a_list = []
        for key in self.config["scopes_to_metrics"][scope]["metrics"]:
            a_list.append(key)
        return a_list
    
    def get_queries(self,metric):
        return self.config["metrics_to_queries_ref"][metric][1]

    def should_exclude(self,metric):
        return self.config["metrics_to_queries_ref"][metric][0]
    
    def get_colors_preferred(self):
        return self.config["colors_preferred"].split("-")