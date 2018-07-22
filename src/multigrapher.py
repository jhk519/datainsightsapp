# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 19:42:58 2018

@author: Justin H Kim
"""
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

# Non-standard Modules
from PIL import ImageTk

# Project Modules
from default_engines import MultiGrapherEngine

class MultiGrapher(tk.Frame):
    def __init__(self,parent,controller=None,engine="default",config=None):
        super().__init__(parent)
        self.parent = parent
        if not controller:
            self.controller = parent
        else:
            self.controller = controller
            
        if str(engine) == "default":
            self.engine = MultiGrapherEngine()
        else:
            self.engine = engine    
            
        self.config_key = "multigrapher_config"    
        if config:
            self.engine.set_build_config(raw_config = config[self.config_key])
                        
#        self.time_created = self.engine.time_str()
#        self.online_loaded = tk.IntVar(value=0)
        
#        self.db_panel_packs = []
#        self._build_top_frame()
#        self._build_middle_frame()
        
if __name__ == "__main__":
    import config2
    dbcfg = config2.backend_settings
    app = tk.Tk()
    test_widget = DBManager(app, config=dbcfg)
    test_widget.grid(padx=20)
    app.mainloop()          