# -*- coding: utf-8 -*-
"""
Created on Wed Jun 27 16:33:14 2018

@author: Justin H Kim
"""
try:
    import Tkinter as tk
    import tkFont
    import ttk
except ImportError:  # Python 3
    import tkinter as tk
    import tkinter.ttk as ttk

# Tkinter Modules
try:
    import Tkinter as tk
    import tkFont
    import ttk
except ImportError:  # Python 3
    import tkinter as tk
    import tkinter.ttk as ttk

# Standard Modules
from pprint import pprint
import pickle
import numpy as np

# Project Modules
from appwidget import AppWidget
    
class DataTable(AppWidget):
    def __init__(self,parent,controller,config,dbvar=None):
        self.widget_name = "datatable"
        super().__init__(parent,controller,config,dbvar)
#        self["width"] = 60
            
        self.nav_tree = ttk.Treeview(self)
        self.scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.nav_tree.xview)
        self.nav_tree.configure(xscrollcommand=self.scroll.set)    
        
        self.pack_propagate(0)
        self.scroll.pack(side="bottom", fill="x")
        self.nav_tree.pack(side="top", fill="both", expand=True)        
        self.log("DataTable.py init")
# API
#   We use the "cfg" attribute present in all defaultengines as a convenient way
#   to store and access the latest "mrp". 
    def update_table(self,mrp):
        self.set_build_config(mrp)    
        if self.nav_tree is not None:
            self.nav_tree.destroy()
            self.scroll.destroy()
            
        self.nav_tree = ttk.Treeview(self, columns=self.get_cfg_val("line_labels"),show="headings")
        self.scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.nav_tree.xview)
        self.nav_tree.configure(xscrollcommand=self.scroll.set)    
        
        self.pack_propagate(0)
        self.scroll.pack(side="bottom", fill="x")
        self.nav_tree.pack(side="top", fill="both", expand=True)   

        for header in self.get_cfg_val("line_labels"):
            self.nav_tree.heading(header,text=header,
                                  command=lambda c=header: self.sortby(self.nav_tree,c,1))
            self.nav_tree.column(header, minwidth=20, anchor="center", stretch=False,
                                 width=125)
         
        for row_values in self.engine.get_rows_of_data(self.get_cfg_val("data_list_of_lists")):
            self.nav_tree.insert("", "end", values=row_values)
            
                    