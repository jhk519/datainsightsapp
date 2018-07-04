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
    
from pprint import pprint as pprint
import copy

# Project Modules
from default_engines import QueryPanelEngine
   
class QueryPanel(ttk.LabelFrame):
    def __init__(self,parent,controller=None,engine="default",config=None,panel_name=""):
        #If used in the app package, parent is a panel
        super().__init__(parent,text="Search Input")
        self.parent = parent
        if not controller:
            self.controller = parent
        else:
            self.controller = controller
            
#        Abstract Vars
        self.panel_name = panel_name
        self.enabled_state = True
        if str(engine) == "default":
            self.engine = QueryPanelEngine()
        else:
            self.engine = engine
            
#        UI Vars
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
        
        self.selection_pack = {
            "extra":self.extra_var.get(),
            "x_axis_label": self.x_axis_type.get(),
            "mirror_days": self.mirror_days_var.get(),
            "left": {
                "frame": None,
                "gtype":None,
                "dbtype": None,
                "metric": None,
                "queries":[]
            },
            "right": {
                "frame": None,
                "gtype":None,
                "dbtype": None,
                "metric": None,
                "queries":[]
                #selected_query_pack = [stvar, label, choose_color, delete]      
            },            
        }
#       Set Build Config and Update
        self.config_key = "querypanel_config"    
        if config:
            self.engine.set_build_config(raw_config = config[self.config_key])  
            
#        Build Skeleton UI
        self.__build_skeleton()
        self._update_category_menu()
        self._update_queries(self.category_var.get()) 
            
#   API                
    def get_selection_pack(self):
        stringified_pack = {
            "extra":self.extra_var.get(),
            "x_axis_label": self.x_axis_type.get(),
            "mirror_days": self.mirror_days_var.get(),            
            "left": {
                "gtype":self.selection_pack["left"]["gtype"],
                "db-type": self.selection_pack["left"]["dbtype"],
                "metric": self.selection_pack["left"]["metric"],
                "queries":[]
            },
            "right": {
                "gtype":self.selection_pack["right"]["gtype"],
                "db-type": self.selection_pack["right"]["dbtype"],
                "metric": self.selection_pack["right"]["metric"],
                "queries":[]
                #selected_query_pack = [stvar, label, choose_color, delete]      
            },            
        }
            
        for axis in ["left","right"]:
            for ind,oldpack in enumerate(self.selection_pack[axis]["queries"]):
                new_pack = [oldpack[0].get(),oldpack[2]["background"]]
                stringified_pack[axis]["queries"].append(new_pack)     
        return stringified_pack 
    
    def set_cfgvar(self,new_cfgvar):
        self.engine.set_build_config(raw_config = new_cfgvar[self.config_key])
            
#   UX EVENT HANDLERS AND HELPERS      
    def _use_extra_var_changed(self):
        need_use = self.use_extra_var.get()
        if need_use:
            self.extra_widget.grid()
            for axis in ["left","right"]:
                for ind,pack in enumerate(self.selection_pack[axis]["queries"]):
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
        targ_metric = self.selection_pack[which_axis]["metric"]
        targ_curr_queries = self.selection_pack[which_axis]["queries"]
        
#        if x-type already exists, and they dont match, cancel operation
#        if they match, carry on
        if not curr_x == "None" and not curr_x == query_ref["x-axis-label"]:
            print("Current X-Axis Type:",self.x_axis_type,"=/=",query_ref["x-axis-label"]) 
            return False
#       if no x-type exists, set it to the requested-query's x-axis type and 
#       carry on
        elif curr_x == "None":
            self.x_axis_type.set(query_ref["x-axis-label"])

#       check if that axis already has a y-metric, if they dont match, cancel
#       if none exists, set metric, gtype and dbtype. 
        if targ_metric and not targ_metric == query_ref["y-axis-label"]:   
            print("Y-Axis Type:",targ_metric,"=/=",query_ref["y-axis-label"]) 
            return False
        elif not targ_metric:
            self.selection_pack[which_axis]["metric"] = query_ref["y-axis-label"]
            self.selection_pack[which_axis]["gtype"] = query_ref["chart-type"]
            self.selection_pack[which_axis]["dbtype"] = query_ref["db-req"]

        for index, select_pack in enumerate(targ_curr_queries):
            stvar, label, choose_color, delete  = select_pack
            if stvar.get() == "None":
                stvar.set(query_str)
                self._update_queries(self.category_var.get())
                return True
            elif stvar.get() == query_str:
                print("Already Included! This query should not have been available!")
                return False
            elif index == 3:
                print("Cannot find a select_pack to change to requested query!")
                return False
        
    def _update_category_menu(self):
        self.category_menu["values"] = self.engine.get_categories()
        self.category_menu.current(0)
        
    def _update_queries(self, category):
        req_queries = self.engine.get_queries_list(category)

        try:
            self.controller.hold_y_var
        except AttributeError:
            print("Not using valid controller")
            print(str(self.controller)," Not Suitable for Callback")      
        else:     
            self.controller.hold_y_var.set(False)
                
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
            
            if self.use_extra_var.get() == True and query_ref["can_filter"] == None:
                continue    
            
            if curr_x == "None" or curr_x == query_ref["x-axis-label"]:
                left_m = self.selection_pack["left"]["metric"] 
                right_m = self.selection_pack["right"]["metric"]
                if left_m == query_ref["y-axis-label"] or left_m == None:
                    found = False
                    for qpack in self.selection_pack["left"]["queries"]:
                        #qpack = [stvar, label, choose_color, delete]
                        if query_str == qpack[0].get():
                            found = True
                            break
                    if not found:
                        left_axis["state"] = "normal"
                if right_m == query_ref["y-axis-label"] or right_m == None:   
                    found = False
                    for qpack in self.selection_pack["right"]["queries"]:
                        if query_str == qpack[0].get():
                            found = True
                            break
                    if not found:
                        right_axis["state"] = "normal"
                        
        self._check_controller_autosearch()
                        
    def _check_controller_autosearch(self):
        try:
            self.controller.check_valid
        except AttributeError:
            print("QueryPanel Controller does not have check_valid attribute for autosearch!")
        else:
            self.controller.check_autosearch()
                    
    def _category_changed(self,event=None):
        self._update_queries(self.category_var.get())
        
    def _clear_axis_info(self,axis):
        for key in ["gtype","db-type","metric"]:
            self.selection_pack[axis][key] = None 

    def _is_axis_empty(self,axis):
        found_something = False
        for qpack in self.selection_pack[axis]["queries"]:
            if not qpack[0].get() == "None":
                    found_something = True
        return not found_something
            
    def _delete_query(self,axis_index):
        axis,index = axis_index
        targ_queries = self.selection_pack[axis]["queries"]
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
        pack = self.selection_pack[axis]["queries"][index]
        pack[2]["background"] = get_color
        
#   BUILD FUNCTIONS
    def __build_skeleton(self):
        x = 1
        self.extra_use_check = tk.Checkbutton(self,text="Use Product Code Filter",
              onvalue=True,  offvalue=False, variable=self.use_extra_var,
              command=lambda x= x:self._use_extra_var_changed())
        self.extra_use_check.grid(row=0,column=0,sticky="w")
        
        self.extra_widget = ttk.Entry(self, width=15, textvariable=self.extra_var)
        self.extra_widget.grid(row=0, column=1,columnspan=2, pady=2, sticky="w")
        self.extra_widget.grid_remove()
        
#       Build Axis Buckets        
        self.mirror_days_check = tk.Checkbutton(self,text="Mirror Queries with Past Results? ",
              onvalue=True,  offvalue=False, variable=self.use_mirror_var,
              command=lambda x= x:self._use_mirror_var_changed())
        self.mirror_days_check.grid(row=3,column=0,sticky="w",pady=(0,10))          
        
        self.mirror_days_entry = ttk.Entry(self, width=5, textvariable=self.mirror_days_var)
        self.mirror_days_entry.grid(row=3, column=1,columnspan=2, pady=2, sticky="w")
        self.mirror_days_entry.grid_remove()        
        
#        QUERY MENU
        self.query_menu = ttk.LabelFrame(self,text="Select Queries")
        self.query_menu.grid(row=4,column=0,columnspan=2,sticky="w")

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
        
        self.category_menu.bind('<<ComboboxSelected>>',self._category_changed)
        self.category_menu["state"] = "readonly"  
        
        self.query_menu_separator = ttk.Separator(self.query_menu)
        self.query_menu_separator.grid(row=2,column=0,columnspan=4,sticky="ew",
                                       padx=(45,45),pady=(5,5))
        
#       Build Queries        
        for index in range(0,self.max_num_queries):
            row_n = index + 3
            query_var = tk.StringVar()
            
            query_label = tk.Label(self.query_menu,textvariable=query_var,anchor="w")
            query_label.grid(row=row_n,column=0,sticky="ew",padx=(5,0))
            
            left_axis = tk.Button(self.query_menu,text="L",width=5,
                      command=lambda index=index:self._send_to_axis("left",index))
            left_axis.grid(row=row_n,column=1,sticky="e",padx=(10,0),pady=(5))
            
            right_axis = tk.Button(self.query_menu,text="R",width=5,
                      command=lambda index=index:self._send_to_axis("right",index))
            right_axis.grid(row=row_n,column=2,sticky="w",padx=(5,5))
            
            pack = (query_var, left_axis, right_axis)
            self.ls_query_packs.append(pack)
            
#       BUILD AXIS PANELS
        self.selection_pack["left"]["frame"] = ttk.LabelFrame(self,text="Left Axis")
        self.selection_pack["left"]["frame"].grid(row=4,rowspan=6,column=2,sticky="wn",
                           padx=(10,5))
        
        self.selection_pack["right"]["frame"] = ttk.LabelFrame(self,text="Right Axis")
        self.selection_pack["right"]["frame"] .grid(row=4,rowspan=6,column=3,sticky="wn")  
        
        available_colors = self.engine.get_colors_preferred() 
        for axis in ["left","right"]:        
            for index in range(0,4):
                rownum = index + 1
                backindex = index
                if axis == "right":
                    backindex = index + 4                
                
                currframe = self.selection_pack[axis]["frame"]
                
                stvar = tk.StringVar()
                stvar.set("None")
                label = tk.Label(currframe,textvariable=stvar,wraplength=110,anchor="w",
                                 justify="left",width=15)
                label.grid(row=rownum,column=0,padx=(10,0),sticky="w")
                
                axis_index = axis,index
                choose_color = tk.Button(currframe,width=1,
                     command=lambda axis_index =axis_index :self._choose_colors(axis_index))
                choose_color.grid(row=rownum,column=1,padx=(10,0))
                choose_color.configure(background=available_colors[backindex]) 

                delete = tk.Button(currframe,width=1, text="X",
                    command=lambda axis_index=axis_index:self._delete_query(axis_index))
                delete.grid(row=rownum, column=2,padx=(10,10))
                
                selected_query_pack = [stvar, label, choose_color, delete]
                self.selection_pack[axis]["queries"].append(selected_query_pack)

        
if __name__ == "__main__":
    import config2
    cfg = config2.backend_settings
    app = tk.Tk()
    panel = QueryPanel(app,config=cfg,panel_name="Right Axis")
    panel.grid(padx=20)
    app.mainloop()