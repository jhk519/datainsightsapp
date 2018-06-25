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
import queries
   
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
        self.max_num_queries = 5
        self.scope_var = tk.StringVar()
        self.scope_extra_var = tk.StringVar()
        self.metric_var = tk.StringVar() 
        self.ls_query_packs = []
        
#        Build Skeleton UI
        self.__build_skeleton()
        
#       Set Build Config and Update
        if config:
            self.engine.set_build_config(raw_config = config)
            self._update_scope_menu("Graph")
            self._config_scope_extra()
            self._update_metrics_menu(self.scope_var.get())
            self._update_queries(self.metric_var.get()) 
            
    def __build_skeleton(self):
#        Build Scope (No Extra)
        self.scope_title= ttk.Label(self, text="Scope")
        self.scope_title.grid(row=0, column=0, sticky="w", padx=0)
        
        self.scope_menu = ttk.Combobox(self, textvariable=self.scope_var)
        self.scope_menu.grid(row=1, column=0, columnspan=2, sticky="w",padx=5)  
        self.scope_menu.bind('<<ComboboxSelected>>',self._scope_changed)  
        self.scope_menu["state"] = "readonly"
        
        self.extra_entry_label = ttk.Label(self)
        self.extra_entry_label.grid(row=0, column=2, sticky="w", padx=25) 
        
        self.extra_widget = ttk.Entry(self, width=15, textvariable=self.scope_extra_var)
        self.extra_widget.grid(row=1, column=2, padx=25, pady=2, sticky="w")
        self.extra_widget.grid_remove()
        
#       Build Metric
        self.metric_title = ttk.Label(self, text="Metric")
        self.metric_title.grid(row=2,column=0,sticky="w",padx=0,pady=(7,0))

        self.metric_menu = ttk.Combobox(self, textvariable=self.metric_var)
        self.metric_menu.grid(row=3, column=0, columnspan=2,pady=(0, 7),  sticky="w", padx=5)
        
        self.metric_menu.bind('<<ComboboxSelected>>',self._metric_changed)
        self.metric_menu["state"] = "readonly"
        
#       Build Query Boxes
        try:
            self.controller.check_valid
        except AttributeError:
            print("Not using valid controller")
            print(str(self.controller)," Not Suitable for Callback")
            query_check_callback = lambda: print("No Suitable Callback for Query Command")         
        else:
            if self.controller.check_valid == "DataInsightsApp_ControlPanel":
                query_check_callback = lambda: self.controller.check_autosearch()            
        for index in range(0,self.max_num_queries):
            stvar_check_var = tk.StringVar()
            temp_checkbutton = ttk.Checkbutton(self,text="Default", variable=stvar_check_var,
                                               onvalue="OnValue", offvalue="OffValue",
                                               command=query_check_callback
                                               )
            temp_checkbutton.grid(row=index + 4, column=0, sticky="w", padx=5, pady=5)
            
            temp_choose_color_button = tk.Button(self,width=1,
                                 command=lambda index=index:self._choose_colors(index))
            temp_choose_color_button.grid(row=index+4,column=1,sticky="e",padx=(5,0),
                pady=5)
            temp_choose_color_button["background"] = "black"   
            pack = (stvar_check_var,temp_checkbutton,temp_choose_color_button)
            self.ls_query_packs.append(pack)
            
#            UI UPDATE HELPERS
            
    def _update_scope_menu(self,page):
        self.scope_menu["values"] = self.engine.get_scopes(page)
        self.scope_menu.current(0)
        
    def _config_scope_extra(self):
        scope = self.scope_var.get()
        extra_cfg = self.engine.get_extra(scope)
        
        if extra_cfg:
            self.extra_entry_label.grid()
            self.extra_entry_label["text"] = extra_cfg["text"]
            self.extra_widget.grid()
        else:
            self.extra_widget.grid_remove()
            self.extra_entry_label.grid_remove()          

    def _update_metrics_menu(self,scope):
        self.metric_menu["values"] = self.engine.get_metrics(scope)
        self.metric_menu.current(0)
        
    def _update_queries(self, metric):
        req_queries = self.engine.get_queries(metric)
        available_colors = self.engine.get_colors_preferred()

        try:
            self.controller.hold_y_var
        except AttributeError:
            print("Not using valid controller")
            print(str(self.controller)," Not Suitable for Callback")      
        else:     
            self.controller.hold_y_var.set(False)
            if self.engine.should_exclude(metric) == "exclude":
                self.controller.exclude_panels(True, self.panel_name)
            else:
                self.controller.exclude_panels(False, self.panel_name) 

        for index,pack in enumerate(self.ls_query_packs):
            checkvar,checkbox,colorbutton = pack[0],pack[1],pack[2]
            
            checkvar.set("OffValue")
            checkbox.configure(text="",state="disabled")
                            
            if index < len(req_queries):
                colorx = index
                if self.panel_name == "Right Axis":
                    colorx = index + 4
                try:
                    available_colors[index]
                except IndexError:
                    colorx = index - 4
                checkbox.configure(state="readonly",text=req_queries[index],
                                   onvalue=req_queries[index])
                colorbutton.configure(background=available_colors[colorx])
        self.ls_query_packs[0][1].invoke()   

#   UX EVENT FUNCTIONS        
    def _scope_changed(self,event=None):
        self._config_scope_extra()
        self._update_metrics_menu(self.scope_var.get())
        self._update_queries(self.metric_var.get())  
        
    def _metric_changed(self,event=None):
        self._update_queries(self.metric_var.get())
        
    def _choose_colors(self, number):
        pack = self.ls_query_packs[number]
        colorbutton = pack[2]
        colorbutton["background"] = colorchooser.askcolor()[1]
        
#   API
    def toggle_enabled(self, setto=None):
        if not setto is None:
            self.enabled_state = setto
            if setto:
                self.scope_menu["state"] = "readonly"
                self.metric_menu["state"] = "readonly"
                for query_pack in self.ls_query_packs:
                    if not query_pack[1]["text"] == "":
                        query_pack[1]["state"] = "normal"
            else:
                self.scope_menu["state"] = "disabled"
                self.metric_menu["state"] = "disabled"
                for query_pack in self.ls_query_packs:
                    query_pack[1]["state"] = "disabled"
        elif setto is None:
            if self.enabled_state:
                self.enabled_state(False)
            else:
                self.enabled_state(True)
                
    def get_selection_pack(self):
        scope = self.scope_var.get()
        extra = self.scope_extra_var.get()
        metric = self.metric_var.get()
        pack = {"enabled":self.enabled_state,
                "scope":scope,
                "extra":extra,
                "metric":metric,
                "queries_list":[]}
        
        for query_pack in self.ls_query_packs:
            if not query_pack[0].get() == "OffValue":
                pack["queries_list"].append((query_pack[0].get(),query_pack[2]["background"]))          
        return pack     


        
if __name__ == "__main__":
    import config2
    cfg = config2.backend_settings["analysispage_config"]["controls_config"]["queries_config"]
    app = tk.Tk()
    panel = QueryPanel(app,config=cfg,panel_name="Right Axis")
    panel.grid(padx=20)
    app.mainloop()