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
    
import pprint as pprint


# Project Modules
from default_engines import QueryPanelEngine
   
class QueryPanel(ttk.LabelFrame):
    def __init__(self,parent,controller=None,engine="default",config=None,panel_name=""):
        #If used in the app package, parent is a panel
        super().__init__(parent)
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
        self.max_num_queries = 10
        self.extra_var = tk.StringVar()
        self.category_var = tk.StringVar() 
        self.x_axis_type = tk.StringVar()
        self.x_axis_type.set("None")
        self.ls_query_packs = []
        self.axis_packs = {
            "left": {
                "frame": None,
                "gtype":None,
                "db-type": None,
                "metric": None,
                "queries":[]
            },
            "right": {
                "frame": None,
                "gtype":None,
                "db-type": None,
                "metric": None,
                "queries":[]
            },            
        }
        
#        Build Skeleton UI
        self.__build_skeleton()
        
#       Set Build Config and Update
        self.config_key = "querypanel_config"    
        if config:
            self.engine.set_build_config(raw_config = config[self.config_key])  

        self._update_category_menu()
        self._update_queries(self.category_var.get()) 
            
#   API                
    def get_selection_pack(self):
#        extra = self.extra_var.get()
        selection_pack = {
            "extra":self.extra_var.get(),
            "x_axis_label": self.x_axis_type.get(),
            "left":None, 
            "right":None
        }     
        for axis,info in self.axis_packs.items():
            selection_pack[axis] = info       
        return selection_pack  
    
    def set_cfgvar(self,new_cfgvar):
        self.engine.set_build_config(raw_config = new_cfgvar[self.config_key])
            
#   UX EVENT HANDLERS AND HELPERS      
    def _send_to_axis(self,which_axis,index):
        available_colors = self.engine.get_colors_preferred() 
        compatible = True
        query_str = self.ls_query_packs[index][0].get()
        query_ref = self.engine.get_cfg_val("queries_ref")[query_str]
        curr_x = self.x_axis_type.get()
        targ_frame = self.axis_packs[which_axis]["frame"]
        targ_metric = self.axis_packs[which_axis]["metric"]
        targ_curr_queries = self.axis_packs[which_axis]["queries"]
        
        if not curr_x == "None":
            if not curr_x == query_ref["x-axis-label"]:
                print("Current X-Axis Type:",self.x_axis_type,"=/=",query_ref["x-axis-label"]) 
                compatible = False
                return            
        elif curr_x == "None":
            self.x_axis_type.set(query_ref["x-axis-label"])

        if targ_metric:
            if not targ_metric == query_ref["y-axis-label"]:   
                print("Y-Axis Type:",targ_metric,"=/=",query_ref["y-axis-label"]) 
                compatible = False
                return
        elif not targ_metric:
            self.axis_packs[which_axis]["metric"] = query_ref["y-axis-label"]
            self.axis_packs[which_axis]["gtype"] = query_ref["chart-type"]
            self.axis_packs[which_axis]["dbtype"] = query_ref["db-req"]
            
        if compatible:
            currlen = len(targ_curr_queries)
            temp = ttk.Label(targ_frame,text=query_str)
            temp.grid(row=currlen,column=0,sticky="w",pady=(10,10))
            
            com_tpl = which_axis, currlen
            choose_color = tk.Button(targ_frame,width=1,
                                     command=lambda com_tpl=com_tpl:self._choose_colors(com_tpl))
            choose_color.grid(row=len(targ_curr_queries),column=1,padx=(10,0))
            choose_color.configure(background=available_colors[currlen]) 
            
            delete_query_button = tk.Button(
                    targ_frame,width=2, command=lambda com_tpl=com_tpl:self._delete_query(com_tpl))
            delete_query_button.grid(row=len(targ_curr_queries), column=2,padx=(10,0))
            
            targ_curr_queries.append([query_str,available_colors[currlen],temp,choose_color,delete_query_button])
             
        self._update_queries(self.category_var.get())
    
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
            if curr_x == "None" or curr_x == query_ref["x-axis-label"]:
                left_m = self.axis_packs["left"]["metric"] 
                right_m = self.axis_packs["right"]["metric"]
                if left_m == query_ref["y-axis-label"] or left_m == None:
                    found = False
                    for qry in self.axis_packs["left"]["queries"]:
                        if query_str == qry[0]:
                            found = True
                            break
                    if not found:
                        left_axis["state"] = "normal"
                if right_m == query_ref["y-axis-label"] or right_m == None:   
                    found = False
                    for qry in self.axis_packs["right"]["queries"]:
                        if query_str == qry[0]:
                            found = True
                            break
                    if not found:
                        right_axis["state"] = "normal"
                    
    def _category_changed(self,event=None):
        self._update_queries(self.category_var.get())
        
    def _delete_query(self,command_tuple):
        which_axis,index = command_tuple
        for x in range(2,5):
           self.axis_packs[which_axis]["queries"][index][x].grid_forget() 
        self.axis_packs[which_axis]["queries"].pop(index)
        if not self.axis_packs[which_axis]["queries"]:
            for key in ["gtype","db-type","metric"]:
               self.axis_packs[which_axis][key] = None 
            self._update_queries(self.category_var.get())
            
    def _choose_colors(self, command_tuple):
        get_color = colorchooser.askcolor()[1]
        which_axis,index = command_tuple
        self.axis_packs[which_axis]["queries"][index][1] = get_color
        self.axis_packs[which_axis]["queries"][index][3]["background"] = get_color
        
#   BUILD FUNCTIONS
    def __build_skeleton(self):
        self.extra_entry_label = ttk.Label(self,text="Filter by Product:",anchor="w")
        self.extra_entry_label.grid(row=0, column=0, sticky="ew", padx=(0,25))
        
        self.extra_widget = ttk.Entry(self, width=15, textvariable=self.extra_var)
        self.extra_widget.grid(row=0, column=1,columnspan=1, pady=2, sticky="ew")
        
#       Build category
        self.category_label = ttk.Label(self, text="Category")
        self.category_label.grid(row=1,column=0,sticky="w",padx=0,pady=(5,15))

        self.category_menu = ttk.Combobox(self, textvariable=self.category_var)
        self.category_menu.grid(row=1, column=1,columnspan=2,pady=(5, 15),  sticky="w")
        
        self.category_menu.bind('<<ComboboxSelected>>',self._category_changed)
        self.category_menu["state"] = "readonly"
        
#       Build Axis Buckets
        self.x_axis_type_header = ttk.Label(self, text="X-Axis Type: ")
        self.x_axis_type_header.grid(row=1,column=3,padx=25)
        
        self.x_axis_type_label = ttk.Label(self, textvariable=self.x_axis_type)
        self.x_axis_type_label.grid(row=1,column=4)
        
        self.axis_packs["left"]["frame"] = ttk.Labelframe(self,text="Left Axis")
        self.axis_packs["left"]["frame"].grid(row=2,rowspan=10,column=3,sticky="n",
                                              padx=(15,15))
        
        self.axis_packs["right"]["frame"] = ttk.Labelframe(self,text="Right Axis")
        self.axis_packs["right"]["frame"] .grid(row=2,rowspan=10,column=4,sticky="n")     

#       Build Queries        
        for index in range(0,self.max_num_queries):
            query_var = tk.StringVar()
            
            query_label = tk.Label(self,textvariable=query_var,anchor="w")
            query_label.grid(row=index+2,column=0,sticky="ew")
            
            left_axis = tk.Button(self,text="L",width=5,
                      command=lambda index=index:self._send_to_axis("left",index))
            left_axis.grid(row=index+2,column=1,sticky="e",padx=(0,0),pady=(5))
            
            right_axis = tk.Button(self,text="R",width=5,
                      command=lambda index=index:self._send_to_axis("right",index))
            right_axis.grid(row=index+2,column=2,sticky="e",padx=(5,0))
            
            pack = (query_var, left_axis, right_axis)
            self.ls_query_packs.append(pack)
        
if __name__ == "__main__":
    import config2
    cfg = config2.backend_settings
    app = tk.Tk()
    panel = QueryPanel(app,config=cfg,panel_name="Right Axis")
    panel.grid(padx=20)
    app.mainloop()