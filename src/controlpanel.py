# -*- coding: utf-8 -*-
"""
Created on Thu May 31 14:25:28 2018
@author: Justin H Kim
"""

#Tkinter Modules
try:
    import Tkinter as tk
    import tkFont
    import ttk
except ImportError:  # Python 3
    import tkinter as tk
    import tkinter.ttk as ttk
from tkinter import filedialog

# Standard Modules
import datetime
import os
import sys

# Non-Standard Modules
import pandas as pd
from pprint import pprint
import numpy as np

# Project Modules
import querypanel
import master_calendar.calendardialog as cal_dialog
from default_engines import ControlPanelEngine

class ControlPanel(ttk.PanedWindow):
    def __init__(self,parent,controller=None,engine="default",config=None):
        super().__init__(parent)
        self.parent = parent
        if not controller:
            self.controller = parent
        else:
            self.controller = controller
            
        if str(engine) == "default":
            self.engine = ControlPanelEngine()
        else:
            self.engine = engine         
            
        self.config_key = "controlpanel_config"    
        if config:
            self.engine.set_build_config(raw_config = config[self.config_key])   
        
#       LOGIC VARIABLES
        self.check_valid = "DataInsightsApp_ControlPanel"
        self.start_date = None
        self.end_date = None   
        
        self.ls_query_panels = []
        self.prime_results_pack = None
        self.secondary_results_pack = None

#       UX VARIABLES
#        lock/unlock y-axis when skipping by week or month
        self.hold_y_var = tk.BooleanVar()
        self.hold_y_var.set(False)
        
        self.start_textvar = tk.StringVar()
        self.start_textvar.set("Pick Start Date")    
        
        self.end_textvar = tk.StringVar()
        self.end_textvar.set("Pick End Date")  
        
#        autosearch on query change
        self.autosearch = tk.BooleanVar()
        self.autosearch.set(False)        
                
#        BUILD
        self.b_input_pane()
        self.b_queries_pane(config),
        self.b_menu_pane()
        self.add(self.input_pane)
        self.add(self.query_pane)
        self.add(self.menu_pane)   
        
#       CONFIG
        if config:
            if self.engine.get_cfg_val("setdates_on_load"):
                self._set_dates(self.engine.get_set_date_config())

    def _set_dates(self,date_cfg_pack):
        self.start_date,self.end_date = self.engine.set_end_date(date_cfg_pack)
        self.start_textvar.set(str(self.start_date))
        self.end_textvar.set(str(self.end_date)) 
        
  # ===================================================================
#       API
# ===================================================================    
    def set_cfgvar(self,new_cfgvar):
        self.engine.set_build_config(raw_config = new_cfgvar[self.config_key])
        for qp in self.ls_query_panels:
            qp.set_cfgvar(new_cfgvar)
            
    def search_call(self):
        try:
            self.controller.search_queries
        except AttributeError:
            print("Not using valid controller")
            print(str(self.controller)," Not Suitable for .search_queries callback")       
        else:     
            selection_pack = self.gen_selection_pack()
            self.controller.search_queries(selection_pack)

    def export_excel_call(self):
        try:
            self.controller.export_excel
        except AttributeError:
            print("Not using valid controller")
            print(str(self.controller)," Not Suitable for .export_excel callback")       
        else:     
            self.controller.export_excel()        
        
    def export_graph_call(self):
        try:
            self.controller.export_png
        except AttributeError:
            print("Not using valid controller")
            print(str(self.controller)," Not Suitable for .export_png callback")       
        else:     
            self.controller.export_png()   
             
    def exclude_panels(self,need_exclude, st_solo_panel):
        """
        this is called from ap.update_query_checks.
        which gets called when the METRIC gets changed.
        metric is "changed" if the scope changes, or the metric menu is clicked,
        """
        for qp in self.ls_query_panels:
            if need_exclude:
                if not qp.panel_name == st_solo_panel:
                    qp.toggle_enabled(False)

            else:
                if not qp.panel_name == st_solo_panel:
                    qp.toggle_enabled(True)                 

#   Called by Querypanel query commands
    def check_autosearch(self):
        if self.autosearch.get():
            self.search_call()            
            
    def gen_selection_pack(self):
        """
        pack
        {"enabled":self.bl_enabled,
        "scope":scope,
         "extra":extra,
         "metric":metric,
         "queries_list":[("query_str","red"),("query_str2","blue")]}
        """
        start = self.start_date
        end = self.end_date
        prime_pack = self.ls_query_panels[0].get_selection_pack()
        secondary_pack = self.ls_query_panels[1].get_selection_pack()
        selection_pack = {"start":start,
                          "end":end,
                          "prime":prime_pack,
                          "secondary":secondary_pack,
                          "hold_y":self.hold_y_var
                          }
        return selection_pack
        
  # ===================================================================
#       UX EVENT HANDLERS AND HELPERS
# =================================================================== 
#   Note that days is positive or negative!
    def _skip_calendars(self, days):
        self.start_date = self.start_date + datetime.timedelta(days)
        self.end_date = self.end_date + datetime.timedelta(days)
        self.start_textvar.set(str(self.start_date))
        self.end_textvar.set(str(self.end_date))
        self.search_call()

    def _open_start_calendar(self):
        start_calendar = cal_dialog.CalendarDialog(
            self)
        self.start_date = start_calendar.result.date()
        self.start_textvar.set(str(self.start_date))

    def _open_end_calendar(self):
        end_calendar = cal_dialog.CalendarDialog(self)
        self.end_date = end_calendar.result.date()
        self.end_textvar.set(str(self.end_date))

    def _open_ref_calendar(self):
        ref_calendar = cal_dialog.CalendarDialog(self)
        self.extra_date = ref_calendar.result.date()
        self.extra_textvar.set(str(self.extra_date))

    def _sortby(self, tree, col, descending):
        """sort tree contents when a column header is clicked on"""
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
        
    def b_input_pane(self):
        self.input_pane = ttk.Labelframe(
            self, text="Input")

        self.back_one_month_button = ttk.Button(
            self.input_pane, command=lambda: self._skip_calendars(-30), text="<<",width=3)
        self.back_one_month_button.grid(
                row=0, column=0, padx=(5, 0), pady=2)
        self.back_one_week_button = ttk.Button(
            self.input_pane, command=lambda: self._skip_calendars(-7), text="<",width=3)
        self.back_one_week_button.grid(
                row=0, column=1, padx=5, pady=2)

        self.start_day_button = ttk.Button(self.input_pane,
                                          command=self._open_start_calendar,
                                          textvariable=self.start_textvar)
        self.start_day_button.grid(row=0, column=2, padx=5, pady=2)

        self.end_day_button = ttk.Button(self.input_pane,command=self._open_end_calendar,
            textvariable=self.end_textvar)
        self.end_day_button.grid(row=0, column=3, padx=5, pady=2)

        self.forward_one_week_button = ttk.Button(
            self.input_pane, command=lambda: self._skip_calendars(7), text=">",width=3)
        self.forward_one_week_button.grid(
                row=0, column=4, padx=5, pady=2)

        self.forward_one_month_button = ttk.Button(
            self.input_pane, command=lambda: self._skip_calendars(30), text=">>",width=3)
        self.forward_one_month_button.grid(
            row=0, column=5, padx=(0, 5), pady=2)

        self.hold_y_axis_button = ttk.Checkbutton(
            self.input_pane,
            text="Hold Y-Axis on Date Change?",
            variable=self.hold_y_var,
            onvalue=True,
            offvalue=False)
        
        self.hold_y_axis_button.grid(
            row=1,
            column=0,
            pady=2,
            padx=5,
            sticky="w",
            columnspan=5)

    def b_queries_pane(self,config=None):
        self.query_pane = tk.Frame(self)
        col = 0
        for query_panel_name in self.engine.get_cfg_val("axis_panel_names"):
            query_panel = querypanel.QueryPanel(
                self.query_pane,
                controller=self,
                engine="default",
                config = config,
                panel_name = query_panel_name)
            query_panel["text"] = query_panel_name
            self.ls_query_panels.append(query_panel)
            query_panel.grid(row=0, column=col, sticky="n")
            col += 1
            
    def b_menu_pane(self):
        self.menu_pane = ttk.Labelframe(
            self, text="Controls")

        self.should_search_on_query_change = ttk.Checkbutton(
            self.menu_pane,
            text="Auto-search on query change?",
            variable=self.autosearch,
            onvalue=True,
            offvalue=False)
        self.should_search_on_query_change.grid(
            row=0, column=0, pady=2, padx=5, sticky="w", columnspan=2)

        self.entry_input_button = ttk.Button(
            self.menu_pane,
            command=self.search_call,
            text="Search")
        self.entry_input_button.grid(
            row=1, column=0, padx=5, pady=2, sticky="w")

        self.export_excel_button = ttk.Button(
            self.menu_pane,
            command=self.export_excel_call,
            text="Export Data to Excel")
        self.export_excel_button.grid(
            row=1, column=1, padx=5, pady=2, sticky="w")
        
        self.export_graph_button = ttk.Button(
            self.menu_pane,
            command=self.export_graph_call,
            text="Export Graph",
            state="normal")
        self.export_graph_button.grid(
            row=1, column=2, padx=5, pady=2, sticky="w")        
        
if __name__ == "__main__":
    import config2
    controls_config = config2.backend_settings
    
    app = tk.Tk()
    controlpanel = ControlPanel(app,config=controls_config)
    controlpanel.grid(padx=20)
    app.mainloop()