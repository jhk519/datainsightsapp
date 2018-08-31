# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 15:41:08 2018

@author: Justin H Kim
"""
# Tkinter Modules
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
from pprint import pprint
import copy
import datetime

# Project Modules
from appwidget import AppWidget
import master_calendar.calendardialog as cal_dialog
   
class QueryPanel(AppWidget):
    def __init__(self,parent,controller,config,dbvar=None):
        self.widget_name = "querypanel"
        super().__init__(parent,controller,config,dbvar) 
            
#        UI Vars
        self.check_valid = "DataInsightsApp_ControlPanel"
        self.start_date = None
        self.end_date = None   

        self.ls_query_panels = []
        self.prime_results_pack = None
        self.secondary_results_pack = None

#        lock/unlock y-axis when skipping by week or month
#        autosearch on query change
        self.autosearch = tk.BooleanVar()
        self.autosearch.set(False)          
        
        self.hold_y_var = tk.BooleanVar()
        self.hold_y_var.set(False)
        
        self.start_textvar = tk.StringVar()
        self.start_textvar.set("Pick Start Date")    
        
        self.end_textvar = tk.StringVar()
        self.end_textvar.set("Pick End Date")  

        self.category_menu = None
        self.max_num_queries = 11
        self.use_extra_var = tk.BooleanVar()
        self.use_extra_var.set(False)
        self.extra_var = tk.StringVar()
        
        self.category_var = tk.StringVar() 
        self.ls_query_packs = []
        
        self.x_axis_type = tk.StringVar()
        self.x_axis_type.set("None")
        
        self.use_mirror_var = tk.BooleanVar()
        self.use_mirror_var.set(False)
        
        self.mirror_days_var = tk.IntVar()
        self.mirror_days_var.set(0)
        self.axis_panels = {
            "left": {
                "axispanel": None,
                "gtype":None,
                "dbtype": None,
                "metric": None,
                "queries":[]
            },
            "right": {
                "axispanel": None,
                "gtype":None,
                "dbtype": None,
                "metric": None,
                "queries":[]                        
            }
        }
        
#       Set Build Config and Update
        self.config_key = "querypanel"    
        if config:
            self.engine.set_build_config(raw_config = config[self.config_key])  
            
#        Build Skeleton UI

        self.build_date_pane()
        self.__build_query_menu()
        self.populate_query_menu()
        self.build_left_queries()
        self.build_right_queries()
        self.populate_queries()
        self.build_options()
        self._update_queries(self.category_var.get()) 
        
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1) 
        self.rowconfigure(1,weight=1) 
        self.rowconfigure(2,weight=1) 
        self.rowconfigure(3,weight=1)         
        
#       CONFIG
        if config:
            if self.engine.get_cfg_val("setdates_on_load"):
                self._set_dates(self.engine.get_set_date_config())            
            
#   API            
                
    def gen_selection_pack(self):
        self.log("Starting Selection Pack Gen.")  
        left_comp = [(p[0].get(), p[2]["background"]) for i,p in enumerate(self.axis_panels["left"]["queries"])]
        right_comp = [(p[0].get(), p[2]["background"]) for i,p in enumerate(self.axis_panels["right"]["queries"])]
        selpack = {
            "extra":self.extra_var.get(),
            "x_axis_label": self.x_axis_type.get(),
            "mirror_days": self.mirror_days_var.get(),            
            "left": {
                "gtype":self.axis_panels["left"]["gtype"],
                "db-type": self.axis_panels["left"]["dbtype"],
                "metric": self.axis_panels["left"]["metric"],
                "queries": left_comp,
            },
            "right": {
                "gtype":self.axis_panels["right"]["gtype"],
                "db-type": self.axis_panels["right"]["dbtype"],
                "metric": self.axis_panels["right"]["metric"],
                "queries": right_comp,
                #selected_query_pack = [stvar, label, choose_color, delete]      
            }, 
            "start": self.start_date,
            "end": self.end_date,
            "hold_y": self.hold_y_var.get()            
        }
        self.log("Start: {}, End: {}, Hold_y: {}".format(selpack["start"], selpack["end"], selpack["hold_y"] ))
        return selpack  
    
    def set_cfgvar(self,new_cfgvar):
        self.log("Changing cfg.")
        self.engine.set_build_config(new_cfgvar[self.widget_name]) 
        for widget in self.config_chain:
            widget.set_cfgvar(new_cfgvar)
        colors = self.engine.get_colors_preferred()
        all_query_slots = self.axis_panels["left"]["queries"] + self.axis_panels["right"]["queries"]
        for query_index, query_slot_pack in enumerate(all_query_slots):
            color_button = query_slot_pack[2]
            color_button["background"] = colors[query_index]
            
    def _set_dates(self,date_cfg_pack):
        self.start_date,self.end_date = self.engine.set_end_date(date_cfg_pack)
        self.start_textvar.set(str(self.start_date))
        self.end_textvar.set(str(self.end_date))              
            
#   UX EVENT HANDLERS AND HELPERS   
  # ===================================================================
#       UX EVENT HANDLERS AND HELPERS
# =================================================================== 
#   Note that days is positive or negative!
    def _skip_calendars(self, days):
        self.start_date = self.start_date + datetime.timedelta(days)
        self.end_date = self.end_date + datetime.timedelta(days)
        self.start_textvar.set(str(self.start_date))
        self.end_textvar.set(str(self.end_date))
        self._check_controller_autosearch()

    def _open_start_calendar(self):
        start_calendar = cal_dialog.CalendarDialog(
            self)
        self.start_date = start_calendar.result.date()
        self.start_textvar.set(str(self.start_date))
        self._check_controller_autosearch()        

    def _open_end_calendar(self):
        end_calendar = cal_dialog.CalendarDialog(self)
        try:
            self.end_date = end_calendar.result.date()
        except AttributeError:
            self.info("end_calendar.result.date() Probably Returned NoneType")
        self.end_textvar.set(str(self.end_date))
        self._check_controller_autosearch()        

    def _open_ref_calendar(self):
        ref_calendar = cal_dialog.CalendarDialog(self)
        self.extra_date = ref_calendar.result.date()
        self.extra_textvar.set(str(self.extra_date))
            
    def _use_extra_var_changed(self):
        need_use = self.use_extra_var.get()
        if need_use:
            self.extra_widget.grid()
            for axis in ["left","right"]:
                for ind,pack in enumerate(self.axis_panels[axis]["queries"]):
                    qstr = pack[0].get()
                    if qstr == "None":
                        continue
                    if self.engine.get_cfg_val("queries_ref")[qstr]["can_filter"] == None:
                        self._delete_query((axis,ind))
        else:
            self.extra_widget.grid_remove()
            self.extra_var.set("")
        self._update_queries(self.category_var.get())
        
    def _use_mirror_var_changed(self):
        need_use = self.use_mirror_var.get()
        if need_use:
            self.mirror_days_entry.grid()
            self.mirror_days_var.set(30)
        else:
            self.mirror_days_entry.grid_remove()
            self.mirror_days_var.set(0)

    def _send_to_axis(self,which_axis,index):
        query_str = self.ls_query_packs[index][0].get()
        query_ref = self.engine.get_cfg_val("queries_ref")[query_str]
        
        curr_x = self.x_axis_type.get()
        targ_metric = self.axis_panels[which_axis]["metric"]
        targ_curr_queries = self.axis_panels[which_axis]["queries"]
        
#        if x-type already exists, and they dont match, cancel operation
#        if they match, carry on
        if not curr_x == "None" and not curr_x == query_ref["x-axis-label"]:
            self.log("Current X-Axis Type: {} =/= {}".format(
                    self.x_axis_type,query_ref["x-axis-label"]))
            return False
#       if no x-type exists, set it to the requested-query's x-axis type and 
#       carry on
        elif curr_x == "None":
            self.x_axis_type.set(query_ref["x-axis-label"])

#       check if that axis already has a y-metric, if they dont match, cancel
#       if none exists, set metric, gtype and dbtype. 
        if targ_metric and not targ_metric == query_ref["y-axis-label"]:   
            self.log("Y-Axis Type: {} =/= {}".format(targ_metric,query_ref["y-axis-label"]))
            return False
        elif not targ_metric:
            self.axis_panels[which_axis]["metric"] = query_ref["y-axis-label"]
            self.axis_panels[which_axis]["gtype"] = query_ref["chart-type"]
            self.axis_panels[which_axis]["dbtype"] = query_ref["db-req"]

        for index, select_pack in enumerate(targ_curr_queries):
            stvar, label, choose_color, delete  = select_pack
            if stvar.get() == "None":
                stvar.set(query_str)
                self._update_queries(self.category_var.get())
                return True
            elif stvar.get() == query_str:
                self.bug("{} is already Included! It should not have been available to send.".format(
                        query_str))
                return False
            elif index == 3:
                self.bug("Cannot find a select_pack to change to {}!".format(query_str))
                return False
        
    def _update_queries(self, category):
        self.log(".update_queries called for category {}".format(category))
        req_queries = self.engine.get_queries_list(category)

        try:
            self.hold_y_var
        except AttributeError:
            self.bug("{} not suitable for .hold_y_var callback".format(str(self.controller)))   
        else:     
            self.hold_y_var.set(False)
                
        q_count = 0
        for index,pack in enumerate(self.ls_query_packs):
            query_var, left_axis, right_axis = pack
            query_var.set("")
            left_axis.grid()
            left_axis["state"] = "disabled"
            right_axis.grid()            
            right_axis["state"] = "disabled"    

            if not q_count < len(req_queries):
                left_axis.grid_remove()
                right_axis.grid_remove()
                continue
            
            query_str = req_queries[q_count]
            query_ref = self.engine.get_cfg_val("queries_ref")[query_str]
            query_var.set(query_str)

            curr_x = self.x_axis_type.get()
            q_count += 1 
            
            #if cannot use product filter, and product filter input exists       
            if self.use_extra_var.get() == True and query_ref["can_filter"] == None:
                continue    
            
            if curr_x == "None" or curr_x == query_ref["x-axis-label"]:
                left_m = self.axis_panels["left"]["metric"] 
                right_m = self.axis_panels["right"]["metric"]
                if left_m == query_ref["y-axis-label"] or left_m == None:
                    found = False
                    for qpack in self.axis_panels["left"]["queries"]:
                        #qpack = [stvar, label, choose_color, delete]
                        if query_str == qpack[0].get():
                            found = True
                            break
                    if not found:
                        left_axis["state"] = "normal"
                if right_m == query_ref["y-axis-label"] or right_m == None:   
                    found = False
                    for qpack in self.axis_panels["right"]["queries"]:
                        if query_str == qpack[0].get():
                            found = True
                            break
                    if not found:
                        right_axis["state"] = "normal"
                        
        self._check_controller_autosearch()
                        
    def _check_controller_autosearch(self):
        if self.autosearch.get():
            self.push_search()
    
    def push_search(self):
        self.log("*** Push Search ***")
        selection_pack = self.gen_selection_pack()
        self.controller.search_queries(selection_pack)
                    
    def _category_changed(self,event=None):
        self._update_queries(self.category_var.get())
        self.category_menu.selection_clear()
        
    def _clear_axis_info(self,axis):
        for key in ["gtype","db-type","metric"]:
            self.axis_panels[axis][key] = None 

    def _is_axis_empty(self,axis):
        found_something = False
        for qpack in self.axis_panels[axis]["queries"]:
            if not qpack[0].get() == "None":
                    found_something = True
        return not found_something
      
            
    def _clear_all_queries(self,axis):
        self.log("Clear all queries for axis: {}".format(axis))
        for index in range(0,4):
          self.bug("Clear all queries iteration: {}".format(index))
          self._delete_query((axis,0))
            
    def _delete_query(self,axis_index):
        self.bug("Delete_query called for: {}".format(axis_index))
        axis,index = axis_index
        targ_queries = self.axis_panels[axis]["queries"]
        targ_qpack = targ_queries[index]
        targ_qpack[0].set("None")
        
        for row_x in range(index,4):
            try:
                next_value = targ_queries[row_x+1][0].get()
            except IndexError:
                next_value = "None"
            targ_queries[row_x][0].set(next_value)
        
        if self._is_axis_empty("left"):
            self._clear_axis_info("left")
        if self._is_axis_empty("right"):
            self._clear_axis_info("right")
        if self._is_axis_empty("left") and self._is_axis_empty("right"):
            self.x_axis_type.set("None")
        self._update_queries(self.category_var.get())
            
    def _choose_colors(self, axis_index):
        get_color = colorchooser.askcolor()[1]
        axis,index = axis_index
        pack = self.axis_panels[axis]["queries"][index]
        pack[2]["background"] = get_color
        
#   BUILD FUNCTIONS
        
    def build_date_pane(self):
        self.date_pane = ttk.Labelframe(
            self, text="Date Range")
        self.date_pane.grid(row=0,column=0,columnspan=2,sticky="W")        

        self.back_one_month_button = ttk.Button(
            self.date_pane, command=lambda: self._skip_calendars(-30), text="<<",width=3)
        self.back_one_month_button.grid(
                row=0, column=0, padx=(5, 0), pady=2)
        self.back_one_week_button = ttk.Button(
            self.date_pane, command=lambda: self._skip_calendars(-7), text="<",width=3)
        self.back_one_week_button.grid(
                row=0, column=1, padx=5, pady=2)

        self.start_day_button = ttk.Button(self.date_pane,
                                          command=self._open_start_calendar,
                                          textvariable=self.start_textvar)
        self.start_day_button.grid(row=0, column=2, padx=5, pady=2)

        self.end_day_button = ttk.Button(self.date_pane,command=self._open_end_calendar,
            textvariable=self.end_textvar)
        self.end_day_button.grid(row=0, column=3, padx=5, pady=2)

        self.forward_one_week_button = ttk.Button(
            self.date_pane, command=lambda: self._skip_calendars(7), text=">",width=3)
        self.forward_one_week_button.grid(
                row=0, column=4, padx=5, pady=2)

        self.forward_one_month_button = ttk.Button(
            self.date_pane, command=lambda: self._skip_calendars(30), text=">>",width=3)
        self.forward_one_month_button.grid(
            row=0, column=5, padx=(0, 5), pady=2)


    def __build_query_menu(self):        
#        QUERY MENU
        self.query_menu = ttk.LabelFrame(self,text="Select Queries")
        self.query_menu.grid(row=1,column=0,sticky="wn",rowspan=3,padx=(5,5),pady=(8,8))

        self.x_axis_type_header = ttk.Label(self.query_menu, text="Current X-Axis: ",anchor="w")
        self.x_axis_type_header.grid(row=0,column=0,sticky="w",pady=(5,5))
        
        self.x_axis_type_label = ttk.Label(self.query_menu, textvariable=self.x_axis_type)
        self.x_axis_type_label.grid(row=0,column=1,sticky="W",pady=(5,5))  
        
        self.category_label = ttk.Label(self.query_menu, text="Category: ")
        self.category_label.grid(row=1,column=0,sticky="w",padx=0,pady=(5,15))

        self.category_menu = ttk.Combobox(self.query_menu, textvariable=self.category_var,
                                          width=17)
        self.category_menu.grid(row=1, column=1,columnspan=2,pady=(5,5), sticky="w",
                                padx=(0,5))
        
        self.category_menu["values"] = self.engine.get_cfg_val("categories")
        self.category_menu.current(0)         
        self.category_menu.bind('<<ComboboxSelected>>',self._category_changed)
        self.category_menu["state"] = "readonly"  
      
        self.query_menu_separator = ttk.Separator(self.query_menu)
        self.query_menu_separator.grid(row=2,column=0,columnspan=4,sticky="ew",
                                       padx=(45,45),pady=(5,5))
        
    def populate_query_menu(self):
        for index in range(0,self.max_num_queries):
            row_n = index + 3
            query_var = tk.StringVar()
            
            query_label = tk.Label(self.query_menu,textvariable=query_var,anchor="w",
                                   font="Helvetica 9")
            query_label.grid(row=row_n,column=0,sticky="ew",padx=(5,0))
            
            send_left_axis = tk.Button(self.query_menu,text="←L",width=5,
                      command=lambda index=index:self._send_to_axis("left",index))
            send_left_axis.grid(row=row_n,column=1,sticky="e",padx=(10,0),pady=(5))
            
            send_right_axis = tk.Button(self.query_menu,text="R→",width=5,
                      command=lambda index=index:self._send_to_axis("right",index))
            send_right_axis.grid(row=row_n,column=2,sticky="w",padx=(5,5))
            
            pack = (query_var, send_left_axis, send_right_axis)
            self.ls_query_packs.append(pack)
            
    #       BUILD AXIS PANELS
    def build_left_queries(self):            
            left_query_panel = ttk.LabelFrame(self,text="Left Axis")
            left_query_panel.grid(row=1,column=1,sticky="wn",padx=(5,5),pady=(8,8))
            left_clear_all = tk.Button(left_query_panel,text="Clear",foreground="red",
                                       command=lambda: self._clear_all_queries("left"),
                                       relief="groove",font="Helvetica 7",width=4)
            left_clear_all.grid(row=5,column=1,sticky="ne",padx=10,pady=5,columnspan=2)
            self.axis_panels["left"]["axispanel"] = left_query_panel
            
    def build_right_queries(self):
            right_query_panel = ttk.LabelFrame(self,text="Right Axis")
            right_query_panel.grid(row=2,column=1,sticky="wn",padx=(5,5),pady=(8,8))  
            right_clear_all = tk.Button(right_query_panel,text="Clear",foreground="red",
                                       command=lambda: self._clear_all_queries("right"),
                                       relief="groove",font="Helvetica 7",width=4)      
            right_clear_all.grid(row=5,column=1,sticky="ne",padx=10,pady=5,columnspan=2)
            self.axis_panels["right"]["axispanel"] = right_query_panel
            
    def populate_queries(self):        
            available_colors = self.engine.get_colors_preferred() 
            for axis in ["left","right"]:        
                for index in range(0,4):
                    rownum = index + 1
                    colorindex = index
                    
                    if axis == "right":
                        colorindex = index + 4   
                    
                    currframe = self.axis_panels[axis]["axispanel"]
                    
                    stvar = tk.StringVar()
                    stvar.set("None")
                    label = tk.Label(currframe,textvariable=stvar,wraplength=110,anchor="w",
                                     justify="left",width=15,height=2)
                    label.grid(row=rownum,column=0,padx=(10,0),sticky="w")
                    
                    axis_index = axis,index
                    choose_color = tk.Button(currframe,width=1,height=1,
                         command=lambda axis_index =axis_index :self._choose_colors(axis_index))
                    choose_color.grid(row=rownum,column=1,padx=(10,0))
                    choose_color.configure(background=available_colors[colorindex]) 
    
                    delete = tk.Button(currframe,width=1, text="x",
                        command=lambda axis_index=axis_index:self._delete_query(axis_index),
                        font="Helvetica 7")
                    delete.grid(row=rownum, column=2,padx=(10,10),pady=(5,0),sticky="ne")
                    
                    selected_query_pack = [stvar, label, choose_color, delete]
                    self.axis_panels[axis]["queries"].append(selected_query_pack)
                
    def build_options(self):
        x = 1
        self.options_menu = ttk.LabelFrame(self,text="Options and Search")
        self.options_menu.grid(row=3,column=0,sticky="nwse",columnspan=2,padx=(5,5),pady=(8,8))
        
        self.extra_use_check = ttk.Checkbutton(self.options_menu,text="Filter by Product Code",
              onvalue=True,  offvalue=False, variable=self.use_extra_var,
              command=lambda x= x:self._use_extra_var_changed())
        self.extra_use_check.grid(row=0,column=0,sticky="w")
        
        self.extra_widget = ttk.Entry(self.options_menu, width=15, textvariable=self.extra_var)
        self.extra_widget.grid(row=0, column=1,columnspan=1, pady=2, sticky="w")
        self.extra_widget.grid_remove()
            
        self.mirror_days_check = ttk.Checkbutton(self.options_menu,text="Mirror with Past Data",
              onvalue=True,  offvalue=False, variable=self.use_mirror_var,
              command=lambda x= x:self._use_mirror_var_changed())
        self.mirror_days_check.grid(row=1,column=0,sticky="w")          
        
        self.mirror_days_entry = ttk.Entry(self.options_menu, width=5, textvariable=self.mirror_days_var)
        self.mirror_days_entry.grid(row=1, column=1,columnspan=2, sticky="w")
        self.mirror_days_entry.grid_remove()     
        
        self.hold_y_axis_button = ttk.Checkbutton(
            self.options_menu,
            text="Lock Y-Axis",
            variable=self.hold_y_var,
            onvalue=True,
            offvalue=False)
        self.hold_y_axis_button.grid(row=2,column=0,sticky="w",
            columnspan=1)      
        
        self.should_search_on_query_change = ttk.Checkbutton(
            self.options_menu,
            text="Search on Query/Date Change",
            variable=self.autosearch,
            onvalue=True,
            offvalue=False)
        self.should_search_on_query_change.grid(
            row=3, column=0,sticky="w")
        self.should_search_on_query_change.invoke()

        self.entry_input_button = ttk.Button(
            self.options_menu,
            command=self.push_search,
            text="Search")
        self.entry_input_button.grid(row=4, column=0,sticky="w")        
                        
#if __name__ == "__main__":
#    import config2
#    cfg = config2.backend_settings
#    app = tk.Tk()
#    panel = QueryPanel(app,config=cfg,panel_name="Right Axis")
#    panel.grid(padx=20)
#    app.mainloop()