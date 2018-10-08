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
        self.xscroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.nav_tree.xview)
        self.yscroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.nav_tree.yview)
        
        self.nav_tree.configure(xscrollcommand=self.xscroll.set)    
        self.nav_tree.configure(yscrollcommand=self.yscroll.set)    
        
        self.pack_propagate(0)
        self.xscroll.pack(side="bottom", fill="x")
        self.yscroll.pack(side="right", fill="y")
        
        self.nav_tree.pack(side="top", fill="both", expand=True)        
        self.log("DataTable.py init")
# API
#   We use the "cfg" attribute present in all defaultengines as a convenient way
#   to store and access the latest "mrp". 

    def update_table(self,table_pack):
        self.log("Updating Datatable.")
        self.set_build_config(table_pack)    
        if self.nav_tree is not None:
            self.nav_tree.destroy()
            self.yscroll.destroy()
            self.xscroll.destroy()
        
        self.nav_tree = ttk.Treeview(self, columns=self.get_cfg_val("line_labels"),show="headings")
        self.xscroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.nav_tree.xview)
        self.yscroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.nav_tree.yview)
        
        self.nav_tree.configure(xscrollcommand=self.xscroll.set)    
        self.nav_tree.configure(yscrollcommand=self.yscroll.set)      

        for header in self.get_cfg_val("line_labels"):
            self.nav_tree.heading(header,text=header,
                                  command=lambda c=header: self.sortby(self.nav_tree,c,1))
            self.nav_tree.column(header, minwidth=20, anchor="e", stretch=False,
                                 width=125)
         
        for row_values in self.engine.get_rows_of_data(self.get_cfg_val("data_lists")):
            self.nav_tree.insert("", "end", values=row_values)
            
        self.pack_propagate(0)
        
        self.xscroll.pack(side="bottom", fill="x")
        self.yscroll.pack(side="right", fill="y")
        
        self.nav_tree.pack(side="top", fill="both", expand=True)            
        
        self.log("Completed updating datatable.")
            
                    