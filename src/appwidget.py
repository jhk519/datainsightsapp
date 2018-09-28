# -*- coding: utf-8 -*-
"""
Created on Thu Aug 30 12:59:56 2018

@author: Justin H Kim
"""
import tkinter as tk
import tkinter.ttk as ttk

import logging
import datetime
import os
import pickle
import sqlite3
import PIL
import requests
import copy
import urllib
import io
import numpy as np
import pandas as pd
from pprint import pprint

import queries
import exceltodataframe as etdf

class AppWidget(tk.Frame):
    def __init__(self,parent,controller,config,dbvar,showlog=True):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        
        if not showlog:
            self.log = print
        else:
            self.log = logging.getLogger(__name__ + "-" + self.widget_name).info
            self.log("Init.")
        self.bug = logging.getLogger(self.widget_name).debug   
        
        self._req_headers = []  
        self.config_chain = []
        self.popupentryvar = tk.StringVar()        
        
        try:
            config[self.widget_name]
        except KeyError:
            self.bug("{} not in config. Check config2 file.".format(self.widget_name))
            self.set_build_config({})
        else:
            self.set_build_config(config[self.widget_name])
            
        self.__dbvar = dbvar  
        
        if self.widget_name == "dbmanager":
            self.engine = DBManagerEngine()
        elif self.widget_name == "analysispage":
            self.engine = AnalysisPageEngine()
        elif self.widget_name == "querypanel":
            self.engine = QueryPanelEngine()
        elif self.widget_name == "newquerypanel":
            self.engine = QueryPanelEngine()
        elif self.widget_name == "datatable":
            self.engine = DataTableEngine()
        elif self.widget_name == "productviewer":
            self.engine = ProductViewerEngine()
        elif self.widget_name == "multigrapher":
            self.engine = MultiGrapherEngine()
        elif self.widget_name == "settingsmanager":
            self.engine = SettingsManagerEngine()
            return
        else:
            self.bug("{} does not match any available engines".format(self.widget_name))

#   API
    def set_build_config(self,raw_config):
        if self._check_req_headers(config_to_check=raw_config):
            self.log("Passed Check Req Headers.")
            self.__cfgvar = raw_config
        else:
            self.bug("New Config is Incompatible. Setting new Config terminated.")
            
    def set_dbvar(self,new_dbdata):
        self.__dbvar = new_dbdata    
        
    def get_dbvar(self):
        return self.__dbvar
    
    def get_config(self,need_copy=False):
        if need_copy:
            return copy.deepcopy(self.__cfgvar)
        else:
            return self.__cfgvar
             
    def get_time_str(self,key="now"):
        if key == "now":
            return datetime.datetime.now().strftime("%y%m%d-%H%M%S") 
        
    def get_cfg_val(self,key):
        try: 
            value = self.__cfgvar[key]
        except TypeError:
            self.bug("Could not get cfg_val for: {} for {} config.".format(key,__name__ + "-" + self.widget_name))
            return None
        except KeyError:
            self.bug("This key is not found in cfg! {}".format(key))
            return None
        else:
            return value
    
    def get_export_full_name(self,base_string,ftype="excel",outdir=None):
        if ftype == "excel":
            ext = ".xlsx"
        elif ftype =="image":
            ext = ".png"
        elif ftype =="sqlite":
            ext = ".db"
            
        outname = base_string + self.get_time_str() + ext
        if not outdir:
            outdir = self.get_cfg_val("automatic export location")
            self.log("outdir from config: {}".format(outdir))
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        fullname = os.path.join(outdir, outname)      
        return fullname  
             
    def _check_req_headers(self,config_to_check=None):
        if not config_to_check:
            config_to_check = self.__cfgvar
        passed = True
        for target in self._req_headers:
            if not config_to_check.get(target,False):
                self.bug("MISSING HEADER: {}".format(target))
                passed = False
        return passed    
    
    #   API       
    def set_cfgvar(self,new_cfgvar):
        self.log("Changing cfg.")
        self.set_build_config(new_cfgvar[self.widget_name]) 
        for widget in self.config_chain:
            widget.set_cfgvar(new_cfgvar)
        
    def create_popup(self,title,text,entrycommand=False,firstb=None,secondb=None):
        #firstb secondb is ("BUTTONTEXT",BUTTONCOMMAND)        
        self.popup = tk.Toplevel()
        self.popup.title(title)
        tk.Message(self.popup,text=text).pack()
        if firstb and secondb:
            tk.Button(self.popup,text=firstb[0],command=firstb[1]).pack()
            tk.Button(self.popup,text=secondb[0],command=secondb[1]).pack()
            tk.Button(self.popup,text="OK",command=self.popup.destroy).pack()
        if entrycommand:
            tk.Entry(self.popup,textvariable=self.popupentryvar).pack()
            tk.Button(self.popup,text="Set",command=entrycommand).pack()
            tk.Button(self.popup,text="Close",command=self.popup.destroy).pack()
            
        return self.popup
            
    def _sortby(self, tree, col, descending):
        """sort tree contents when a column header is clicked on
        please note this function was taken online and not my own. 
        """
        # grab values to sort
        data = [(tree.set(child, col), child)
                for child in tree.get_children('')]
        # if the data to be sorted is numeric change to float
        #data =  change_numeric(data)
        # now sort the data in place
        data.sort(reverse=descending)
        for ix, item in enumerate(data):
            tree.move(item[1], '', ix)
        # switch the heading so it will sort in the opposite direction
        tree.heading(
            col, command=lambda col=col: self.sortby(
                tree, col, int(
                    not descending)))   
        
class CreateToolTip(object):
    """
    create a tooltip for a given widget
    CREDIT FOR THIS CLASS HERE:
        crxguy52 @ https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tkinter
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()        
            
class SettingsManagerEngine():
    def __init__(self):    
        self.log = logging.getLogger(__name__).info
        self.log("Init.")
        self.bug = logging.getLogger(__name__).debug    
        
    def get_updated_config(self, app_cfg, parser_sections):
        """ Receives parser._sections from user_settings.ini, and replaces the
        key-value pairs in the default config2
        """
        
        user_settings = []
        for section_header,section_cfg in parser_sections.items():
            for setting_header, setting_str in section_cfg.items():
                try:
                    app_cfg[section_header]
                except KeyError:
                    self.bug("{} from .ini file not found in config.".format(section_header))
                    self.bug("This will mean updates to ini will not be unpacked and config updated.")
                    continue
                set_type,set_val = setting_str.split("$$")
                final_val = self._get_clean_val(set_val,set_type)
                app_cfg[section_header][setting_header] = final_val
                user_settings.append([section_header,setting_header,final_val,set_type])
        try:
            with open('settings//presets.pickle',"rb") as presetlist:
                app_cfg["multigrapher"]["presetpages"] = pickle.load(presetlist) 
        except FileNotFoundError:
            self.bug("No preset pickle file found. Skipping.")
        return app_cfg,user_settings  
        
    def _get_clean_val(self,setting_val,setting_type):
        if setting_type == "bool":
            if setting_val == "True":
                val = True
            elif setting_val == "False":
                val = False
            else:
                self.bug("ERROR, {} NOT SUITABLE VAL: FOR {}".format(setting_val,setting_type))
                raise ValueError
        elif setting_type == "int":
            val = int(setting_val)
        elif setting_type in ["list","date","str","dirloc","fileloc","colors","event_dates"]:
            val = setting_val
        else:
            self.bug("INVALID TYPE FOR SETTING! - {} - {}".format(setting_type, setting_val))
            val = None   
        return val

class DBManagerEngine():
    def __init__(self):    
        self.log = logging.getLogger(__name__).info
        self.log("Init.")
        self.bug = logging.getLogger(__name__).debug  
        
    def _gen_bare_dbs(self):
        dbs = {}
        template = self.get_cfg_val("db_build_config")
        for key in template:
            dbs[key] = None
        return dbs   
    
    def get_cdb(self,odb):
#        print(odb.head)
        adb = odb[["customer_phone_number","customer_id"]]
#        print(type(adb))
        cdb = adb.drop_duplicates()
        return cdb
    
    #    to get a pdb roughly from an odb
    def get_pdb(self,odb):
        adb = odb[["product_cafe24_code","product_option"]]
        cdb = adb.drop_duplicates()
        return cdb        
        
    def gen_single_db(self, db_ref, path_list,header_ref):
        ext = ".xlsx"
        req_excels_tpl = (db_ref["core"], db_ref["appends_list"])
        match_on_key = db_ref["match_on_key"]
        
        for index, path in enumerate(path_list):
            if index == 0:
                new_df = etdf.gen_single_db_from_excels(path, ext, header_ref,
                                                        req_excels_tpl, match_on_key)
            else:
                new_df =  etdf.add_data(new_df, path, ext, header_ref, 
                               req_excels_tpl,match_on_key)                
        return new_df        

    def update_single_db(self,db_str,path_list,db_ref,new_df,header_ref):
#        self.log("Adding Data to: {}".format(db_str))
        ext = ".xlsx"
        req_excels_tpl = (db_ref["core"], db_ref["appends_list"])
        match_on_key = db_ref["match_on_key"]
        
        for index, path in enumerate(path_list):
#            self.log("Updating from path {}".format(path))
            new_df =  etdf.add_data(new_df, path, ext, header_ref, 
                               req_excels_tpl,match_on_key)
        return new_df
#    
#    def load_offline_dbs(self,dir_loc):
#        with open(dir_loc, "rb") as dbfile:
#            try:
#                self.set_dbvar(pickle.load(dbfile))
#            except:
#                print("Likely in-compatible DB file.")
            
    def load_online_dbs(self,counter=None,ticker=None):
        url = self.get_cfg_val("URL for Online DB Download")
        first_response = requests.get(url,stream=True)
#        x=0
        with open('databases//DH_DBS.pickle', 'wb') as dbfile:
            for chunk in first_response.iter_content(chunk_size=1000000):
                if counter:
                    counter.set(counter.get()+1)
                    ticker.update()
                dbfile.write(chunk)
#                x += 1
                
        with open('databases//DH_DBS.pickle', "rb") as dbfile:
            return dbfile

    def df2sqlite(self,dataframe, db_name="import.sqlite", tbl_name="import"):
        self.log("Preparing conversion to sqlite for: {}".format(db_name))
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
    
        wildcards = ','.join(['?'] * len(dataframe.columns))
        data = [tuple(x) for x in dataframe.values]
        count = 0
        for x in data[3]:
            count += 1
    
        cur.execute("drop table if exists %s" % tbl_name)
    
        col_str = '"' + '","'.join(dataframe.columns) + '"'
        cur.execute("create table %s (%s)" % (tbl_name, col_str))
        cur.executemany("insert into %s values(%s)" % (tbl_name, wildcards), data)
        conn.commit()
        conn.close()
        self.log("Export to Sqlite Completed")    
        
class ProductViewerEngine():
    def __init__(self):    
        self.log = logging.getLogger(__name__).info
        self.log("Init.")
        self.bug = logging.getLogger(__name__).debug   
#        
#        self.bug("Post-Super Init for {} Engine".format(name))
        
#    def get_cdb_data(self):
#        cdb = self.get_dbvar()["cdb"]
#        return cdb
#    
#    def _get_orders_by_product(self,product_code):
#        temp_odb = self.get_dbvar()["odb"]
#        locced = temp_odb.loc[temp_odb["product_cafe24_code"] == product_code]
#        self.log(".get_orders_by_product locced df length: {}".format(locced.shape[0]))
#        return locced
        
    def get_pdb_product_data(self,pdb, code,codetype):
        self.log("Getting pdb data for {}, search_type: {}, objecttype: {}".format(code,codetype,str(type(code))))
        
        self.log("Orig. pdb length: {}".format(pdb.shape[0]))
        if codetype == "Product Code":
            returndf = pdb.loc[pdb['product_cafe24_code'] == code]  
        elif codetype == "Barcode":
            returndf = pdb.loc[pdb['sku_code'] == int(code)]
        self.log("Locced pdb length: {}".format(returndf.shape[0]))
        return returndf
    
    def get_customers_list(self,temp_odb,code):
        self.log("Called with code: {}".format(code))
        if not code is None and not code == "":
            filtered_odb = temp_odb.loc[temp_odb["product_cafe24_code"] == code]            
            if filtered_odb.shape[0] < 1:
                self.bug("No orders for this product code: {}".format(code))
                return "no_results"
            else:
                dropped = filtered_odb.drop_duplicates(subset="customer_phone_number")
                return dropped
        else:
            self.bug("No Code Given")
            return "no_code_given"
        
    def search_product(self,pdb, code,codetype):
        self.log("Code Search: {}".format(code))
        if not code is None and not code == "":
            
            filtered_pdb = self.get_pdb_product_data(pdb,code, codetype)
        else:
            return "no_code_given"
            
        if filtered_pdb.shape[0] < 1:
            self.bug("Search yielded a DF less than 1 length.")
            return "no_results"
        else:
            self.log("Search yielded DF of {} length.".format(filtered_pdb.shape[0]))
             
        plist = filtered_pdb.to_dict(orient='records')
        
        final_dict = {
            "product_info": {
                "product_code": "DEFAULT PRODUCT CODE",
#                "vendor_name": "DEFAULT VENDOR NAME",
#                "vendor_code": "DEFAULT VENDOR CODE",
#                "vendor_price": "DEFAULT VENDOR PRICE",
                "main_image_url": "DEFAULT URL",
                "category": "DEFAULT  CATEGORY"
            },
            "sku_list": []
        }
            
        for sku_dict in plist:
            final_dict["product_info"]["product_cafe24_code"] = sku_dict["product_cafe24_code"]
#            final_dict["product_info"]["vendor_name"] = sku_dict["vendor_name"]
#            final_dict["product_info"]["vendor_code"] = sku_dict["vendor_code"]
#            final_dict["product_info"]["vendor_price"] = sku_dict["vendor_price"]
#            final_dict["product_info"]["main_image_url"] = sku_dict["main_image_url"]
            final_dict["product_info"]["category"] = sku_dict["category"]
            
            sku_full_options_text_split = sku_dict["option_text"].split(",")
            sku_color = sku_full_options_text_split[0]
            sku_size = sku_full_options_text_split[1]
            
            final_dict["sku_list"].append(
                (sku_dict["sku_code"],sku_color,sku_size, sku_dict["sku_image_url"])   
            )
        return final_dict
            
    def get_PIL_image(self,url):
        if url == "DEFAULT URL":
            self.bug("Received url of default value. Skipping download attempt.")
            return None
        try:        
            self.log("Trying PIL Image from {}...".format(url))
            raw_data = urllib.request.urlopen(url).read()
            self.log("urllib.request.urlopen(ABOVE URL).read() successfully called.")   
        except ValueError:
            self.bug("THIS IMAGE AT {} IS NOT WORKING!".format(url))
            return None
        except AttributeError:
            self.bug("CANNOT READ URLOPEN FOR ", url)
            return None
        else: 
            PILim = PIL.Image.open(io.BytesIO(raw_data)).resize((300, 300))
            TKim = PIL.ImageTk.PhotoImage(image=PILim)         
            return TKim   

class MultiGrapherEngine():
    def __init__(self):    
        self.log = logging.getLogger(__name__).info
        self.log("Init.")
        self.bug = logging.getLogger(__name__).debug  
        
        
    def convert_slot_pack_to_request_pack(self,slot_pack,custom_today):
            
        request_pack = {
            "aggregate_by":slot_pack["aggregate_by"],
            "start": (custom_today - datetime.timedelta(slot_pack["days_back"])),
            "end": custom_today,
            "extra": slot_pack["extra"],
            "left": {
                "gtype": slot_pack["left"]["gtype"],
                "metric": slot_pack["left"]["metric"],
                "queries": slot_pack["left"]["queries"],
                "set_y": slot_pack["left"]["set_y"]
                
            },
            "mirror_days": slot_pack["mirror_days"],
            "right": {
                "gtype": slot_pack["right"]["gtype"],
                "metric": slot_pack["right"]["metric"],
                "queries": slot_pack["right"]["queries"],
                "set_y": slot_pack["right"]["set_y"]
            },
            "x_axis_label": slot_pack["x_axis_label"],
            "title":slot_pack["title"]
        }
        return request_pack
       
    def convert_request_pack_to_slot_pack(self,request_pack,custom_today=None): 
        if request_pack["title"] == None:
            le = request_pack["left"]["queries"]
            ri = request_pack["right"]["queries"]
            if ri:
                if le:
                    newtitle = "{} vs {}".format(le[0][0],ri[0][0])
                else:
                    newtitle = ri[0][0]
            else:
                newtitle = le[0][0]

            self.log("New title {}".format(newtitle))
        else:
            newtitle = request_pack["title"] 
        slot_pack = {
            "aggregate_by":request_pack["aggregate_by"],
            "extra":request_pack["extra"],
            "x_axis_label": request_pack["x_axis_label"],
            "mirror_days":request_pack["mirror_days"],      
            "last_path":None,
            "left": {
                "gtype":request_pack["left"]["gtype"],
                "metric": request_pack["left"]["metric"],
                "queries": request_pack["left"]["queries"],
                "set_y": request_pack["left"]["set_y"]
            },
            "right": {
                "gtype":request_pack["right"]["gtype"],
                "metric": request_pack["right"]["metric"],
                "queries": request_pack["right"]["queries"],
                "set_y": request_pack["right"]["set_y"]
            }, 
            "custom_today":custom_today,
            "days_back":((request_pack["end"] - request_pack["start"]).days),
            "title": newtitle
        }                   
        return slot_pack        
        
class AnalysisPageEngine():
    def __init__(self):    
        self.log = logging.getLogger(__name__).info
        self.log("Init.")
        self.bug = logging.getLogger(__name__).debug   
        
    def get_results_packs(self,pack,dbvar,event_string):
        """
        selpack = {
         "aggregate_by":"day",
         "end": datetime.date(2018, 1, 28),
         "extra": "",
         "left": {"gtype": "line",
                  "metric": "Order Value (KRW)",
                  "queries": [("Average Order Value", "firebrick", "-")],
                  "set_y": [False, 0, 0]},
         "mirror_days": 0,
         "n_rankings":10,
         "right": {"gtype": None,
                   "metric": None,
                   "queries": [],
                   "set_y": [False, 0, 0]},
         "start": datetime.date(2018, 1, 14),
         "title": None,
         "x_axis_label": "Date"}
        """      
       
        start = pack["start"]       
        end = pack["end"]
        axes_select_packs = self._determine_left_right_axis(pack)
        axes_result_packs = [None,None]
        if bool(pack["mirror_days"]):
            m_start = (start - datetime.timedelta(pack["mirror_days"]))
            m_end = (end - datetime.timedelta(pack["mirror_days"]))
        
        event_list = []
        for index, event in enumerate(event_string.split("%%")):
            event_parts = event.split(",")
            start_date = event_parts[0]
            end_date = event_parts[1]
            name_str = event_parts[2]     
            event_list.append((start_date,end_date,name_str))

        for ind,axis in enumerate(axes_select_packs):
            if axis:
                ls_queries = []
                x_data = []
                y_data_lists = []
                colors_to_plot = []
                styles_to_plot = []
                
                for index,query_tuple in enumerate(axis["queries"]):
                    
                    first_found = True
                    if not query_tuple[0] == "None":

                        xandy = queries.main(query_tuple[0],dbvar,start,end,
                                             extra=pack["extra"], n_rankings=pack["n_rankings"] )
                        self.log("xandy type: {}".format(type(xandy)))
                        if xandy[0] == "MULTIPLE PLOTS":
                            colors = ["firebrick","dodgerblue","seagreen","darkorchid","gray","yellow","salmon","deeppink","coral",
                                      "firebrick","dodgerblue","seagreen","darkorchid","gray","yellow","salmon","deeppink","coral"]
                            if first_found:
                                x_data = xandy[1]
                                first_found = False                            
                            for index,single_plot_tuple in enumerate(xandy[2]):
                                ls_queries.append(single_plot_tuple[1])
                                colors_to_plot.append(colors[index])
                                styles_to_plot.append(query_tuple[2])                                
                                y_data_lists.append(single_plot_tuple[0])
                        else:
                            if xandy == "No Date Data":
                                self.bug("No Date Data given to default engine from queries")
                                return xandy
                            elif xandy is None:
                                self.bug("None given to default engine query.")
                                return None
                            else:
                                ls_queries.append(query_tuple[0])
                                colors_to_plot.append(query_tuple[1])
                                styles_to_plot.append(query_tuple[2])                                
                                queryx,queryy = xandy
                                if first_found:
                                    x_data = queryx
                                    first_found = False
                                y_data_lists.append(queryy)
                        
                        if bool(pack["mirror_days"]):
                            ls_queries.append("{}MR_{}-{}".format(query_tuple[0],m_start,m_end))
                            colors_to_plot.append(query_tuple[1])
                            styles_to_plot.append(query_tuple[2])
                            xandy = queries.main(query_tuple[0],dbvar,
                                                 m_start,m_end,extra=pack["extra"])
                            self.bug("xandy type: {}".format(type(xandy)))
                            if xandy == "No Date Data":
                                self.bug("No Date Data given to default engine from queries")
                                return xandy
                            elif xandy is None:
                                self.bug("None given to default engine query.")
                                return None
                            queryx,queryy = xandy
                            if first_found:
                                x_data = queryx
                                first_found = False
                            y_data_lists.append(queryy)                            
                         
                axis_pack  = {
                    "start":start,
                    "end":end,
                    "met": axis["metric"],
                    "gtype": axis["gtype"],
                    "set_y":axis["set_y"],
                    "str_x": pack["x_axis_label"],
                    "str_y": axis["metric"],
                    "line_labels":ls_queries,
                    "x_data": x_data,
                    "y_data": y_data_lists,
                    "colors":colors_to_plot,
                    "linestyles": styles_to_plot,
                    "title":pack["title"],
                    "event_dates": event_list
                    
                }
                axes_result_packs[ind] = axis_pack          
        return axes_result_packs             

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
        
        return sheetname,newdf 
    
    def _has_queries_req(self,queriespacklist):
        found_something = False
        for qpack in queriespacklist:
            if not qpack[0] == "None":
                found_something = True
        return found_something           
    
    def _determine_left_right_axis(self,pack):
        p_req = self._has_queries_req(pack["left"]["queries"])
        s_req = self._has_queries_req(pack["right"]["queries"])
        
        if p_req and s_req:
            return pack["left"],pack["right"]
        elif p_req and not s_req:
            return pack["left"],None
        elif not p_req and s_req:
            return pack["right"],None
        return None,None         
    
class QueryPanelEngine():
    def __init__(self):    
        self.log = logging.getLogger(__name__).info
        self.log("Init.")
        self.bug = logging.getLogger(__name__).debug   
    
    def get_queries_list(self,category,queries_ref):
        qlist = []
        if category:
            for k,v in queries_ref.items():
                if v["category"] == category:
                    qlist.append(k)    
        else:
            qlist = list(queries_ref.keys())
        qlist.sort()
        return qlist
    
    def get_start_and_end(self,setdates_gap,setdates_from_date):
        days_back = int(setdates_gap)
        from_what_day = setdates_from_date
        
        if from_what_day == "today":
            end_date = datetime.datetime.today().date()
        elif from_what_day == "yesterday":
            end_date = (datetime.datetime.today() - datetime.timedelta(1)).date()
        elif len(from_what_day) == 8:
            try:
                int(from_what_day)
            except ValueError:
                self.bug("from_what_day in ._auto_test is not a valid date string.")
                return
            year = int(from_what_day[0:4])
            month = int(from_what_day[4:6])
            day = int(from_what_day[6:8]) 
            end_date = datetime.date(year, month, day)
            start_date = end_date - datetime.timedelta(days_back)
        return start_date,end_date      
    
class DataTableEngine():
    def __init__(self):    
        self.log = logging.getLogger(__name__).info
        self.log("Init.")
        self.bug = logging.getLogger(__name__).debug   
        
        """
        cfg/mrp = {
            "start":start,
            "end":end,
            "title": title,
            "line_labels": labels,
            "data_list_of_lists": datas
        }      
        """

    def get_rows_of_data(self,data_list_of_lists):
        list_of_rows = []
        for row_c,data_pt in enumerate(data_list_of_lists[0]):
            row_values = []
            for index, data_list in enumerate(data_list_of_lists):
                val = data_list[row_c]
                if isinstance(val, float) or isinstance(val, np.float64):
                    val = round(val, 2)
                row_values.append(val)
            list_of_rows.append(row_values)
        return list_of_rows    

