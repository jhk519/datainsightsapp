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
from pprint import pprint as PRETTYPRINT
import pickle
import logging
import datetime
from os import system

# Project Modules
from appwidget import AppWidget
#import newquerypanel
import querypanel
import graphframe
import datatable

class AnalysisPage(AppWidget):
    last_selection_pack= None
    
    def __init__(self,parent,controller,config,dbvar=None):
        self.widget_name = "analysispage"
        super().__init__(parent,controller,config,dbvar)   

        self.graph_table_notebook = ttk.Notebook(self) 
        self.graph_table_notebook.grid(row=0,rowspan=1,column=0,sticky="news")
        
        self.graph_frame = graphframe.GraphFrame(self.graph_table_notebook,self,config)
        self.datatable = datatable.DataTable(self.graph_table_notebook,self,config)
        
        self.graph_table_notebook.add(self.graph_frame,text="Graph")
        self.graph_table_notebook.add(self.datatable,text="Table")
        
        self.query_panel = querypanel.QueryPanel(self,self,config)
        self.query_panel.grid(row=0, column=1, sticky="nw",rowspan=2)
        
        self.menu_pane = ttk.Labelframe(self, text="Controls")
        self.menu_pane.grid(row=1,column=0,sticky="NW")      
        self.b_menu_pane()        
        
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

        self.config_chain.append(self.query_panel)

# ================================================================
# ================================================================
#       API
# ================================================================
# ================================================================       
        
    def request_and_graph_data(self,request_pack):
        self.log("****************** START REQUEST ****************** .")     
        self.last_request_pack = request_pack
        date_list,m_datelist,merged_list_of_plot_tuples = self.engine.get_results_pack(
                request_pack,
                self.get_dbvar(), 
                self.get_cfg_val("event_list"),
                ignore_numbers=self.get_cfg_val("ignore_numbers"))
        
        self.last_graphing_pack,self.last_table_pack  = self.request_pack_to_graphing_and_table_pack(
                request_pack,date_list,merged_list_of_plot_tuples)

        self.log("Received Data")
 
        self.draw_graph(self.last_graphing_pack)
        self.datatable.update_table(self.last_table_pack)
        self.log("****************** END REQUEST ******************")
        
# ================================================================
# ================================================================
#       Helper Functions
# ================================================================
# ================================================================  
            
    def draw_graph(self,graphing_pack):
        self.last_graphing_pack = graphing_pack
        self.graph_frame.update_graph(self.last_graphing_pack )
        
    def request_pack_to_graphing_and_table_pack(self,req_pk,date_list,merged_list_of_plot_tuples):
        # EVENTS
        events_list = []
        if req_pk["graph_options"]["show_events"]:
            events_list = self.engine.get_events_list(self.get_cfg_val("event_list"))
            
        # FORCE-Y AXIS
        force_y_tuple = (req_pk["graph_options"]["force_y_axis"],
                         req_pk["graph_options"]["force_y_axis_min"],
                         req_pk["graph_options"]["force_y_axis_max"])
        

        # GENERATE Y-AXIS TITLE
        y_title_str = "{} ({})".format(req_pk["metric_options"]["metric"],
                                       req_pk["metric_options"]["data_type"])        
        
        # GENERATE X-AXIS TITLE
        if req_pk["x_axis_type"] == "date_series":
            x_title_str = "Date"
            
            if req_pk["result_options"]["aggregation_period"] > 1:
                x_title_str = "{} ({} of {}-Day Periods)".format(
                    x_title_str,
                    req_pk["result_options"]["aggregation_type"],
                    req_pk["result_options"]["aggregation_period"])
                
        # GENERATE CHART TITLE
        title_str = req_pk["metric_options"]["metric"]
        if not req_pk["metric_options"]["metric_type"] == "None": 
            title_str = "{} ({})".format(req_pk["metric_options"]["metric"],
                                        req_pk["metric_options"]["metric_type"])
        if not req_pk["metric_options"]["breakdown"] == "None":
            title_str = "{} By {}".format(title_str,
                                          req_pk["metric_options"]["breakdown"])  

        title_str = "{} of {}".format(req_pk["metric_options"]["data_type"],
                                      title_str)              
            
        grph_pck  = {
            "axis":req_pk["graph_options"]["axis"],
            "start":date_list[0],
            "end":date_list[-1],
            "met": req_pk["metric_options"]["metric"],
            "gtype": req_pk["x_axis_type"],
            "str_x": x_title_str,
            "str_y": y_title_str,
            "line_labels":[plot_tuple[0] for plot_tuple in merged_list_of_plot_tuples],
            "x_data": date_list,
            "y_data": [plot_tuple[1] for plot_tuple in merged_list_of_plot_tuples],
            "color":req_pk["graph_options"]["color"],
            "breakdown_colors": self.get_cfg_val("breakdown colors").split("-"),
            "title": title_str,
            "linestyles":req_pk["graph_options"]["line_style"],
            "event_dates":events_list,
            "force_y": force_y_tuple,
        }   
        
        line_labels = [grph_pck["str_x"]] + [plot_tuple[0] for plot_tuple in merged_list_of_plot_tuples]
        data_lists = [grph_pck["x_data"]] + [plot_tuple[1] for plot_tuple in merged_list_of_plot_tuples]
        
        table_pack = {
            "line_labels":line_labels,
            "data_lists": data_lists,
            "sheet_title": req_pk["metric_options"]["breakdown"],
            "table_title": title_str
        }

        return grph_pck, table_pack         
        
# ================================================================
# ================================================================
#       UX FUNCTIONS
# ================================================================
# ================================================================          

    def export_excel(self):
        if self.get_cfg_val("automatic search export"):
            fullname = self.get_export_full_name(self.last_graphing_pack["title"])
        else:    
            fullname = None        
        sheetname,newdf = self.engine.get_export_excel_pack(self.last_table_pack)
        if not fullname:
            file_location = tk.filedialog.asksaveasfilename()
            fullname = file_location + self.get_time_str() + ".xlsx"
        newdf.to_excel(fullname, sheet_name=sheetname)    
        if self.get_cfg_val("automatically open excel exports"):
            system('start excel.exe "%s"' % (fullname))

    def export_png(self,outdir=None):
        """
        Currently called by controlpanel's export function
        and as a helper for send_to_multigrapher
        """
        if self.get_cfg_val("automatic search export"):
            fullname = self.get_export_full_name(self.last_graphing_pack["title"],
                                                        ftype="image",
                                                        outdir=outdir)
        else: 
            file_location = tk.filedialog.asksaveasfilename()
            fullname = file_location + self.get_time_str() + ".png"
        self.graph_frame.my_figure.savefig(fullname, dpi=self.graph_frame.my_figure.dpi) 
        self.log(fullname)
        return fullname

    def send_to_multigrapher(self):
        self.log("Send to multigrapher called.")
        slot = None
        fullname = self.export_png(outdir="exports\multigrapher")        
        self.controller.send_to_multigrapher(fullname,self.last_request_pack,slot)      
        
    def receive_new_title(self):
        title = "Edit Graph Title"
        text ="Please Enter New Title."
        self.create_popup(title,text,entrycommand=self.new_title_listener)  

# ================================================================
# ================================================================
#       UX HELPERS
# ================================================================
# ================================================================      

    def new_title_listener(self):
        try: 
            self.last_graphing_pack["title"]
        except TypeError:
            self.bug("Received new title but self.last_selection_pack is None.")
        else:
            self.last_graphing_pack["title"] = self.popupentryvar.get()
            self.draw_graph(self.last_graphing_pack)
        self.popup.destroy()        
        
    def b_menu_pane(self):
 
        self.export_excel_button = ttk.Button(
            self.menu_pane,
            command=self.export_excel,
            text="Export Data to Excel")
        self.export_excel_button.grid(
            row=0, column=0, padx=5, pady=2, sticky="w")
        
        self.export_graph_button = ttk.Button(
            self.menu_pane,
            command=self.export_png,
            text="Export Graph",
            state="normal")
        self.export_graph_button.grid(
            row=0, column=1, padx=5, pady=2, sticky="w")   
        
        self.send_to_multigrapher_button = ttk.Button(
            self.menu_pane,
            command=self.send_to_multigrapher,
            text="Send to Multigrapher",
            state="normal")
        self.send_to_multigrapher_button.grid(
            row=0, column=2, padx=5, pady=2, sticky="w") 

        self.new_title_button = ttk.Button(
            self.menu_pane,
            command=self.receive_new_title,
            text="Change Title",
            state="normal")
        self.new_title_button.grid(
            row=0, column=3, padx=5, pady=2, sticky="w")  
        
if __name__ == "__main__":
    logname = "debug-{}.log".format(datetime.datetime.now().strftime("%y%m%d"))
    ver = "v0.2.10.7 - 2018/07/22"
    
    logging.basicConfig(filename=r"debug\\{}".format(logname),
        level=logging.DEBUG, 
        format="%(asctime)s %(filename)s:%(lineno)s - %(funcName)s() %(levelname)s || %(message)s",
        datefmt='%H:%M:%S')
    logging.info("-------------------------------------------------------------")
    logging.info("DEBUGLOG @ {}".format(datetime.datetime.now().strftime("%y%m%d-%H%M")))
    logging.info("VERSION: {}".format(ver))
    logging.info("AUTHOR:{}".format("Justin H Kim"))
    logging.info("-------------------------------------------------------------")
    import config2
    controls_config = config2.backend_settings
    dbfile =  open(r"databases/DH_DBS.pickle", "rb")
    dbs = pickle.load(dbfile)  
    app = tk.Tk()    
    app.state("zoomed")
    analysispage = AnalysisPage(app,app,controls_config,dbvar=dbs)
    analysispage.grid(padx=20)
    app.mainloop()        
