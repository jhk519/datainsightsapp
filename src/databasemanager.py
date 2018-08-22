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
import logging

# Project Modules
from default_engines import DBManagerEngine

class DBManager(tk.Frame):
    def __init__(self,parent,controller=None,engine="default",config=None):
        super().__init__(parent)
        self.parent = parent
        if not controller:
            self.controller = parent
        else:
            self.controller = controller
            
        self.log = logging.getLogger(__name__).info
        self.log("{} Init.".format(__name__))    
        self.bug = logging.getLogger(__name__).debug             
            
        if str(engine) == "default":
            self.engine = DBManagerEngine()
        else:
            self.engine = engine    
            
        self.config_key = "dbmanager_config"    
        if config:
            self.engine.set_build_config(raw_config = config[self.config_key])
                        
        self.time_created = self.engine.time_str()
        self.online_loaded = tk.IntVar(value=0)
        
        self.db_panel_packs = []
        self._build_top_frame()
        self._build_middle_frame()
        self._build_bottom_frame()

        if self.engine.get_cfg_val("loaddb_on_load"):
            self._load_offline_dbs(file_loc=self.engine.get_cfg_val("loaddb_loc"))
 
#   API       
    def get_dbvar(self):
        return self.engine.get_dbvar()
    
    def set_cfgvar(self,new_cfgvar):
        self.engine.set_build_config(raw_config = new_cfgvar[self.config_key])
        
#   UX EVENT HANDLERS AND HELPERS   
    def _reset_and_gen_all_new_dbs(self):
        self.log("Resetting All DBs.")
        dir_loc = filedialog.askdirectory()
        self.engine.reset_and_gen_all_dbs(dir_loc)
        self.gen_db_status_value["text"] = "Generated new DBs at " + self.engine.time_str()
        self._update_statuses()
        self.controller.propagate_db_var_change(self.get_dbvar())
        self.log("Completed Generated New Dbs")
        
    def _reset_and_gen(self,db_str,dir_list = None):
        self.bug(".reset_and_gen for {} called. dir_list given: {}".format(db_str,dir_list))
        if not dir_list:
#          returns tuple of strings
            pathstr_tuple = filedialog.askopenfilenames()
            dir_list = list(pathstr_tuple)
            self.bug(".reset_and_gen called. Filedialog returns: {}".format(dir_list))
        self.engine.reset_and_gen_single_db(db_str, dir_list=dir_list)
        self._update_statuses()
        self.log("Completed resetting and generating: ".format(db_str))

    def _add_data_to_all_dbs(self):
        self.log("Adding Data to All DBs.")
        dir_loc = filedialog.askdirectory()
        self.engine.update_data_all_dbs(dir_loc)
        self.add_db_status_value["text"] = "Add new DBs at " + self.engine.time_str()
        self._update_statuses()        
        self.log("Completed Adding Data to All Dbs")      

    def _add_data(self, db_str, dir_list=None):
        self.bug("Add data to {}, dir_list given: {}".format(db_str,dir_list))
        if not dir_list:
            pathstr_tuple = filedialog.askopenfilenames()
            dir_list = list(pathstr_tuple)
            self.bug("Filedialog returns: {}".format(dir_list))
        self.engine.update_single_db(db_str,dir_list)
        self._update_statuses()
        self.log("Completed adding to: {}".format(db_str))

    def _pick_online_offline(self):
        self.popup = tk.Toplevel()
        self.popup.title("Load from Online or from Computer?")
        msg = tk.Message(
            self.popup,
            text="Please Choose to Load DB from Online or Offline.")
        msg.pack()
        online_button = ttk.Button(
            self.popup,
            text="Online",
            command=self._load_online_dbs)
#        online_button["state"] = "disabled"
        offline_button = ttk.Button(
            self.popup,
            text="Offline",
            command=self._load_offline_dbs)
        online_button.pack()
        offline_button.pack()

    def _load_online_dbs(self):
        self.popup.destroy()
        self.online_loaded.set(0)
        self.load_db_status_value = ttk.Progressbar(self.bottom_frame,maximum=14,
                                                    mode="determinate",variable=self.online_loaded)
        self.load_db_status_value.grid(row=2, column=1, sticky="e", padx=15)
        
        self.engine.load_online_dbs(counter=self.online_loaded,ticker=self.load_db_status_value)        
        self._update_statuses()
        self.log("Loaded DBs.")

    def _load_offline_dbs(self,file_loc=None):
        try:
            self.popup.destroy()
        except AttributeError:
            self.bug("Cannot find popup widget to .destroy()")
        if file_loc:
            dir_loc = file_loc
        else:
            dir_loc = filedialog.askopenfilename()
        self.engine.load_offline_dbs(dir_loc)

        self.load_db_status_value["text"] = "Loaded at DBs at " + self.engine.time_str()
        self._update_statuses()
        self.log("Loaded DBs.")

    def _save_dbs(self, save_type):
        self.engine.save_all_dbs(save_type)
        self.save_db_status_value["text"] = "Saved DBs at " + self.engine.time_str()
        self._update_statuses()

    def _export_db_csv(self, db_str):
        self.log("Export DB CSV for {}".format(db_str))
        if self.engine.get_cfg_val("automatic db export"):
            fullname = self.engine.get_export_full_name(db_str)
            self.bug(".export_db_csb auto-fullname: {}".format(fullname))
        else:
            self.bug("No automatic db export given, asking dialog.")
            dir_loc = filedialog.asksaveasfilename() 
            fullname = dir_loc + ".xlsx"
            self.bug("_export_db_csv manual fullname: {}".format(fullname))
        self.log("Start Excel conversion")
        self.engine.get_dbvar()[db_str].to_excel(fullname)
        self.log("End Excel Conversion")

    def _export_db_sqlite(self, db_str):
        self.log("Export DB to SQlite")
        if self.engine.get_cfg_val("automatic db export"):
            fullname = self.engine.get_export_full_name(db_str,ftype="sqlite")
        else:
            dir_loc = filedialog.asksaveasfilename()
            fullname = dir_loc + ".db"
        self.engine.df2sqlite(db_str, fullname)
        self.log(".export_db_sqlite resolved.")

    def _update_statuses(self):
        try:
            created = self.time_created
            self.datahub_status_value["text"] = str(created)
        except BaseException:
            self.datahub_status_value["text"] = "No Datahub Found!"

        for db_pack in self.db_panel_packs:
            # (curr_db, db_title,db_status,db_export_csv,db_export_sqlite)
            try:
                specific_db = self.engine.get_dbvar()[db_pack[0]]
            except KeyError:
                db_pack[1]["text"] = "Database is Missing!"
                db_pack[1]["fg"] = "red"
                continue
            if not str(type(specific_db)) == "<class 'pandas.core.frame.DataFrame'>":
                db_pack[1]["text"] = "Data is Not Dataframe Type\n" + \
                    str(type(specific_db))
                db_pack[1]["fg"] = "red"
                continue
            if specific_db.shape[0] < 10:
                db_pack[1]["text"] = "Too little data (<10 rows)"
                db_pack[1]["fg"] = "red"
                continue
            db_pack[1]["text"] = "Passed initial check... Checking dataset."
            db_pack[1]["fg"] = "orange"

            no_sort_dbs = {"pdb", "sm_odb", "sm_stdb","cdb"}
            line2 = ""
            if not db_pack[0] in no_sort_dbs:
                firstd = None
                lastd = None
                targ = "date"
                specific_db.sort_values(targ, inplace=True)
                firstd = str(specific_db[targ].iloc[1])[0:10]
                lastd = str(specific_db[targ].iloc[-1])[0:10]
                line2 = "\n" + firstd + " to " + lastd
            items = str(specific_db.shape[0] - 1)
            cols = str(specific_db.shape[1])
            line1 = "Has " + items + " rows, and " + cols + " columns"

            db_pack[1]["text"] = line1 + line2
            db_pack[1]["fg"] = "green"

#   BUILD FUNCTIONS
    def _build_top_frame(self):
        self.top_frame = ttk.LabelFrame(self, text="General")
        self.top_frame.grid(row=0, column=0, sticky="wne",columnspan=2)

        self.datahub_status_title = ttk.Label(self.top_frame, text="Datahub Init. Time")
        self.datahub_status_title.grid(row=1, column=0, sticky="w", padx=15)

        self.datahub_status_value = tk.Label(self.top_frame, text="NA")
        self.datahub_status_value.grid(row=1, column=1, sticky="e", padx=15)

    def _build_middle_frame(self):
        self.middle_frame = ttk.LabelFrame(self, text="Databases")
        self.middle_frame.grid(row=1, column=0, sticky="we")

#        HEADERS
        row_c = 0
        self.database_name_header = ttk.Label(
            self.middle_frame, text="Name")
        self.database_name_header.grid(row=row_c, column=0)

        self.status_header = ttk.Label(
            self.middle_frame, text="Status Info")
        self.status_header.grid(
            row=row_c, column=1)

        self.status_header = ttk.Label(
            self.middle_frame, text="Export Options")
        self.status_header.grid(
            row=row_c, column=2, columnspan=2)

        for db_str,curr_db in self.engine.get_cfg_val("db_build_config").items():
            row_c += 1
            ttk.Label(self.middle_frame, text=curr_db["proper_title"]).grid(row=row_c, column=0, sticky="w", padx=15,pady=(5,20))

            db_status = tk.Label(self.middle_frame, text="Default")
            db_status.grid(row=row_c, column=1, sticky="e", padx=15)

            db_export_csv = ttk.Button(self.middle_frame,
                                       command=lambda db_str=db_str: self._export_db_csv(
                                           db_str),
                                       text="CSV")
            db_export_csv.grid(row=row_c, column=2, padx=8, pady=5)

            db_export_sqlite = ttk.Button(
                self.middle_frame,
                command=lambda db_str=db_str: self._export_db_sqlite(db_str),
                text="SQLite")
            db_export_sqlite.grid(row=row_c, column=3, padx=8)

            db_reset_and_gen = ttk.Button(self.middle_frame,
                                          command=lambda db_str=db_str: self._reset_and_gen(
                                              db_str),
                                          text="Regenerate")
            db_reset_and_gen.grid(row=row_c, column=4, padx=8)

            db_append = ttk.Button(self.middle_frame,
                                   command=lambda db_str=db_str: self._add_data(
                                       db_str),
                                   text="Append")
            db_append.grid(row=row_c, column=5, padx=8)

            db_pack = (db_str, db_status)
            self.db_panel_packs.append(db_pack)

    def _build_bottom_frame(self):
        
        self.bottom_frame = ttk.LabelFrame(self, text="Actions", height=200)
        self.bottom_frame.grid(row=1, column=1, sticky="nwes")

        self.upload_new_button = ttk.Button(
            self.bottom_frame,
            command=self._reset_and_gen_all_new_dbs,
            text="Reset and Gen New Databases from Excels")
        self.upload_new_button.grid(
            row=0, column=0, padx=15, pady=(25,5), sticky="w")

        self.add_data_to_all_dbs_button = ttk.Button(
            self.bottom_frame,
            command=self._add_data_to_all_dbs,
            text="Add Data to All DBs from Excels")
        self.add_data_to_all_dbs_button.grid(
            row=1, column=0, padx=15, pady=5, sticky="w")

        self.load_db_button = ttk.Button(self.bottom_frame,
                                         command=self._pick_online_offline,
                                         text="Load Databases")
        self.load_db_button.grid(row=2, column=0, padx=15, pady=5, sticky="w")

        self.save_db_as_df_button = ttk.Button(self.bottom_frame,
                                               command=lambda: self._save_dbs(
                                                   "pickled_dataframe"),
                                               text="Save Databases")
        self.save_db_as_df_button.grid(
            row=3, column=0, padx=15, pady=5, sticky="w")

        self.gen_db_status_value = ttk.Label(self.bottom_frame, text=" - ")
        self.gen_db_status_value.grid(row=0, column=1, sticky="e", padx=15)

        self.add_db_status_value = ttk.Label(self.bottom_frame, text=" - ")
        self.add_db_status_value.grid(row=1, column=1, sticky="e", padx=15)

        self.load_db_status_value = ttk.Label(self.bottom_frame, text=" - ")
        self.load_db_status_value.grid(row=2, column=1, sticky="e", padx=15)

        self.save_db_status_value = ttk.Label(self.bottom_frame, text=" - ")
        self.save_db_status_value.grid(row=3, column=1, sticky="e", padx=15)
    
if __name__ == "__main__":
    import config2
    dbcfg = config2.backend_settings
    app = tk.Tk()
    test_widget = DBManager(app, config=dbcfg)
    test_widget.grid(padx=20)
    app.mainloop()        
    
