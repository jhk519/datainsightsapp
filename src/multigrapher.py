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
import logging
import os
import datetime

# Non-standard Modules
import PIL

# Project Modules
from appwidget import AppWidget

class MultiGrapher(AppWidget):
    def __init__(self,parent,controller,config,dbvar=None):
        self.widget_name = "multigrapher"
        super().__init__(parent,controller,config,dbvar)  
            
        self.graph_slots = []
        self.build_tree_frame()
        self.build_graphs_frame()
        
        self.refresh_nav_tree() 
#        pprint(self.engine.get_config())
        self.apply_all_slots_on_page(0)
        
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)   
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)        
  
    def refresh_nav_tree(self):
        cfg = self.engine.get_cfg_val("presetpages")
        self.nav_tree.delete(*self.nav_tree.get_children())
        
        for page in cfg:
            name = page["pagename"]
            pagenameid = self.nav_tree.insert("","end",name,text=name,tags=("page"))
            for index, slot in enumerate(page["slots"]):
                pcode = slot["extra"]
                mirror_days = slot["mirror_days"]
                days_back = slot["days_back"]
                if slot["title"]:
                    title = slot["title"]
                else:
                    title = ""
                
                slottext = "Slot {}".format(str(index))
                slotval = ["","","",title,pcode,days_back,mirror_days]
                slotid = self.nav_tree.insert(pagenameid,"end",pagenameid+"_"+str(index),tags=("slot"),
                                            text=slottext,
                                            values=slotval)

#                leftid = self.nav_tree.insert(slotid,"end",slotid+"_"+"left",text="Left",tags=("axis"))
#                rightid = self.nav_tree.insert(slotid,"end",slotid+"_"+"right",text="Right",tags=("axis"))
                
                for n,query in enumerate(slot["left"]["queries"]):
                    padded_columns = ["Left",query[0],query[1]]
                    self.nav_tree.insert(slotid,"end",slotid+"_L_"+str(n),values=padded_columns,tags=("query"))    
                for n,query in enumerate(slot["right"]["queries"]):
                    padded_columns = ["Right",query[0],query[1]]
                    self.nav_tree.insert(slotid,"end",slotid+"_R_"+str(n),values=padded_columns,tags=("query"))
        self.nav_tree.tag_configure("page",background="#d3d3d3") 
        self.nav_tree.tag_configure("slot",background="#f4f4f4")                   
#        self.nav_tree.tag_configure("axis",background="#f4f4f4")

    def get_TKimage(self,path,size):
          self.log("Resizing to: {}".format(size))
          PILim = PIL.Image.open(path)
          PILim = PILim.resize(size,PIL.Image.ANTIALIAS)
          TKim = PIL.ImageTk.PhotoImage(image=PILim)         
          return TKim      
      
#    def save_all_slots_to_page(self,pageslot):
#        self.controller.send_new_presets(self.engine.get_cfg_val("presetpages"))
      
    def apply_all_slots_on_page(self,pageslot):
        self.log("APPLY ALL SLOTS")
        page =  self.engine.get_cfg_val("presetpages")[pageslot]
        for index,slot_pack in enumerate(page["slots"]):
            self.log("Applying for slot index {}.".format(index ))
            request_pack = self.engine.convert_slot_pack_to_request_pack(slot_pack)
            try:
                self.apply_slot(request_pack,index)
            except TypeError:
                self.bug("erprtwrharhreh")
                    
    def apply_slot(self,request_pack,slotnum):
        path = self.controller.get_graph_path(request_pack)
        slot = self.graph_slots[slotnum]
        self.load_graph_in_slot(path,slot)
    
    def load_graph_in_slot(self,path,slot):
        self.log("Loading path")
        canvas = slot[0]
        canvas.update_idletasks()
        size = 400,250
        im = self.get_TKimage(path,size)
        cimg = canvas.create_image(0, 0, image=im, anchor="nw", tags="IMG")
        slot[1] = im
        slot[2] = path  

    def receive_image(self,path,request_pack,slotnum=None):
        self.log("Received image from path: {} and slotnum {}".format(path,slotnum))
        the_slot = None
        if not slotnum:
            self.log("No slotnum given")
            for index,slot in enumerate(self.graph_slots):
                if not slot[1] == "IMAGE":
                    self.bug("Slot in index: {} skipping because not 'image'.".format(str(index)))
                    continue
                else:
                    the_slot = slot
                    break        

        elif slotnum:
            the_slot = self.graph_slots[slotnum]         
        self.load_graph_in_slot(path,the_slot)
        
        slot_pack = self.engine.convert_request_pack_to_slot_pack(request_pack)
        try:
            self.engine.get_cfg_val("presetpages")[0]["slots"][index] = slot_pack
        except IndexError:
            self.bug("No slot currently in config. Appending to list.")
            self.engine.get_cfg_val("presetpages")[0]["slots"].append(slot_pack)
        self.refresh_nav_tree()
#        pprint(self.engine.get_cfg_val("presetpages"))
        self.controller.send_new_presets(self.engine.get_cfg_val("presetpages"))
        
    def export_multigraph(self):
        self.log("Exporting Stiched Graphs")
        result = PIL.Image.new("RGB", (1620, 1020),"white")
        for index, slot in enumerate(self.slots):
            self.bug("slot[1] == {}, slot[2] == ".format(slot[1],slot[2]))
            if slot[1] == "IMAGE":
              continue
            path = slot[2]
            try:
              img = PIL.Image.open(path)
            except FileNotFoundError:
              self.bug("File Not Found at Path: {}".format(path))
            img.thumbnail((800, 500), PIL.Image.ANTIALIAS)
            y = int(index / 2) *510
            x = int(index % 2) * 805            
            w, h = img.size
            self.bug('index {0} pos {1},{2} size {3},{4}'.format(index, x, y, w, h))
            result.paste(img, (x, y, x + w, y + h))
        result.save(("image.jpg"))
        
    def build_tree_frame(self):
        self.log("Building Tree Frame")
        
        self.tree_frame = ttk.LabelFrame(self,text="Pages")
        self.tree_frame.grid(row=0,column=1,sticky="nesw")
        
        nav_tree_cols = [("AXIS",50),("QUERY",100),("COLOR",50),("NAME",90),("PCODE",80),("DAYS",60),("MIRROR",60)]     
        
        self.nav_tree = ttk.Treeview(self.tree_frame, columns=[aa[0] for aa in nav_tree_cols])
        self.nav_tree.pack()
  
        for header in nav_tree_cols:
            self.nav_tree.heading(header[0],text=header[0], command=lambda c=header: sortby(self.nav_tree, c, 0))
#            resizes
            self.nav_tree.column(header[0],
                                 width=header[1],
                                 anchor="center") 

        self.nav_tree.tag_configure("box_item",background="lightgrey")
        self.nav_tree.column("#0",width=100)
        self.nav_tree.heading("#0",text="Page / Slot")                             
                             
#        self.vsb = ttk.Scrollbar(self.tree_frame,orient="vertical",
#            command=self.nav_tree.yview)
#        self.nav_tree.configure(yscrollcommand=self.vsb.set)     
##        self.vsb.grid(column=0, row=0, sticky='nes',in_=self.tree_frame,rowspan=2)                         
#
#        self.s13 = ttk.Separator(self.tree_frame, orient=tk.VERTICAL)
#        self.s13.grid(row=0,column=2,rowspan=2,sticky="nesw")        
    def build_graphs_frame(self):
        self.log("Initiating MG Build Process.")
        
        self.graphs_frame = ttk.LabelFrame(self,text="Page")
        self.graphs_frame.grid(row=0,column=0)
        
        for n in range(0,4):
            self.bug("MG Build n={}".format(n))
            slot = tk.LabelFrame(self.graphs_frame,text=str(n+1))
            rowx = int(n/2)
            colx = int(n%2)
            self.bug("Rowx {}, colx {}".format(str(rowx),str(colx)))
            slot.grid(row=rowx,column=colx,sticky="nw",pady=0)
            
            slot.columnconfigure(0, weight=1)
            slot.rowconfigure(0, weight=1)
          
            canvas = tk.Canvas(slot)        
            self.graph_slots.append([canvas,"IMAGE","PATH"])  
            
        self.export_png = ttk.Button(
            self,
            command=self.export_multigraph,
            text="Export Graphs to .png")
        self.export_png.grid(
            row=3, column=0, padx=0, pady=2, sticky="w")
        
        for slot in self.graph_slots:
            canvas = slot[0]
            canvas.grid(row=0,column=0,sticky="wnse",padx=10,pady=10)
            canvas.update_idletasks()
            wd = canvas.winfo_width()
            self.bug(str(wd) + " width")        
            

def sortby(tree, col, descending):
    """sort tree contents when a column header is clicked on"""
    # grab values to sort
    data = [(tree.set(child, col), child) \
        for child in tree.get_children('')]
    # if the data to be sorted is numeric change to float
    #data =  change_numeric(data)
    # now sort the data in place
    data.sort(reverse=descending)
    for ix, item in enumerate(data):
        tree.move(item[1], '', ix)
    # switch the heading so it will sort in the opposite direction
    tree.heading(col, command=lambda col=col: sortby(tree, col, int(not descending)))         
        
if __name__ == "__main__":
    import config2
    dbcfg = config2.backend_settings
    app = tk.Tk()
    test_widget = MultiGrapher(app, app,dbcfg)
    test_widget.grid(padx=20)
    app.mainloop()          