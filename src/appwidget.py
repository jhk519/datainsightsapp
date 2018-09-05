# -*- coding: utf-8 -*-
"""
Created on Thu Aug 30 12:59:56 2018

@author: Justin H Kim
"""
import tkinter as tk
import tkinter.ttk as ttk
import logging

import default_engines
import datetime

from pprint import pprint

class AppWidget(tk.Frame):
    def __init__(self,parent,controller,config,dbvar):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        
        self.config_chain = []
            
        self.log = logging.getLogger(self.widget_name).info
        self.log("{} Init.".format(__name__ + "-" + self.widget_name))
        self.bug = logging.getLogger(self.widget_name).debug   
        
        if self.widget_name == "dbmanager":
            self.engine = default_engines.DBManagerEngine()
        elif self.widget_name == "analysispage":
            self.engine = default_engines.AnalysisPageEngine()
        elif self.widget_name == "controlpanel":
            self.engine = default_engines.ControlPanelEngine()
        elif self.widget_name == "querypanel":
            self.engine = default_engines.QueryPanelEngine()
        elif self.widget_name == "datatable":
            self.engine = default_engines.DataTableEngine()
        elif self.widget_name == "productviewer":
            self.engine = default_engines.ProductViewerEngine()
        elif self.widget_name == "multigrapher":
            self.engine = default_engines.MultiGrapherEngine()
        elif self.widget_name == "settingsmanager":
            self.engine = default_engines.SettingsManagerEngine()
            self.engine.set_build_config(raw_config = config) 
            return
        else:
            self.bug("{} does not match any option in default_engines.".format(self.widget_name))
           
        try:
            config[self.widget_name]
        except KeyError:
            self.bug("{} not in config. Check config2 file.".format(self.widget_name))
        else:
            self.engine.set_build_config(config[self.widget_name]) 
            
        if dbvar:
            self.engine.set_dbvar(dbvar)    
        return
    
    #   API
    def get_dbvar(self):
        return self.engine.get_dbvar()
    
    def set_dbvar(self,new_dbvar):
        self.engine.set_dbvar(new_dbvar)
        
    def set_cfgvar(self,new_cfgvar):
        self.log("Changing cfg.")
        self.engine.set_build_config(new_cfgvar[self.widget_name]) 
        for widget in self.config_chain:
            widget.set_cfgvar(new_cfgvar)
        
    def create_popup(self,title,text,firstb=None,secondb=None):
        self.popup = tk.Toplevel()
        self.popup.title(title)
        tk.Message(self.popup,text=text).pack()
        if firstb:
            tk.Button(self.popup,text=firstb[0],command=firstb[1]).pack()
        if secondb:
            tk.Button(self.popup,text=secondb[0],command=secondb[1]).pack()
            return
        tk.Button(self.popup,text="OK",command=self.popup.destroy).pack()
        return
        