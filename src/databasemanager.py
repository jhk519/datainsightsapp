 # -*- coding: utf-8 -*-
"""
Created on Thu Apr 26 17:12:28 2018

@author: Justin H Kim
"""
# Tkinter Modules
try:
    import Tkinter as tk
    import tkFont
    import ttk
except ImportError:  # Python 3
    import tkinter as tk
    import tkinter.ttk as ttk
from tkinter import filedialog

# Standard Modules
import pickle
import pandas as pd
import logging
import requests
import datetime
import sqlite3
from pprint import pprint as PRETTYPRINT
import os

# Project Modules
from appwidget import AppWidget

class DBManager(AppWidget):
    def __init__(self,parent,controller,config,dbvar=None):
#        PRETTYPRINT(config)
        self.widget_name = "dbmanager"
        super().__init__(parent,controller,config,dbvar)     
        self.engine = DBManagerEngine()
 
#       WIDGET SPECIFIC        
#        PRETTYPRINT(self.get_cfg_val("dbs_cfg"))
        self.set_dbvar(self.engine.gen_bare_dbvar(self.get_cfg_val("dbs_cfg")))
        
        self.online_loaded = tk.IntVar(value=0)
        self.db_status_labels = []
        
        self.dbs_overview_frame = tk.LabelFrame(self,text="Overview")
        self.dbs_overview_frame.grid(row=0,column=0,sticky="nw")
        
        self.dbs_controls_frame = tk.LabelFrame(self,text="Misc. Controls")
        self.dbs_controls_frame.grid(row=0,column=1,sticky="nw",padx=(15,15))
        
        self.build_dbs_overview_frame(self.dbs_overview_frame)
        self.build_dbs_controls_frame(self.dbs_controls_frame)
        
        if self.get_cfg_val("loaddb_on_load"):
            self.load_offline_dbs(file_loc=self.get_cfg_val("loaddb_loc"))        
        
# ================================================================
# ================================================================
#       UX API
# ================================================================
# ================================================================  

    def ux_regenerate(self,db_str):
        self.log("Starting Regenerate DB: {}".format(db_str))
        pathstr_tuple = tuple(filedialog.askopenfilenames())
        self.log("Paths: {}".format(",\n".join(pathstr_tuple)))
        
        if len(pathstr_tuple) == 0:
            self.bug("User selected no paths for regen. Aborting.")
            return
        
        db_cfg = self.get_cfg_val("dbs_cfg")[db_str]
        
        for index, path in enumerate(pathstr_tuple):
            if index == 0:
                new_df = self.engine.gen_dataframe_from_excel(path, db_cfg)
            else:
                add_row_df = self.engine.gen_dataframe_from_excel(path, db_cfg)   
                new_df = self.engine.add_rows_to_dataframe_from_excel(new_df,add_row_df,db_cfg["match_on_key"])
                
            if type(new_df) is str:
                self.bug(new_df)
                self.create_popup("DB Generation Error","For excel @ {},\n {}".format(path,new_df))           
            
        if db_str == "odb":
            self.log("Merging odb with pdb.")
            new_df_merged = self.engine.merge_odb_with_pdb(
                    odb = new_df,
                    pdb = self.get_dbvar()["pdb"])

            self.get_dbvar()[db_str] = self.engine.get_and_add_order_counts(new_df_merged)
            
        else:
           self.get_dbvar()[db_str] = new_df 

        self.log("Completed resetting and generating: {}".format(db_str))  
        self._update_statuses()
        
    def ux_add_rows(self,db_str):
        self.log("Starting Add Rows To DB: {}".format(db_str))
        pathstr_tuple = tuple(filedialog.askopenfilenames())
        self.log("Paths: {}".format(",\n".join(pathstr_tuple)))
        
        db_cfg = self.get_cfg_val("dbs_cfg")[db_str]
        
        for index, path in enumerate(pathstr_tuple):
            add_row_df = self.engine.gen_dataframe_from_excel(path, db_cfg)   
            
            if db_str == "odb":
                add_row_df_merged = self.engine.merge_odb_with_pdb(
                        odb = add_row_df,
                        pdb = self.get_dbvar()["pdb"])
            return_df = self.engine.add_rows_to_dataframe_from_excel(
                    self.get_dbvar()[db_str],
                    add_row_df_merged,
                    db_cfg["match_on_key"])
            
            if type(return_df) is str:
                self.bug(return_df)
                self.create_popup("DB Generation Error" , "For excel @ {},\n {}".format(path,return_df))   
                return 
            else:
                self.get_dbvar()[db_str] = return_df
         
        if db_str == "odb":   
            self.get_dbvar()[db_str] = self.engine.get_and_add_order_counts(self.get_dbvar()[db_str])   
                
        self.log("Completed Adding Rows: {}".format(db_str))             
        self._update_statuses()
        
    def ux_update_columns(self,db_str):
        self.log("Starting Update Columns To DB: {}".format(db_str))
        pathstr_tuple = tuple(filedialog.askopenfilenames())
        self.log("Paths: {}".format(",\n".join(pathstr_tuple)))  
        
        db_cfg = self.get_cfg_val("dbs_cfg")[db_str]
        for index, path in enumerate(pathstr_tuple):
            return_df = self.engine.update_columns(self.get_dbvar()[db_str],path,db_cfg)
            if type(return_df) is str:
                self.bug(return_df)
                self.create_popup("DB Update Columns Error" , "For excel @ {},\n {}".format(path,return_df))   
                return             
            else: self.get_dbvar()[db_str] = return_df
        self.log("Completed Updating Columns: {}".format(db_str))  
        self._update_statuses()
        
    def ux_export_db_excel(self,db_str):
        self.log("Export DB Excel for {}".format(db_str))
        if self.get_cfg_val("automatic db export"):
            fullname = self.get_export_full_name(db_str)
            self.log(".export_db_csb auto-fullname: {}".format(fullname))
        else:
            dir_loc = filedialog.asksaveasfilename() 
            fullname = dir_loc + ".xlsx"
            self.bug("_export_db_csv manual fullname: {}".format(fullname))
        self.get_dbvar()[db_str].to_excel(fullname)
        
#        os.system('start excel.exe "%s"' % (fullname))
        self.log("End Excel Conversion")
        self._update_statuses()
        
    def ux_export_db_sqlite(self,db_str):
        self.log("Starting Export DB Sqlite: {}".format(db_str))
        if self.get_cfg_val("automatic db export"):
            fullname = self.get_export_full_name(db_str,ftype="sqlite")
        else:
            dir_loc = filedialog.asksaveasfilename()
            fullname = dir_loc + ".db"
        self.engine.df2sqlite(self.get_dbvar()[db_str], fullname)
        self.log("Export Sqlite Completed.")         
        self._update_statuses()
        
    def ux_load_dbs(self):
        title = "Load from Online or from Computer?"
        text = "Please Choose to Load DB from Online or Offline."
        onlineb = ("Online",self.load_online_dbs)
        offlineb = ("Offline",self.load_offline_dbs)   
        self.create_popup(title,text,firstb=onlineb,secondb=offlineb)  
        
    def ux_save_dbs(self):
        with open('databases//DH_DBS.pickle', 'wb') as dbfile:
            pickle.dump(self.get_dbvar(), dbfile)           
        self.save_dbs_status.set("Saved DBs at " + self.get_time_str())
        self._update_statuses()
        
# ================================================================
# ================================================================
#       FUNCTIONS
# ================================================================
# ================================================================     
    def load_online_dbs(self):
        print("Cant load online dbs, dummy!")
        
    def load_offline_dbs(self,file_loc=None):
        try:
            self.popup.destroy()
        except AttributeError:
            self.bug("Cannot find popup widget to .destroy()")
            
        if file_loc: dir_loc = file_loc
        else: dir_loc = filedialog.askopenfilename()
            
        with open(dir_loc, "rb") as dbfile:
            try:
                self.set_dbvar(pickle.load(dbfile))
            except:
                print("Likely in-compatible DB file.")

        self.load_dbs_status.set("Loaded at DBs at {}".format(self.get_time_str()))
        self._update_statuses()
        self.log("Loaded DBs.")        
        
# ================================================================
# ================================================================
#       BUILD FUNCTIONS
# ================================================================
# ================================================================          
        
    def build_dbs_overview_frame(self,targ_frame):
        rown = 0
        
        ttk.Label(targ_frame, text="Name").grid(row=rown, column=0)
        ttk.Label(targ_frame, text="Info").grid(row=rown, column=1)
        ttk.Label(targ_frame, text="Update").grid(row=rown, column=2,columnspan=3)       
        ttk.Label(targ_frame, text="Export").grid(row=rown, column=5,columnspan=2)
        rown += 1
        
        for db_str,db_cfg in self.get_cfg_val("dbs_cfg").items():
            coln = 0
            ttk.Label(targ_frame, text=db_cfg["proper_title"]).grid(
                row=rown, column=0, sticky="w",padx=(10,10),pady=10)
            coln += 1
            
            status_var = tk.StringVar()
            status_var.set("Default Status for {}".format(db_str))
            tk.Label(targ_frame,textvariable=status_var).grid(
                    row=rown,column=coln,padx=(10,10))
            coln += 1
            
            regen_cmd = lambda db_str=db_str: self.ux_regenerate(db_str)
            ttk.Button(targ_frame,command=regen_cmd,text="Regenerate").grid(
                    row=rown, column=coln,padx=(5,5))
            coln += 1
            
            add_rows_cmd = lambda db_str=db_str: self.ux_add_rows(db_str)
            ttk.Button(targ_frame,command=add_rows_cmd,text="Add Rows").grid(
                    row=rown, column=coln,padx=(5,5)) 
            coln += 1
            
            update_columns_cmd = lambda db_str=db_str: self.ux_update_columns(db_str)
            ttk.Button(targ_frame,command=update_columns_cmd,text="Update Columns").grid(
                    row=rown, column=coln,padx=(5,5))     
            coln += 1
            
            excel_cmd = lambda db_str=db_str: self.ux_export_db_excel(db_str)
            ttk.Button(targ_frame,command=excel_cmd,text="Excel").grid(
                    row=rown, column=coln,padx=(5,5))
            coln += 1
            
            sql_cmd = lambda db_str=db_str: self.ux_export_db_sqlite(db_str)
            ttk.Button(targ_frame,command=sql_cmd, text="SQLite").grid(
                    row=rown, column=coln,padx=(5,5))
            coln += 1
            
            self.db_status_labels.append([db_str,status_var])
            rown += 1
        
    def build_dbs_controls_frame(self,targ_frame):
        rown = 0      
        
        # LOAD DBS
        ttk.Button(targ_frame, command=self.ux_load_dbs,text="Load Databases").grid(
                row=rown, column=0,sticky="w", padx=(10,10))
        self.load_dbs_status = tk.StringVar()
        self.load_dbs_status.set("Load DBs Default Status")
        ttk.Label(targ_frame, textvariable=self.load_dbs_status).grid(
                row=rown, column=1, sticky="e",pady=10)
        rown += 1

        # SAVE DBS
        ttk.Button(targ_frame, command=self.ux_save_dbs,text="Save Databases").grid(
                row=rown, column=0, sticky="w", padx=(10,10))
        self.save_dbs_status = tk.StringVar()
        self.save_dbs_status.set("Save DBs Default Status")
        ttk.Label(targ_frame, textvariable=self.save_dbs_status).grid(
                row=rown, column=1, sticky="e",padx=(0,10),pady=10)     
        rown += 1
        
    def _update_statuses(self):

        for status_tuple in self.db_status_labels:
            db_str = status_tuple[0]
            status_var = status_tuple[1]

            try:
                specific_db = self.get_dbvar()[db_str]
            except KeyError:
                status_var.set("Database is Missing!")
                continue
            
            if not str(type(specific_db)) == "<class 'pandas.core.frame.DataFrame'>":
                status_var.set("Data is Not Dataframe Type, it is:{}".format(type(specific_db)))
                continue
            
            if specific_db.shape[0] < 10:
                status_var.set("Too little data (<10 rows)")
                continue
            
            status_var.set("Passed initial check... Checking dataset.")
            
            rows = str(specific_db.shape[0] - 1)
            cols = str(specific_db.shape[1])
            status_line = "Has {} rows, and {} columns".format(rows,cols)
            
            no_dates_dbs = {"pdb"}
            if not db_str in no_dates_dbs:
                firstd = None
                lastd = None
                targ = "date"
                specific_db.sort_values(targ, inplace=True)
                firstd = str(specific_db[targ].iloc[1])[0:10]
                lastd = str(specific_db[targ].iloc[-1])[0:10]
                status_line = "{}\n{} to {}".format(status_line,firstd,lastd)      

            status_var.set(status_line)
        try:
            self.controller.propagate_db_var_change 
        except AttributeError:
            self.bug("No controller to propagate_db_var_change.")
        else:
            self.controller.propagate_db_var_change(self.get_dbvar())           
          
class DBManagerEngine():
    def __init__(self):    
        self.log = logging.getLogger(__name__).info
        self.log("Init.")
        self.bug = logging.getLogger(__name__).debug  
        
    def gen_bare_dbvar(self,cfg):
        return { key: None for key in cfg}
    
    def get_translated_and_dropped_df(self,init_df,header_ref):
        init_df.rename(
            columns=lambda x: x.strip().replace(" ", "").replace("\n", ""), inplace=True)
        for header in list(init_df):
            if header not in header_ref and header not in header_ref.values():
                init_df = init_df.drop(labels=header, axis=1)
            else:
                continue
        init_df.rename(columns=header_ref, inplace=True)
        
        return init_df
    
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
        
    def gen_dataframe_from_excel(self,excel_path,db_cfg):       
        self.log("Converting Excel at: {}".format(excel_path))
        if os.path.isfile(excel_path):    
            header_ref = db_cfg["header_translations"]
            
            init_df = pd.read_excel(excel_path, 0)
            init_df = self.get_translated_and_dropped_df(init_df,header_ref)
            
            req_headers_set = set(sorted(db_cfg["header_translations"].values()))
            current_headers = set(sorted(list(init_df.columns)))

            
            if req_headers_set.issubset(init_df.columns):
                self.log("all required headers are present, continuuing")
            else:
                missing_columns = req_headers_set - current_headers
                missing_spaced = "\n".join(missing_columns)                
                self.bug("missing columns: \n{}".format(missing_spaced))
                return "Missing Headers: {}".format(missing_columns)
        else: 
            self.bug("NO EXCEL EXISTS AT ".format(excel_path))
            return "NO EXCEL EXISTS AT ".format(excel_path)
        return self.sanitize_df(init_df)     
    

    def add_rows_to_dataframe_from_excel(self,curr_df,append_df,drop_on):
        new_df = pd.concat([curr_df, append_df], axis=0, ignore_index = True,
                           join = "outer").drop_duplicates(subset=drop_on,sort=False)
        return self.sanitize_df(new_df)    

    def update_columns(self,orig_odb, excel_path, db_cfg):
        if os.path.isfile(excel_path):    
            header_ref = db_cfg["header_translations"]
            req_header = db_cfg["match_on_key"]
            
            update_excel = pd.read_excel(excel_path, 0)
            update_excel = self.get_translated_and_dropped_df(update_excel,header_ref)
            
            current_headers = set(sorted(list(update_excel.columns)))
            
            if req_header in current_headers:
                self.log("All headers in update_columns excel are one or more of the req headers, including order_part_id")
            else:
                self.bug("Current headers has extra columns or missing order_part_id")
                return "Update Excel has incompatible columns OR is missing 'order_part_id' column."
        else: 
            self.bug("NO EXCEL EXISTS AT ".format(excel_path))
            return "NO EXCEL EXISTS AT ".format(excel_path)
        
        update_excel =  self.sanitize_df(update_excel)  
        orig_odb.update(update_excel,join="left",overwrite=True)
        
        return orig_odb

    def sanitize_df(self,df):
        self.log("Sanitizing...")
        temp = df.copy(deep=True)
        temp = temp.fillna(0) 
        for column_name in temp.columns:
            if "date" in column_name:
                temp[column_name] = temp[column_name].apply(lambda x: self.convert_to_date(x))
                   
        return temp        
    
    def convert_to_date(self,data_point, debugdb = ""):
        if type(data_point) == datetime.datetime or type(data_point) == pd._libs.tslib.Timestamp:
            return_val = data_point.date()
            if str(return_val) == "1970-01-01":
                return_val = 0        
        else:
            return_val = data_point
        return return_val    

    def merge_odb_with_pdb(self,odb,pdb):
        self.log("Merging odb with pdb...")
        return pd.merge(odb, pdb.drop_duplicates(subset="product_cafe24_code"), on="product_cafe24_code", right_index=False,
                       how='left', sort=False)  
        
    def get_and_add_order_counts(self,odb):
        self.log("Generating order_counts.")
        try:
            odb = odb.drop(labels="order_count", axis=1)
        except KeyError:
            self.bug("Cannot drop order_count, it's ok if this was a regen.")
        
        # Get only order_ids
        uniques = odb.drop_duplicates(subset="order_id",inplace=False)  
        # Eliminate fully cancelled orders
        no_cancels = uniques.loc[uniques["cancel_status"] !="취소"]
        # Group by phone number, and count up
        groupby_count = no_cancels.groupby("customer_phone_number").cumcount() + 1
        # Append counts back to uniques (via index)
        uniques["order_count"] = groupby_count
        
        # Merge back into original order db
        merged = pd.merge(odb, uniques[["order_id","order_count"]], 
                          right_index=False, on="order_id", how='left', sort=False)  

        return merged            
        
"""                
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

"""
        
if __name__ == "__main__":
    logname = "debug-{}.log".format(datetime.datetime.now().strftime("%y%m%d"))
    ver = "v0.2.10.7 - 2018/07/22"
    
    logging.basicConfig(filename=r"debug\\{}".format(logname),
        level=logging.DEBUG, 
        format="%(asctime)s %(filename)s:%(lineno)s - %(funcName)s() %(levelname)s || %(message)s",
        datefmt='%H:%M:%S')
    logging.info("-------------------------------------------------------------")
    logging.info("DEBUGLOG @ {}".format(datetime.datetime.now().strftime("%y%m%d-%H%M")))
    logging.info("VERSION: {}".format(ver))
    logging.info("AUTHOR:{}".format("Justin H Kim"))
    logging.info("-------------------------------------------------------------")
    
    import config2
    dbcfg = config2.backend_settings
    app = tk.Tk()
    test_widget = DBManager(app,app,dbcfg)
    test_widget.grid(padx=20)
    app.mainloop()                