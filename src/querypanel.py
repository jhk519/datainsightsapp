# -*- coding: utf-8 -*-
"""
Created on Thu Sep 27 13:42:49 2018

@author: Justin H Kim
"""

try:
    import Tkinter as tk
    import tkFont
    import ttk
except ImportError:  # Python 3
    import tkinter.colorchooser as colorchooser
    import tkinter as tk
    import tkinter.font as tkFont
    import tkinter.ttk as ttk
    
# Standard Modules
import datetime
import logging
import pickle
from pprint import pprint as PRETTYPRINT
    
# Project Modules
from appwidget import AppWidget
import master_calendar.calendardialog as cal_dialog

class QueryPanel(AppWidget):
    def __init__(self,parent,controller,config,dbvar=None):
        self.widget_name = "newquerypanel"
        super().__init__(parent,controller,config,dbvar) 
        
        # QUERY MENU
        self.current_category_var = tk.StringVar()
        self.current_x_axis_type = tk.StringVar()
        self.categories_list = []
        
        # DATA FILTERS
        self.start_datetime = datetime.date(2018, 5, 1)
        self.end_datetime = datetime.date(2018, 5, 15)
        
        self.start_date_button_var = tk.StringVar()
        self.start_date_button_var.set(str(self.start_datetime))
        
        self.end_date_button_var = tk.StringVar()
        self.end_date_button_var.set(str(self.end_datetime))
        
        self.current_product_var = tk.StringVar()
        self.current_product_var.set("category")
        self.current_product_entry_var = tk.StringVar()
        
        self.current_platform_var = tk.StringVar()
        
        # METRICS
        self.metrics_list = []
        self.current_metric_var = tk.StringVar()
        self.current_metric_type_var = tk.StringVar()
        self.current_metric_data_type_var = tk.StringVar()
        self.current_metric_breakdown_var = tk.StringVar()
        
        # RESULTS
        self.current_aggregation_time_var = tk.StringVar()
        self.current_aggregation_type_var = tk.StringVar()
        
        self.current_n_rankings_var = tk.IntVar()
        self.current_n_rankings_var.set(5)
        
        self.current_compare_to_days_var = tk.StringVar()
        self.current_compare_to_days_var.set(0)
        
        # GRAPH
        self.current_linestyle_var = tk.StringVar() 
        self.color_button_widget = None
        self.current_custom_name_entry_var = tk.StringVar()
        
        # BUILD 
        self.build_skeleton()
        self.build_category_menu()
        self._ux_category_changed()
        self.build_results_options_menu(self.results_options_labelframe)
        self.build_graph_options_menu(self.graph_options_labelframe)
        self.build_send_to_axis_menu(self.send_to_axis_buttons_labelframe)
        
    # UX EVENTS
    
    def _ux_category_changed(self,event=None):
        current_category =  self.current_category_var.get().replace(" ","_").lower()            
        self.log("Category changed to: {}".format(current_category))
        
        self.reset_vars()
        
        self.current_x_axis_type.set(self.get_cfg_val("queries")[current_category]["x_axis_type"])
        
        required_data_filters_list = self.get_cfg_val("queries")[current_category]["data_filters"]
        self.build_data_filters(self.data_filters_labelframe, required_data_filters_list)
        
        required_metrics_dict = self.get_cfg_val("queries")[current_category]["metrics"]
        self.build_metric_options(self.metric_options_labelframe,required_metrics_dict)
        
    def _ux_open_start_cal(self):
        self.log("Getting new start date")
        start_calendar = cal_dialog.CalendarDialog(self, year=self.start_datetime.year, 
                                                   month=self.start_datetime.month)
        try:
            self.start_datetime = start_calendar.result.date()
        except AttributeError:
            self.log("Start date probably set to None.")
        else:
            self.start_date_button_var.set(str(self.start_datetime))     

    def _ux_open_end_cal(self):
        self.log("Getting new end date")
        end_calendar = cal_dialog.CalendarDialog(self,year=self.end_datetime.year, 
                                                 month=self.end_datetime.month)
        try:
            self.end_datetime = end_calendar.result.date()
        except AttributeError:
            self.log("end_date probably set to None")
            return
        else:
            self.end_date_button_var.set(str(self.end_datetime)) 
            
    def _ux_skip_calendars(self, days):
        self.start_datetime += datetime.timedelta(days)
        self.end_datetime += datetime.timedelta(days)
        self.start_date_button_var.set(str(self.start_datetime))
        self.end_date_button_var.set(str(self.end_datetime))  
        
    def _ux_metric_changed(self,event=None):
        current_category =  self.current_category_var.get().replace(" ","_").lower() 
        current_metric = self.current_metric_var.get().replace(" ","_").lower()
        self.log("Current metric: {}".format(current_metric))
        required_metric_dict = self.get_cfg_val("queries")[current_category]["metrics"][current_metric]
        self.update_metric_menus(required_metric_dict)
        
    def _ux_choose_color(self,event=None):
        self.color_button_widget["background"] = colorchooser.askcolor()[1]
        
    def _ux_send_to_axis(self,which_axis="left"):
        current_selections_pack = self.generate_current_selections_pack(which_axis)
        try:
            self.controller.request_and_graph_data(current_selections_pack)
        except AttributeError:
            PRETTYPRINT(current_selections_pack)
        
    # SELECTIONS PACK FUNCTIONS
    
    def generate_current_selections_pack(self,which_axis="left"):
        return {
            "x_axis_type": self.current_x_axis_type.get(),
            "data_filters": {
                "start_datetime": self.start_datetime,
                "end_datetime": self.end_datetime,
                "category_or_product":self.current_product_var.get(),
                "category_or_product_entry":self.current_product_entry_var.get(),
                "platform":self.current_platform_var.get(),
            },
            "metric_options":{ 
                "metric":self.current_metric_var.get(),
                "metric_type":self.current_metric_type_var.get(),
                "data_type":self.current_metric_data_type_var.get(),
                "breakdown":self.current_metric_breakdown_var.get(),
                "number_of_rankings":self.current_n_rankings_var.get(),
            },
            "result_options": {
                "aggregation_period":self.current_aggregation_time_var.get(),
                "aggregation_type":self.current_aggregation_type_var.get(),
                "compare_to_days":self.current_compare_to_days_var.get(),
            },
            "graph_options": {
                "line_style":self.current_linestyle_var.get(),
                "color":self.color_button_widget["background"],
                "axis": which_axis,
                "custom_name": self.current_custom_name_entry_var.get()
            } 
        }
        
    def reset_vars(self):
        self.current_x_axis_type.set("DEFAULT_IGNORE")
        
        self.current_product_var.set("DEFAULT_IGNORE"),
        self.current_product_entry_var.set("None"),
        self.current_platform_var.set("DEFAULT_IGNORE"),
        
        self.current_metric_var.set("DEFAULT_IGNORE"),
        self.current_metric_type_var.set("DEFAULT_IGNORE"),
        self.current_metric_data_type_var.set("DEFAULT_IGNORE"),
        self.current_metric_breakdown_var.set("DEFAULT_IGNORE"),  
        
        self.current_compare_to_days_var.set(0)       
        self.current_custom_name_entry_var.set("None")
                
    # BUILD FUNCTIONS
        
    def build_skeleton(self):
        self.category_dropdown_labelframe = tk.LabelFrame(self,text="Category Menu")
        self.category_dropdown_labelframe.grid(row=0,column=0,sticky="nesw")
        
        self.data_filters_labelframe = tk.LabelFrame(self,text="Data Filters")
        self.data_filters_labelframe.grid(row=1,column=0,sticky="nesw")
        
        self.metric_options_labelframe = tk.LabelFrame(self,text="Metric Options")
        self.metric_options_labelframe.grid(row=2,column=0,sticky="nesw")
        
        self.results_options_labelframe = tk.LabelFrame(self,text="Result Options")
        self.results_options_labelframe.grid(row=3,column=0,sticky="nesw")
        
        self.graph_options_labelframe = tk.LabelFrame(self,text="Graph Options")
        self.graph_options_labelframe.grid(row=4,column=0,sticky="nesw") 
        
        self.send_to_axis_buttons_labelframe = tk.LabelFrame(self,text="Send to Graph Axis")
        self.send_to_axis_buttons_labelframe.grid(row=5,column=0,sticky="news")

    def build_category_menu(self):
        for key,value in self.get_config()["queries"].items():
            self.categories_list.append(value["proper_title"])
        rown = 0
        self.category_dropdown = ttk.Combobox(self.category_dropdown_labelframe, textvariable=self.current_category_var,
                                          width=30)
        self.category_dropdown.grid(row=rown, column=0,columnspan=1,
                                    padx=(0,0),pady=(0,0))   
        
        self.category_dropdown["values"] = self.categories_list
        self.category_dropdown["state"] = "readonly" 
        self.category_dropdown.current(0)
        self.category_dropdown.bind('<<ComboboxSelected>>',self._ux_category_changed)        
        
    # DATA FILTER BUILDS
    
    def build_data_filters(self,targ_frame,required_data_filters_list):
        for child in targ_frame.winfo_children():
            child.destroy()          
        
        curr_row = 0
        for index,data_filter in enumerate(required_data_filters_list):
            self.log("Building data_filter: {}".format(data_filter))
            if data_filter == "start_end_dates":
                curr_row = self.build_start_end_data_filter(targ_frame,rown=curr_row)

            elif data_filter == "category_or_product":
                curr_row = self.build_category_or_product_data_filter(targ_frame,rown=curr_row)
                
            elif data_filter == "platform":
                curr_row = self.build_platform_data_filter(targ_frame,rown=curr_row)
                
    def build_start_end_data_filter(self,targ_frame,rown=0):
        tk.Label(targ_frame,text="Start Date:").grid(row=rown,column=0,sticky="w",
                columnspan=1)
        ttk.Button(targ_frame,command=self._ux_open_start_cal, textvariable=self.start_date_button_var).grid(
                row=rown, column=1,columnspan=2, pady=2,sticky="w")        
        rown += 1
        
        tk.Label(targ_frame,text="End Date:").grid(row=rown,column=0,sticky="w",
                columnspan=1)     
        ttk.Button(targ_frame,command=self._ux_open_end_cal,textvariable=self.end_date_button_var).grid(
                row=rown, column=1,columnspan=2, pady=2,sticky="w")        
        rown += 1
        
        tk.Label(targ_frame,text="Skip Dates:").grid(row=rown,column=0,sticky="w",
                columnspan=1)     
        ttk.Button(targ_frame,text="<<",width=3,command=lambda: self._ux_skip_calendars(-30)).grid(
                row=rown,column=1,pady=2,sticky="w")
        ttk.Button(targ_frame,text=">>",width=3,command=lambda: self._ux_skip_calendars(30)).grid(
                row=rown, column=2, pady=2,sticky="w")   
        
        return rown + 1
        
    def build_category_or_product_data_filter(self,targ_frame, rown=0):
        tk.Label(targ_frame,text="Product:").grid(row=rown, column=0,sticky="w")
        
        dropdown = ttk.Combobox(targ_frame, textvariable=self.current_product_var,
                                width=15)
        dropdown.grid(row=rown, column=1,columnspan=2,padx=(0,0),
                      pady=(0,0),sticky="w")   
        
        dropdown["values"] = ["All","Category","Product Code"]
        dropdown["state"] = "readonly" 
        dropdown.current(0) 
        rown += 1
        
        ttk.Entry(targ_frame,textvariable=self.current_product_entry_var,justify="left").grid(
        row=rown,column=1,columnspan=3)
        
        return rown + 1
        
    def build_platform_data_filter(self,targ_frame,rown=0):
        coln = 0
        
        tk.Label(targ_frame,text="Gen. Platform: ").grid(row=rown, column=coln,sticky="w")
        coln += 1
        
        dropdown = ttk.Combobox(targ_frame, textvariable=self.current_platform_var,
                                width=10)
        dropdown.grid(row=rown, column=coln,columnspan=2,padx=(0,0),
                      pady=(0,0),sticky="w")   
        
        dropdown["values"] = ["All","PC","Mobile"]
        dropdown["state"] = "readonly" 
        dropdown.current(0) 
        
        return rown + 1
    
    # METRIC OPTIONS BUILD
        
    def build_metric_options(self,targ_frame,required_metrics_dict,rown=0):
        for child in targ_frame.winfo_children():
            child.destroy()  
            
        self.metrics_list = []
        
        for name,config in required_metrics_dict.items():
            self.metrics_list.append(config["proper_title"])   
            
        tk.Label(targ_frame,text="Metric:").grid(row=rown, column=0,sticky="w")   
        
        dropdown = ttk.Combobox(targ_frame, textvariable=self.current_metric_var,width=20)
        dropdown.grid(row=rown, column=1,padx=(0,0),pady=(0,0),sticky="w")   
        dropdown["values"] = self.metrics_list
        dropdown["state"] = "readonly" 
        dropdown.current(0)      
        dropdown.bind('<<ComboboxSelected>>',self._ux_metric_changed)
        
        for name,config in required_metrics_dict.items():
            self.metrics_list.append(config["proper_title"])    
            
        rown += 1
        tk.Label(targ_frame,text="Metric Type:").grid(row=rown, column=0,sticky="w")
        
        self.metric_type_menu = ttk.Combobox(targ_frame, textvariable=self.current_metric_type_var,width=20)
        self.metric_type_menu.grid(row=rown, column=1,padx=(0,0),pady=(0,0),sticky="w")   
        self.metric_type_menu["state"] = "readonly" 
        
        rown += 1
        tk.Label(targ_frame,text="Data Type:").grid(row=rown, column=0,sticky="w")
        self.metric_data_type_menu = ttk.Combobox(targ_frame, textvariable=self.current_metric_data_type_var,width=20)
        self.metric_data_type_menu.grid(row=rown, column=1,padx=(0,0),pady=(0,0),sticky="w")   
        self.metric_data_type_menu["state"] = "readonly"   
        
        rown += 1
        tk.Label(targ_frame,text="Breakdown:").grid(row=rown, column=0,sticky="w")
        self.metric_breakdown_menu = ttk.Combobox(targ_frame, textvariable=self.current_metric_breakdown_var,width=20)
        self.metric_breakdown_menu.grid(row=rown, column=1,padx=(0,0),pady=(0,0),sticky="w")   
        self.metric_breakdown_menu["state"] = "readonly"        

        rown += 1
        tk.Label(targ_frame,text="X Rankings (Breakdown):").grid(row=rown, column=0,sticky="w")
        tk.Spinbox(targ_frame, from_=1.0, to=10.0, wrap=True, width=4, 
                   validate="key", state="readonly",textvariable=self.current_n_rankings_var).grid(
                           row=rown,column=1,sticky="w",columnspan=15) 

        self._ux_metric_changed()
        
    def update_metric_menus(self, met_cfg):
        self.metric_type_menu["values"] = met_cfg["metric_types"]
        self.metric_type_menu.current(0)
        self.metric_data_type_menu["values"] = met_cfg["data_types"]
        self.metric_data_type_menu.current(0)
        self.metric_breakdown_menu["values"] = met_cfg["breakdown_types"]
        self.metric_breakdown_menu.current(0)
        
    # RESULTS OPTIONS BUILD
        
    def build_results_options_menu(self,targ_frame,rown=0):
        tk.Label(targ_frame,text="Aggregation Period: ").grid(row=rown, column=0,sticky="w")
        dropdown = ttk.Combobox(targ_frame, textvariable=self.current_aggregation_time_var,width=10)
        dropdown.grid(row=rown, column=1,padx=(0,0),pady=(0,0),sticky="w")   
        dropdown["values"] = ["Daily","Weekly","Monthly","Entire"]
        dropdown["state"] = "readonly" 
        dropdown.current(0)      
        
        rown += 1
        tk.Label(targ_frame,text="Aggregation Type:").grid(row=rown, column=0,sticky="w")
        dropdown = ttk.Combobox(targ_frame, textvariable=self.current_aggregation_type_var,width=10)
        dropdown.grid(row=rown, column=1,padx=(0,0),pady=(0,0),sticky="w")   
        dropdown["values"] = ["Sum","Average"]
        dropdown["state"] = "readonly" 
        dropdown.current(0)   
        
        rown += 1
        tk.Label(targ_frame,text="Compare to X Days Before:").grid(row=rown, column=0,sticky="w")
        tk.Spinbox(targ_frame, from_=0.0, to=365.0, wrap=True, width=4, 
                   validate="key", state="normal",textvariable=self.current_compare_to_days_var).grid(
                           row=rown,column=1,sticky="w",columnspan=15)          

    # GRAPH OPTIONS BUILD
        
    def build_graph_options_menu(self,targ_frame,rown=0):
        
        tk.Label(targ_frame,text="Line Style:").grid(row=rown, column=0,sticky="w")
        x = ttk.Combobox(targ_frame, textvariable=self.current_linestyle_var,width=2,
         values=["-","--","-.",":"],state="readonly")
        x.grid(row=rown, column=1,columnspan=1, sticky="w",padx=(5,0)) 
        x.current(0)
        rown += 1

        tk.Label(targ_frame,text="Color:").grid(row=rown, column=0,sticky="w")
        self.color_button_widget = tk.Button(targ_frame,width=1,height=1,command=self._ux_choose_color)
        self.color_button_widget.grid(row=rown,column=1,padx=(0,0))
        self.color_button_widget.configure(background="black")
        rown += 1
        
        tk.Label(targ_frame,text="Custom Name:").grid(row=rown, column=0,sticky="w")
        ttk.Entry(targ_frame, width=20, textvariable=self.current_custom_name_entry_var).grid(
                  row=rown, column=1, sticky="w",padx=(0,0))        
        
    # SEND TO AXIS BUILD
    
    def build_send_to_axis_menu(self,targ_frame,rown=0):
        send_left_button = tk.Button(targ_frame,text="Left Axis",
                                     command=lambda: self._ux_send_to_axis("left"))
        send_left_button.grid(row=rown,column=0)

        send_left_button = tk.Button(targ_frame,text="Right Axis",
                                     command=lambda: self._ux_send_to_axis("right"))
        send_left_button.grid(row=rown,column=1)
        
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
    
    controls_config = config2.backend_settings
    dbfile =  open(r"databases/DH_DBS.pickle", "rb")
    dbs = pickle.load(dbfile)  
    app = tk.Tk()    
    querypanel = QueryPanel(app,app,controls_config,dbvar=dbs)
    querypanel.grid(padx=20)
    app.mainloop()              