# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 18:22:14 2018

@author: Justin H Kim
"""

# Tkinter Modules
try:
    import Tkinter as tk
    import tkFont
    import ttk
except ImportError:  # Python 3
    import tkinter as tk
    import tkinter.font as tkFont
    import tkinter.ttk as ttk
    
# Standard Modules    
import logging   
import datetime
import pprint as PRETTYPRINTTHIS

# Project Mpdules
import config2
from analysispage import AnalysisPage
from productviewer import ProductViewer
from databasemanager import DBManager
from settingsmanager import SettingsManager
from multigrapher import MultiGrapher

class DataInsightsApp(tk.Tk):
    def __init__(self, account, init_config, ver=None):
        logger = logging.getLogger(__name__)
        self.log = logging.getLogger(__name__).info
        self.bug = logging.getLogger(__name__).debug
        
        logging.info("DataInsightsApp init started.")        
        super().__init__()
        self.log("Super init completed.")
        self.account = account
        self.log("Account id = {}".format(self.account))
            
#       APP-VARS
        self.init_cfg = init_config
        self.analysispages = []
        
#        APP DETAILS
        self.app_version_text = ver
        self.developers_text = "Developed by Justin H Kim."

#        BUILD GUI
        self._build_mainframe()
        self._populate_notebook()
         
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)
                
        self.update()

    def _build_mainframe(self):
        self.mainframe = tk.Frame(self)
        self.mainframe.grid(row=0,column=0,sticky="ensw")
        self.mainframe.columnconfigure(0,weight=1)
        self.mainframe.rowconfigure(0,weight = 1)
        self.notebook = ttk.Notebook(self.mainframe)
        
    def _populate_notebook(self):
#       SETTINGS MANAGER PAGE INIT
        self.settingsmanager = SettingsManager(self.notebook, self, self.init_cfg)
        self.notebook.add(self.settingsmanager,text="Settings",sticky="nesw")
        
        curr_config = self.settingsmanager.get_config()
        
#       DATA MANAGER PAGE INIT 
        self.dbmanager = DBManager(self.notebook, self, curr_config)
        self.notebook.add(self.dbmanager,text="DB Manager",sticky="nsew")  

#       PRODUCT VIEWER PAGE INIT
        self.product_viewer_page = ProductViewer(self.notebook,self,curr_config,
                                                 dbvar = self.dbmanager.get_dbvar())
        self.notebook.add(self.product_viewer_page,text="Product Viewer")
        
#       ANALYSIS PAGE INIT
        ap = AnalysisPage(self.notebook, self, curr_config, dbvar = self.dbmanager.get_dbvar())
        self.analysispages.append(ap)
        self.notebook.add(ap, text="Analysis",sticky="nsew")


        
#       MULTIGRAPHER INIT
        self.multigrapher = MultiGrapher(self.notebook,self, curr_config)
        self.notebook.add(self.multigrapher,text="MultiGrapher",sticky="snew")
        
        
#       FINALIZE NOTEBOOK
        self.notebook.grid(row=0, column=0, sticky="ENSW")
        self.notebook.enable_traversal()
        self.notebook.select(self.dbmanager)
        
        
#       API 
    def propagate_db_var_change(self,new_dbvar):       
#        Required when DBManager does full resets of its dbvar, meaning the 
#        correct dbvar now has a new id.         
        self.product_viewer_page.set_dbvar(new_dbvar)
        for ap in self.analysispages:
            ap.set_dbvar(new_dbvar)
            
    def propagate_cfg_var_change(self,new_cfgvar):
        self.dbmanager.set_cfgvar(new_cfgvar)
        self.product_viewer_page.set_cfgvar(new_cfgvar)
        for ap in self.analysispages:
            ap.set_cfgvar(new_cfgvar)
            
    def send_to_multigrapher(self,path,slot):
        self.log("Send_to_multigrapher for path: {} AND slot: {}".format(path,slot))
        self.multigrapher.receive_image(path,slot)
        
if __name__ == "__main__":
    
    logname = "debug-{}.log".format(datetime.datetime.now().strftime("%y%m%d"))
    ver = "v0.2.10.7 - 2018/07/22"
    
    logging.basicConfig(filename=r"debuglogs\\{}".format(logname),
        level=logging.DEBUG, 
        format="%(asctime)s %(name)s:%(lineno)s - %(funcName)s() %(levelname)s || %(message)s",
        datefmt='%H:%M:%S')
    logging.info("-------------------------------------------------------------")
    logging.info("DEBUGLOG @ {}".format(datetime.datetime.now().strftime("%y%m%d-%H%M")))
    logging.info("VERSION: {}".format(ver))
    logging.info("AUTHOR:{}".format("Justin H Kim"))
    logging.info("-------------------------------------------------------------")
    logging.info("datainsightsapp module initialized...")
    config = config2.backend_settings    
    logging.info("Collected config2.backend_settings")
    
    app = DataInsightsApp("admin",config,ver=ver)
    logging.info("App Initialized...")
    
    app.state("zoomed")
    app.title("Data Insights App - {}".format(ver))
    app.mainloop()
    logging.info("app.mainloop() terminated.")
    
