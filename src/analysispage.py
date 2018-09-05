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
import pickle
import logging
import datetime

# Project Modules
from appwidget import AppWidget
import querypanel
import graphframe
import datatable

class AnalysisPage(AppWidget):
    def __init__(self,parent,controller,config,dbvar=None):
        self.widget_name = "analysispage"
        super().__init__(parent,controller,config,dbvar)   

#       UX VARIABLES     
        self.graph_frame = graphframe.GraphFrame(self)
        self.graph_frame.grid(row=0, rowspan=2,column=0, sticky="NSW")

        self.b_queries_pane(config),
        self.config_chain.append(self.query_panel)
        self.b_menu_pane()  
        
        self.datatable = datatable.DataTable(self,self,config,dbvar)
        self.datatable.grid(row=2,column=0,sticky="new")
           
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

# ================================================================
# ================================================================
#       API
# ================================================================
# ================================================================       
        
    def request_and_graph_data(self,request_pack):
        self.log("***START*** search query.")
        data_pack = self.get_data(request_pack)
        if not data_pack:
            self.bug("Received False from self.get_data")
            return
        else:
            self.last_selection_pack = request_pack
            self.last_data_pack = data_pack
            self.last_graph_pack = self.draw_graph(data_pack)
            
    def draw_graph(self,data_pack):
        merged_results_pack = self.graph_frame.update_graph(data_pack)
        if not merged_results_pack:
            return False
        else:
            return merged_results_pack
        
    def get_data(self,request_pack):
#        pprint(request_pack)
#        print("----------")
        
        init_data = self.engine.get_results_packs(request_pack)
#        pprint(init_data)
#        print("---")
        if init_data == "No Date Data":
            self.bug("No results for this date range.")
            title = "No Results for this date range."
            text ="No results for this date range."
            self.create_popup(title,text) 
            return False
        elif init_data is None:
            self.bug("self.engine.get_results_packs returned None")
            title = "Search Error"
            text ="Error, please send Debug log to admin."
            self.create_popup(title,text)  
            return False
        return init_data

    def export_excel(self):
        export_pack = self.engine.get_export_excel_pack(self.last_graph_pack)
        fullname,sheetname,newdf = export_pack
        if not fullname:
            file_location = tk.filedialog.asksaveasfilename()
            fullname = file_location + self.engine.time_str() + ".xlsx"
        newdf.to_excel(fullname, sheet_name=sheetname)    

    def export_png(self,outdir=None):
        """
        Currently called by controlpanel's export function
        and as a helper for send_to_multigrapher
        """
        if self.engine.get_cfg_val("auto_name_exports"):
            fullname = self.engine.get_export_full_name(self.last_graph_pack["title"],
                                                        ftype="image",
                                                        outdir=outdir)
        else: 
            file_location = tk.filedialog.asksaveasfilename()
            fullname = file_location + self.engine.time_str() + ".png"
        self.graph_frame.my_figure.savefig(fullname) 
        self.log(fullname)
        return fullname

    def send_to_multigrapher(self,slot = None):
        self.log("Send to multigrapher called.")
        slot = None
        fullname = self.export_png(outdir="exports\multigrapher")        
        self.controller.send_to_multigrapher(fullname,self.last_selection_pack,slot)                     

    def _sortby(self, tree, col, descending):
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
        tree.heading(
            col, command=lambda col=col: self.sortby(
                tree, col, int(
                    not descending)))   

    def b_queries_pane(self,config=None):
        self.query_panel = querypanel.QueryPanel(
            self,
            self,
            config)
        self.query_panel.grid(row=0, column=1, sticky="wn")
            
    def b_menu_pane(self):
        self.menu_pane = ttk.Labelframe(
            self, text="Controls")
        self.menu_pane.grid(row=1,column=1,sticky="NW")        

        self.export_excel_button = ttk.Button(
            self.menu_pane,
            command=self.export_excel,
            text="Export Data to Excel")
        self.export_excel_button.grid(
            row=1, column=1, padx=5, pady=2, sticky="w")
        
        self.export_graph_button = ttk.Button(
            self.menu_pane,
            command=self.export_png,
            text="Export Graph",
            state="normal")
        self.export_graph_button.grid(
            row=1, column=2, padx=5, pady=2, sticky="w")   
        
        self.send_to_multigrapher_button = ttk.Button(
            self.menu_pane,
            command=self.send_to_multigrapher,
            text="Send to Multigrapher",
            state="normal")
        self.send_to_multigrapher_button.grid(
            row=1, column=3, padx=5, pady=2, sticky="w")            
        
if __name__ == "__main__":
 
    analysispage = AnalysisPage(app,app,controls_config,dbvar=dbs)
    analysispage.grid(padx=20)
    app.mainloop()        
