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
            
        if config:
            self.engine.set_build_config(raw_config = config)  
            
        if dbvar:
            self.engine.set_dbvar(dbvar)

#        BUILD GUI
        self.graph_frame = graphframe.GraphFrame(self)
        self.graph_frame.grid(row=0, column=0, sticky="NW")
        
        controls_config = self.engine.get_controls_cfg()
        self.control_panel = controlpanel.ControlPanel(self,config=controls_config)
        self.control_panel.grid(row=0, column=1, sticky="new", padx=15)

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

    def _auto_set_dates(self, config):
        self.control_panel.set_dates(config)

# ================================================================
# ================================================================
#       API
# ================================================================
# ================================================================
          
    def search_queries(self,search_pack):
        left_results,right_results = self.engine.get_results_packs(search_pack)
        if left_results:
            self.search_results = self.graph_frame.update_graph(
                    left_results,right_results,False)
            
    def export_excel(self):
        export_pack = self.engine.get_export_excel_pack(self.search_results)
        fullname,sheetname,newdf = export_pack
        if not fullname:
            file_location = tk.filedialog.asksaveasfilename()
            fullname = file_location + self.engine.time_str() + ".xlsx"
        newdf.to_excel(fullname, sheet_name=sheetname)    

    def export_png(self):
        if self.engine.should_auto_export:
            fullname = self.engine.get_export_full_name(self.search_results["title"],
                                                        ftype="image")
        else: 
            file_location = tk.filedialog.asksaveasfilename()
            fullname = file_location + self.engine.time_str() + ".png"
        self.graph_frame.my_figure.savefig(fullname)         
        
if __name__ == "__main__":
    import config2
    controls_config = config2.backend_settings["analysispage_config"]
    dbfile =  open(r"databases/DH_DBS.pickle", "rb")
    dbs = pickle.load(dbfile)  
    app = tk.Tk()
    analysispage = AnalysisPage(app,config=controls_config,dbvar=dbs)
    analysispage.grid(padx=20)
    app.mainloop()        
