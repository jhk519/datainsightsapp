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
import copy    
import logging
import configparser    
import pprint as PRETTYPRINTTHIS

# Project Mpdules
import config2
from analysispage import AnalysisPage
from productviewer import ProductViewer
from databasemanager import DBManager
from settingsframe import SettingsFrame

class DataInsightsApp(tk.Tk):
    def __init__(self, account, config, ver=None):
        
        logger = logging.getLogger(__name__)
        logging.info("DataInsightsApp init started. ")        
        super().__init__()
        logging.info("super init completed.")
        self.account = account
        logging.info("Account id = %s",self.account)
        
#       APP-VARS
#        self.ini_cfg = ini_cfg
        self.cfg = config
        self.analysisframes = []
        
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
#        self.settings_frame = SettingsFrame(self.notebook,self.ini_cfg)
#        self.notebook.add(self.settings_frame,text="Settings")
#        self.fcfg = self.settings_frame.settings_dict
        
#       DATA MANAGER PAGE INIT 
        self.dbmanager = DBManager(self.notebook, self, config = self.cfg["dbmanager_config"])
        self.notebook.add(self.dbmanager,text="Data")  

#        PRODUCT VIEWER PAGE INIT
        self.product_viewer_page = ProductViewer(self.notebook, self, dbvar=self.dbmanager.get_dbsdata())
        self.notebook.add(self.product_viewer_page,text="Product Viewer")
        
#       ANALYSIS PAGE INIT
        ap = AnalysisPage(self.notebook, self, engine="default",
            config = self.cfg["analysispage_config"], dbvar = self.dbmanager.get_dbsdata())
        self.analysisframes.append(ap)
        self.notebook.add(ap, text="Analysis")

        self.notebook.grid(row=0, column=0, sticky="ENSW")
        self.notebook.enable_traversal()
        self.notebook.select(self.dbmanager)
        
if __name__ == "__main__":
    
    logging.basicConfig(filename='debug2.log',level=logging.DEBUG)
    logging.info("datainsightsapp module initialized...")
    
#    fcfg_parser = configparser.ConfigParser()
#    fcfg_parser.read("fcfg.ini")
#    logging.info("Loaded front-config of length %s.", len(fcfg))
    
    config = config2.backend_settings
#    logging.info("Loaded back-config of length %s.", len(bcfg))
    
    logging.info("Deepcopy of header_reference_dict made.")
    
    logging.info("Initializing app...")
    ver = "v0.2.9.4 - 2018/06/25"
    app = DataInsightsApp("admin",config,ver=ver)
    
    app.state("zoomed")
    app.title("Data Insights App")
    app.mainloop()
    logging.info("app.mainloop() terminated.")
    
