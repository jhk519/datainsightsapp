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
import numpy as np
import PIL
import requests
import copy
import pandastable
import logging

import queries
import exceltodataframe as etdf

class DefaultEngine:
    def __init__(self,init_config = None,init_dbvar=None,name=""):
        self.engine_name = "Default" + name + "Engine"
        self.log = logging.getLogger(__name__).info
        self.log("{} Init.".format(self.engine_name))    
        self.bug = logging.getLogger(__name__).debug
        self.__cfgvar = init_config      
        self.__dbvar = init_dbvar
        self.__req_headers = []        

#   API
    def set_build_config(self,raw_config):
        if self._check_req_headers(config_to_check=raw_config):
            self.__cfgvar = raw_config
        else:
            print("New Config is Incompatible. Setting new Config terminated.")
            
    def set_dbvar(self,new_dbdata):
        self.__dbvar = new_dbdata    
        
    def get_dbvar(self):
        return self.__dbvar
    
    def get_config(self,need_copy=False):
        if need_copy:
            return copy.deepcopy(self.__cfgvar)
        else:
            return self.__cfgvar
        return self.__cfgvar
             
    def time_str(self,key="now"):
        if key == "now":
            return datetime.datetime.now().strftime("%y%m%d-%H%M") 
        
    def get_cfg_val(self,key):
        print(self.__cfgvar)
        try: 
            value = self.__cfgvar[key]
        except TypeError:
            self.bug("Could not get cfg_val for: {} for {} config.".format(key,self.engine_name))
        return value
    
    def get_export_full_name(self,db_str,ftype="excel"):
        if ftype == "excel":
            ext = ".xlsx"
        elif ftype =="image":
            ext = ".png"
        elif ftype =="sqlite":
            ext = ".db"
            
        outname = db_str + self.time_str() + ext
        outdir = self.get_cfg_val("automatic export location")
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        fullname = os.path.join(outdir, outname)      
        return fullname  
             
    def _check_req_headers(self,config_to_check=None):
        if not config_to_check:
            config_to_check = self.__config
        passed = True
        for target in self.__req_headers:
            if not config_to_check.get(target,False):
                print("MISSING HEADER: ", target)
                passed = False
        return passed

class SettingsManagerEngine(DefaultEngine):
#    Note that settingsmanager does not use dbvar at all
    def __init__(self,init_config=None, init_dbvar=None):
        super().__init__(init_config=init_config,init_dbvar=init_dbvar,name="SettingsManager")    
        self.user_settings = []
        
    def load_ini_settings(self,parser_sections):
        temp_cfg = self.get_config(need_copy=True)
        self.user_settings = []
        for section_header,section_cfg in parser_sections.items():
            for setting_header, setting_str in section_cfg.items():
                try:
                    temp_cfg[section_header]
                except KeyError:
                    print(section_header,"from .ini file not found in config.")
                    print("This will mean updates to ini will not be unpacked and config updated.")
                    continue
                set_val,set_type = setting_str.split("$$")
                final_val = self._get_clean_val(set_val,set_type)
                temp_cfg[section_header][setting_header] = final_val
                self.user_settings.append([section_header,setting_header,final_val,set_type])
        self.set_build_config(temp_cfg)   
        
    def _get_clean_val(self,setting_val,setting_type):
        if setting_type == "bool":
            if setting_val == "True":
                val = True
            elif setting_val == "False":
                val = False
            else:
                print("ERROR, NOT SUITABLE VAL: ", setting_val,"FOR",setting_type)
                raise ValueError
        elif setting_type == "int":
            val = int(setting_val)
        elif setting_type in ["list","date","str","dirloc","fileloc","colors"]:
            val = setting_val
        else:
            print("INVALID TYPE FOR SETTING! - ", setting_type, " - ", setting_val)
            val = None   
        return val

class DBManagerEngine(DefaultEngine):
    def __init__(self,init_config=None, init_dbvar=None):
        super().__init__(init_config=init_config,init_dbvar=init_dbvar,name="DBManager")

    def gen_bare_dbs(self):
        dbs = {}
        template = self.get_cfg_val("db_build_config")
        for key in template:
            dbs[key] = None
        return dbs   

    def gen_single_db(self, db_str, dir_loc):
        db_ref = self.get_cfg_val("db_build_config")[db_str]
        ext = ".xlsx"
        req_excels_tpl = (db_ref["core"], db_ref["appends_list"])
        match_on_key = db_ref["match_on_key"]
        new_df = etdf.gen_single_db_from_excels(dir_loc, ext, self.get_cfg_val("header_ref"),
                                                req_excels_tpl, match_on_key)
        return new_df
    
    def reset_and_gen_single_db(self,db_str, dir_loc):
        self.get_dbvar()[db_str] = self.gen_single_db(db_str,dir_loc)

    def reset_and_gen_all_dbs(self,dir_loc):
        self.set_dbvar(self.gen_bare_dbs())
        for db_str in self.get_dbvar():
            self.reset_and_gen_single_db(db_str,dir_loc)  
            
    def update_single_db(self,db_str,dir_loc):
        print("Adding Data to: ", db_str)
        db_ref = self.get_cfg_val("db_build_config")[db_str]
        curr_df = self.get_dbvar()[db_str]
        ext = ".xlsx"
        req_excels_tpl = (db_ref["core"], db_ref["appends_list"])
        match_on_key = db_ref["match_on_key"]

        self.get_dbvar()[db_str] = etdf.add_data(curr_df, dir_loc, ext, self.get_cfg_val("header_ref"), 
                               req_excels_tpl,match_on_key)
        
#        print(self.engine_name, "\n", id(self.get_dbvar()))

    def update_data_all_dbs(self,dir_loc):
        for db_str in self.get_dbvar():
            self.update_single_db(db_str,dir_loc) 
            
    def load_offline_dbs(self,dir_loc):
        with open(dir_loc, "rb") as dbfile:
            try:
                self.set_dbvar(pickle.load(dbfile))
            except:
                print("Likely in-compatible DB file.")
            
    def load_online_dbs(self,counter=None,ticker=None):
        url = self.get_cfg_val("URL for Online DB Download")
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
            self.set_dbvar(pickle.load(dbfile))
            
    def save_all_dbs(self,save_type="pickled_dataframe"):
        if save_type == "pickled_dataframe":
            with open('databases//DH_DBS.pickle', 'wb') as dbfile:
                pickle.dump(self.get_dbvar(), dbfile)     
                
#    def get_export_full_name(self,db_str,ftype="excel"):
#        if ftype == "excel":
#            ext = ".xlsx"
#        elif ftype =="image":
#            ext = ".png"
#        elif ftype =="sqlite":
#            ext = ".db"
#            
#        outname = db_str + self.time_str() + ext
#        outdir = self.get_cfg_val("automatic export location")
#        if not os.path.exists(outdir):
#            os.mkdir(outdir)
#        fullname = os.path.join(outdir, outname)      
#        return fullname
    
    def df2sqlite(self,db_str, db_name="import.sqlite", tbl_name="import"):
        print("Preparing conversion to sqlite for: ", db_name)
        dataframe = self.get_dbvar()[db_str]
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
    
        wildcards = ','.join(['?'] * len(dataframe.columns))
        data = [tuple(x) for x in dataframe.values]
        count = 0
        for x in data[3]:
#            print(count)
#            print(type(x), " is ", x)
            count += 1
    
        cur.execute("drop table if exists %s" % tbl_name)
    
        col_str = '"' + '","'.join(dataframe.columns) + '"'
        cur.execute("create table %s (%s)" % (tbl_name, col_str))
        cur.executemany("insert into %s values(%s)" % (tbl_name, wildcards), data)
        conn.commit()
        conn.close()
        print("Export to Sqlite Completed")    
        
class ProductViewerEngine(DefaultEngine):
    def __init__(self,init_config = None, init_dbvar=None, name="ProductViewer"):
        super().__init__(init_config=init_config, init_dbvar=init_dbvar,
                         name="ProductViewer")
        
        self.bug("Post-Super Init for {} Engine".format(name))
        
    def get_cdb_data(self):
        cdb = self.get_dbvar()["cdb"]
        self.log("Cdb Got.")
        return cdb
     
    def get_odb_data(self):
        odb = self.get_dbvar()["odb"]
        self.log("Odb Got.")
        return odb
    
    def get_orders_by_product(self,product_code):
        temp_odb = self.get_odb_data()
        locced = temp_odb.loc[temp_odb["product_cafe24_code"] == product_code]
        self.log("Got Locced.")
        return locced
        
    def get_pdb_product_data(self,pcode):
        pdb = self.get_dbvar()["pdb"]
        x = pdb.loc[pdb['product_code'] == pcode]  
        return x
    
    def get_customers_list(self,code):
        if not code is None and not code == "":
            filtered_odb = self.get_orders_by_product(code)
            if filtered_odb.shape[0] < 1:
                self.bug("No orders for this product code: {}".formaT(code))
                return "No Results"
            else:
                dropped = filtered_odb.drop_duplicates(subset="customer_phone_number")
                return dropped
        else:
            self.bug("No Code Given")
            return "No Code Given"
        
    def search_product(self,code):
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

class MultiGrapherEngine(DefaultEngine):
    def __init__(self, init_config=None, init_dbvar=None):
        super().__init__(init_config=init_config, init_dbvar=init_dbvar, name="MultiGrapher")         
        
class AnalysisPageEngine(DefaultEngine):
    def __init__(self, init_config=None, init_dbvar=None):
        super().__init__(init_config=init_config, init_dbvar=init_dbvar, name="AnalysisPage")
    

    
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
        
        if self.get_cfg_val("automatic search export"):
            fullname = self.get_export_full_name(mrp["title"])
        else:    
            fullname = None
        
        return fullname,sheetname,newdf 
    
    def has_queries_req(self,queriespacklist):
        found_something = False
        for qpack in queriespacklist:
            if not qpack[0] == "None":
                found_something = True
        return found_something           
    
    def determine_left_right_axis(self,pack):
        p_req = self.has_queries_req(pack["left"]["queries"])
        s_req = self.has_queries_req(pack["right"]["queries"])
        
        if p_req and s_req:
            return pack["left"],pack["right"]
        elif p_req and not s_req:
            return pack["left"],None
        elif not p_req and s_req:
            return pack["right"],None
        return None,None         
    
    def get_results_packs(self,pack):
        """
        pack = {
            "start":start,
            "end":end,
            "hold_y":self.hold_y_var         
            "extra":self.extra_var.get(),
            "x_axis_label": self.x_axis_type.get(),
            "mirror_days": self.mirror_days_var.get(),  
            "left": {
                "frame": None,
                "gtype":None,
                "db-type": None,
                "metric": None,
                "queries":[(qstr,qcolor),(qstr,qcolor)]
            },
            "right": {
                "frame": None,
                "gtype":None,
                "db-type": None,
                "metric": None,
                "queries":[(qstr,qcolor),(qstr,qcolor)] 
            },            
        }
        """      
       
        start = pack["start"]       
        end = pack["end"]
        axes_select_packs = self.determine_left_right_axis(pack)
        axes_result_packs = [None,None,pack["hold_y"]]
        if bool(pack["mirror_days"]):
            m_start = (start - datetime.timedelta(pack["mirror_days"]))
            m_end = (end - datetime.timedelta(pack["mirror_days"]))

        for ind,axis in enumerate(axes_select_packs):
            if axis:
                ls_queries = []
                x_data = []
                y_data_lists = []
                colors_to_plot = []
                
                for index,query_tuple in enumerate(axis["queries"]):
                    
                    first_found = True
                    if not query_tuple[0] == "None":
                        ls_queries.append(query_tuple[0])
                        colors_to_plot.append(query_tuple[1])
                        xandy = queries.main(query_tuple[0],
                            self.get_dbvar(),start,end,extra=pack["extra"])
                        if xandy == "No Date Data":
                            return xandy
                        queryx,queryy = xandy
                        if first_found:
                            x_data = queryx
                            first_found = False
                        y_data_lists.append(queryy)
                        
                        if bool(pack["mirror_days"]):
                            ls_queries.append(query_tuple[0] + "_Mirror")
                            colors_to_plot.append(query_tuple[1])
                            xandy = queries.main(query_tuple[0],
                                self.get_dbvar(),m_start,m_end,extra=pack["extra"])
                            if xandy == "No Date Data":
                                return xandy
                            queryx,queryy = xandy
                            if first_found:
                                x_data = queryx
                                first_found = False
                            y_data_lists.append(queryy)                            
                        
                    
                rp  = {
                    "start":start,
                    "end":end,
                    "met": axis["metric"],
                    "gtype": axis["gtype"],
                    "str_x": pack["x_axis_label"],
                    "str_y": axis["metric"],
                    "line_labels":ls_queries,
                    "x_data": x_data,
                    "y_data": y_data_lists,
                    "colors":colors_to_plot,
                }
                axes_result_packs[ind] = rp          
        return axes_result_packs      
        
class ControlPanelEngine(DefaultEngine):
    def __init__(self, init_config=None, init_dbvar=None):
        super().__init__(init_config=init_config, init_dbvar=init_dbvar, name="ControlPanel")
        
    def get_set_date_config(self):
        return (self.get_cfg_val("setdates_gap"),self.get_cfg_val("setdates_from_date"))
    
    def set_end_date(self,date_cfg_pack):
        days_back = int(date_cfg_pack[0])
        from_what_day = date_cfg_pack[1]
        
        if from_what_day == "today":
            self.end_date = datetime.datetime.today().date()
        elif from_what_day == "yesterday":
            self.end_date = (datetime.datetime.today() - datetime.timedelta(1)).date()
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


class QueryPanelEngine(DefaultEngine):
    def __init__(self, init_config=None, init_dbvar=None):
        super().__init__(init_config=init_config, init_dbvar=init_dbvar, name="QueryPanel")
        
    def get_categories(self):
        return self.get_cfg_val("categories")
    
    def get_queries_list(self,category):
        qlist = []
        if category:
            for k,v in self.get_cfg_val("queries_ref").items():
                if v["category"] == category:
                    qlist.append(k)    
        else:
            qlist = list(self.get_cfg_val("queries_ref").keys())
        qlist.sort()
        return qlist
    
    def get_colors_preferred(self):
        return self.get_cfg_val("colors_preferred").split("-")
    
class DataTableEngine(DefaultEngine):
    def __init__(self, init_config=None, init_dbvar=None):
        super().__init__(init_config=init_config, init_dbvar=init_dbvar, name="DataTable") 
        
        """
        cfg/mrp = {
            "start":start,
            "end":end,
            "title": title,
            "line_labels": labels,
            "data_list_of_lists": datas
        }      
        """

    def get_rows_of_data(self):
        list_of_rows = []
        for row_c,data_pt in enumerate(self.get_cfg_val("data_list_of_lists")[0]):
            row_values = []
            for index, data_list in enumerate(self.get_cfg_val("data_list_of_lists")):
                val = data_list[row_c]
                if isinstance(val, float) or isinstance(val, np.float64):
                    val = round(val, 2)
                row_values.append(val)
            list_of_rows.append(row_values)
        return list_of_rows                             