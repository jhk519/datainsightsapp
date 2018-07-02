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
from default_engines import DataTableEngine
    
class DataTable(ttk.Labelframe):
    def __init__(self,parent,controller=None,engine="default",config=None):
        super().__init__(parent)
        self.parent = parent
        if not controller:
            self.controller = parent
        else:
            self.controller = controller
            
        if str(engine) == "default":
            self.engine = DataTableEngine()
        else:
            self.engine = engine         
            
        self.config_key = None   
        if config and self.config_key:
            self.engine.set_build_config(raw_config = config[self.config_key]) 
            
        self.nav_tree = ttk.Treeview(self)
        self.nav_tree.pack()

# API
#   We use the "cfg" attribute present in all defaultengines as a convenient way
#   to store and access the latest "mrp". 
    def update_table(self,mrp):
        self.engine.set_build_config(mrp)    
        if self.nav_tree is not None:
            self.nav_tree.destroy()
            
        self.nav_tree = ttk.Treeview(self, columns=self.engine.get_cfg_val("line_labels"))
        self.nav_tree.pack(fill="x")

        for header in self.engine.get_cfg_val("line_labels"):
            self.nav_tree.heading(header,text=header,
                                  command=lambda c=header: self.sortby(self.nav_tree,c,1))
            self.nav_tree.column(header, minwidth=20, anchor="center", stretch=False,
                                 width=125)
          
        for row_values in self.engine.get_rows_of_data():
            self.nav_tree.insert("", "end", values=row_values)

        self.nav_tree.column("#0", width=1)
        
#   UX EVENT HANDLERS AND HELPERS
    def sortby(self, tree, col, descending):
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
        tree.heading(col,
                     command=lambda col=col: self.sortby(tree, col, int(not descending)))                      
                    