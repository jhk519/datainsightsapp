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
    
from pprint import pprint
import pickle

# Project Modules
from default_engines import AnalysisPageEngine
import controlpanel
import graphframe
import datatable

class AnalysisPage(tk.Frame):
    def __init__(self,parent,controller=None,engine="default",config=None,dbvar=None):
        super().__init__(parent)
        self.parent = parent
        
        if not controller:
            self.controller = parent
        else:
            self.controller = controller
            
        if str(engine) == "default":
            self.engine = AnalysisPageEngine()
        else:
            self.engine = engine      
            
        self.config_key = "analysispage_config"    
        if config:
            self.engine.set_build_config(raw_config = config[self.config_key])
            
        if dbvar:
            self.engine.set_dbvar(dbvar)

#        BUILD GUI
        self.graph_frame = graphframe.GraphFrame(self)
        self.graph_frame.grid(row=0, rowspan=2,column=0, sticky="NW")

        self.control_panel = controlpanel.ControlPanel(self,config=config)
        self.control_panel.grid(row=0, column=1, sticky="new", padx=15)

        self.datatable = datatable.DataTable(self,config=config)
        self.datatable.grid(row=1,column=1,sticky="nw")
           
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

# ================================================================
# ================================================================
#       API
# ================================================================
# ================================================================
        
    def set_dbvar(self,new_dbvar):
        self.engine.set_dbvar(new_dbvar)    
        
    def set_cfgvar(self,new_cfgvar):
        self.engine.set_build_config(raw_config = new_cfgvar[self.config_key])
        self.control_panel.set_cfgvar(new_cfgvar)
          
    def search_queries(self,search_pack_from_console):
        analysis_pack = self.engine.get_results_packs(search_pack_from_console)
        self.search_results = self.graph_frame.update_graph(analysis_pack)
        if self.search_results:
            self.datatable.update_table(self.search_results)
            
    def export_excel(self):
        export_pack = self.engine.get_export_excel_pack(self.search_results)
        fullname,sheetname,newdf = export_pack
        if not fullname:
            file_location = tk.filedialog.asksaveasfilename()
            fullname = file_location + self.engine.time_str() + ".xlsx"
        newdf.to_excel(fullname, sheet_name=sheetname)    

    def export_png(self):
        if self.engine.get_cfg_val("auto_name_exports"):
            fullname = self.engine.get_export_full_name(self.search_results["title"],
                                                        ftype="image")
        else: 
            file_location = tk.filedialog.asksaveasfilename()
            fullname = file_location + self.engine.time_str() + ".png"
        self.graph_frame.my_figure.savefig(fullname)         
        
if __name__ == "__main__":
    import config2
    controls_config = config2.backend_settings
    dbfile =  open(r"databases/DH_DBS.pickle", "rb")
    dbs = pickle.load(dbfile)  
    app = tk.Tk()
    analysispage = AnalysisPage(app,config=controls_config,dbvar=dbs)
    analysispage.grid(padx=20)
    app.mainloop()        
