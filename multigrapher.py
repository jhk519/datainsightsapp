# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 19:42:58 2018

@author: Justin H Kim

slot_pack = {
            "extra":request_pack["extra"],
            "x_axis_label": request_pack["x_axis_label"],
            "mirror_days":request_pack["mirror_days"],      
            "last_path":None,
            "left": {
                "gtype":request_pack["left"]["gtype"],
                "metric": request_pack["left"]["metric"],
                "queries": request_pack["left"]["queries"],
            },
            "right": {
                "gtype":request_pack["right"]["gtype"],
                "metric": request_pack["right"]["metric"],
                "queries": request_pack["right"]["queries"],
            }, 
            "days_back":((request_pack["end"] - request_pack["start"]).days),
            "title": request_pack["title"]
         }     
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
import logging
import os
import datetime

# Non-standard Modules
import PIL

# Project Modules
from appwidget import AppWidget

class MultiGrapher(AppWidget):
            
    curr_pageslotindex = 0
    graph_slots = [] #[canvas,"IMAGE","CONFIG"]
    preview_row = 0 
#    if not custom_today:
#    self.custom_today = datetime.now.date()
#    else:
    custom_today = datetime.date(2018,5,1)    
    
    def __init__(self,parent,controller,config,dbvar=None):
        self.widget_name = "multigrapher"
        super().__init__(parent,controller,config,dbvar)  

        self.build_tree_frame()
        self.build_graphs_frame()

        self.refresh_nav_tree() 
        
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)   
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)   

# ================================================================
# ================================================================
#       API
# ================================================================
# ================================================================  
        
    def receive_image(self,path,request_pack):
        self.log("Received image from path: {}".format(path))
        pages_cfg = self.get_cfg_val("presetpages")
        if len(pages_cfg) == 0:
            self.bug("No pages in presetpages!")
            self.create_popup("No page selected to add image.")
            return
        slots_cfg = pages_cfg[self.curr_pageslotindex]["request_packs"]
        the_graph_slot = None
        request_pack["last_path"] = path

        for index,slot in enumerate(self.graph_slots):
            if not slot[1] == "IMAGEPLACEHOLDER":
                self.bug("Slot in index: {} skipping because not 'image'.".format(str(index)))
                continue
            elif slot[1] == "IMAGEPLACEHOLDER":
                the_graph_slot = slot
        #       Edit cfg with new slot_pack
                try:
                    slots_cfg[index] = request_pack
                except IndexError:
                    self.bug("No slot currently in config. Appending to list.")
                    slots_cfg.append(request_pack)                       
                break
                
        self.load_graph_in_slot(path,the_graph_slot)
        self.refresh_nav_tree()           
        
    def send_presets_and_refresh(self):
        self.send_presets()
        self.refresh_nav_tree() 
                
    def send_presets(self,e=None):
        self.log("Sending presets.")
        try:
            self.controller.send_new_presets
        except AttributeError:
            self.bug("No controller to send new presets.")
        else:
            self.controller.send_new_presets(self.get_cfg_val("presetpages")) 
        
# ================================================================
# ================================================================
#       GRAPH UX
# ================================================================
# ================================================================ 
          
    def update_all_graph_slots(self):
        self.log("Updating graph on all slots.")        
        page =  self.get_cfg_val("presetpages")[self.curr_pageslotindex]
        for index,slot_pack in enumerate(page["request_packs"]):
            self.log("Applying for slot index {}.".format(index ))
            request_pack = self.engine.update_request_pack(slot_pack,self.custom_today)
            new_path = self.update_graph(request_pack,index)
            slot_pack["last_path"] = new_path      
            
    def export_multigraph(self):
        self.log("Exporting Stiched Graphs")
        result = PIL.Image.new("RGB", (1620, 1020),"white")
        for index, slot in enumerate(self.graph_slots):
            self.bug("slot[1] == {}".format(slot[1]))
            if slot[1] == "IMAGEPLACEHOLDER":
              continue
            path = self.get_cfg_val("presetpages")[0]["request_packs"][index]["last_path"]
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

# ================================================================
# ================================================================
#       GRAPH SLOT HELPERS
# ================================================================
# ================================================================         
   
    def update_graph(self,request_pack,slotnum):
        path = self.controller.get_graph_path(request_pack)
        graphslot = self.graph_slots[slotnum]
        self.load_graph_in_slot(path,graphslot)
        return path
    
    def load_graph_in_slot(self,path,graphslot):
        self.log("Loading path")
        canvas = graphslot[0]
        canvas.delete("all")
        canvas.update_idletasks()
        size = 400,250
        im = self.get_TKimage(path,size)
        if not im:
            self.bug("Received false from .get_TKimage, skipping to preview.")
            return False
        graphslot[1] = im
        canvas.create_image(0, 0, image=im, anchor="nw", tags="IMG")
        
    def get_TKimage(self,path,size):
          self.log("Resizing to: {}".format(size))
          try:
              PILim = PIL.Image.open(path)
          except FileNotFoundError:
              self.bug("Last path: {} no longer exists.".format(path))
              return False
          PILim = PILim.resize(size,PIL.Image.ANTIALIAS)
          TKim = PIL.ImageTk.PhotoImage(image=PILim)         
          return TKim   
         
    def load_preview_at_page_index(self,pageindex):
        cur_page = self.get_cfg_val("presetpages")[pageindex]

        for ind,graph_slot in enumerate(self.graph_slots):
            canvas = graph_slot[0]
            canvas.delete("all")
            graph_slot[1] = "IMAGEPLACEHOLDER"
            #listvar to hold text items in memory (tk issue)            
            graph_slot[2] = []
            
            try:
                cfg = cur_page["request_packs"][ind]
            except IndexError:
                continue
            
            self.recursive_unpack(canvas,cfg,graph_slot[2])
            graph_slot[1] = "PREVIEW"
#            
#            if cfg["last_path"] == None or cfg["last_path"] == "None":
#                self.recursive_unpack(canvas,cfg,graph_slot[2])
#                graph_slot[1] = "PREVIEW"
#            else:
#                if self.load_graph_in_slot(cfg["last_path"],graph_slot) == False:
#                    graph_slot[2].append(self.gen_canvas_text(canvas, 0, key="Previous image no longer exists, showing text preview."))
#                    self.recursive_unpack(canvas,cfg,graph_slot[2])
#                    graph_slot[1] = "PREVIEW"                    
            canvas.update_idletasks()
        
    def recursive_unpack(self, canvas, cfg_dict,var_ref):
        if type(cfg_dict) is dict:
            for k,v in cfg_dict.items():
                typev = type(v)
                if typev is str or typev is int:   
                    var_ref.append(self.gen_canvas_text(canvas,len(var_ref), key=k,value=v))
                elif typev is list:
                    for tupleitem in v:
                        var_ref.append(self.gen_canvas_text(canvas, len(var_ref),key=tupleitem))
                elif typev is dict:
                    var_ref.append(self.gen_canvas_text(canvas, len(var_ref),key=k))
                    self.recursive_unpack(canvas,v,var_ref) 

    def gen_canvas_text(self,canvas,row,key="",value=""):
#        self.log("{} {} {}".format(self.preview_row,key,value))
        ypos = (row * 25 + 15)
        textv = "{}".format(key)
        if value:
            textv = textv + " - {}".format(value)
        textid = canvas.create_text(20,ypos,text=textv,anchor="w")  
        return textid
# ================================================================
# ================================================================
#      TREEVIEW UX
# ================================================================
# ================================================================ 

    def create_new_page(self):
        self.log("Creating new page...")
        pgs = self.get_cfg_val("presetpages")
        pgnm = "PAGE{}".format(str(len(pgs)))
        cnt = 1
        while self.nav_tree.exists(pgnm):
            cnt += 1
            pgnm = "PAGE{}".format(str(cnt))
                
        pgs.append({"pagename":pgnm,"request_packs": []})
        self.send_presets_and_refresh()

    def rename_page(self):
        itype,iindex,iid = self.get_type_index_current_item()
        if itype == "page":
            newtitlelambda = lambda iindex = iindex:self.new_page_title_listener(iindex)
            title = "Edit Graph Title"
            text = "Please Enter New Title."
            self.create_popup(title,text,entrycommand=newtitlelambda)   

    def preview_page_at_selection(self,e=None):
        itype,iindex,iid = self.get_type_index_current_item()
        if itype == "page":
            self.curr_pageslotindex = iindex
            self.log("Current curr_pageslotindex set to {}".format(self.curr_pageslotindex))
            self.load_preview_at_page_index(self.curr_pageslotindex)     
            
    def reload_defaults(self):
        defaultcfg = self.controller.get_default_presets()
        self.set_build_config(defaultcfg)
        self.refresh_nav_tree()

    def shift_slot_up(self):            
        itype,iindex,iid = self.get_type_index_current_item()
        if itype == "slot":
            self.log("Switching current item at index: {} to new index {}".format(iindex,iindex-1))
            self.switch_slots(iindex,iindex-1)
            self.load_preview_at_page_index(self.curr_pageslotindex) 
            self.send_presets_and_refresh()
            
    def shift_slot_down(self):
        itype,iindex,iid = self.get_type_index_current_item()
        if itype == "slot":
            self.log("Switching current item at index: {} to new index {}".format(iindex,iindex-1))
            self.switch_slots(iindex,iindex+1)
            self.load_previews(self.curr_pageslotindex) 
            self.send_presets_and_refresh()     
            
    def delete_slot(self):
        itype,iindex,iid = self.get_type_index_current_item()
        if itype == "slot":
            pgid,slotnum = iid.split("_")
            pgindex = self.nav_tree.index(pgid)
            pgs = self.get_cfg_val("presetpages")
            pgs[pgindex]["request_packs"].pop(int(slotnum))
            self.send_presets_and_refresh() 
            
    def delete_page(self):
        itype,iindex,iid = self.get_type_index_current_item()
        if itype == "page":
            self.log("Deleting Page")
            pgs = self.get_cfg_val("presetpages")
            pgs.pop(iindex)
            self.send_presets_and_refresh()                   
            
        
    def switch_slots(self,slotindex1,slotindex2):
        self.bug("switching slotindex {} and {}".format(slotindex1,slotindex2))
        cur_slots_list = self.get_cfg_val("presetpages")[self.curr_pageslotindex]["request_packs"]
        cur_slots_list[slotindex1], cur_slots_list[slotindex2] = cur_slots_list[slotindex2], cur_slots_list[slotindex1]   
        
# ================================================================
# ================================================================
#      TREEVIEW HELPERS
# ================================================================
# ================================================================    
        
    def get_type_index_current_item(self):
        curItemId = self.nav_tree.selection()[0]
#        print("TYPE {}".format(curItemId))
#        self.log("Current Selection at id {}".format(curItemId))
        if curItemId != None:
            if "page" in self.nav_tree.item(curItemId)["tags"]:
                itemtype = "page"
            elif "slot" in self.nav_tree.item(curItemId)["tags"]:
                itemtype = "slot"
            else:
                itemtype = "unknown"
            indexn = self.nav_tree.index(curItemId)
            return itemtype,indexn,curItemId
        else:
            return None
        
    def new_page_title_listener(self,slot_num):
        new_name = self.popupentryvar.get()
        if self.nav_tree.exists(new_name):  
            self.bug("{} already exists. Cannot rename at slot_num: {}".format(new_name,slot_num))
        else:
            self.get_cfg_val("presetpages")[slot_num]["pagename"] = self.popupentryvar.get()
            self.send_presets_and_refresh()

    def refresh_nav_tree(self):
        cfg = self.get_cfg_val("presetpages")
        self.nav_tree.delete(*self.nav_tree.get_children())
        if type(cfg) is list and len(cfg) == 0:
            self.bug("Presetpages cfg is empty list.")
        elif type(cfg) is list and len(cfg) > 0:
            for ind,page in enumerate(cfg):
                name = page["pagename"]
                pagenameid = self.nav_tree.insert("","end",name,text=name,tags=("page",str(ind)))
                for index, slot in enumerate(page["request_packs"]):
                    metric_str = "{} of {} ({})".format(
                                                slot["metric_options"]["data_type"],
                                                slot["metric_options"]["metric"],
                                                slot["metric_options"]["metric_type"]) 
                    
                    bkdwn_str = slot["metric_options"]["breakdown"]
                    
                    agg_str = "{} of {}-Day Periods".format(
                                        slot["result_options"]["aggregation_type"],
                                        slot["result_options"]["aggregation_period"])
                
                    compare_to_str = slot["result_options"]["compare_to_days"]

    
                    slotval = [metric_str,bkdwn_str,agg_str,compare_to_str]
                    slotid = self.nav_tree.insert(pagenameid,"end",pagenameid+"_"+str(index),tags=("slot"),
                                                text="Slot {}".format(index+1),
                                                values=slotval)
            self.nav_tree.selection_set(self.nav_tree.get_children("")[0])
        else:
            self.bug("Presetpages cfg is somehow not a list!")
                                    
# ================================================================
# ================================================================
#      UX Helpers
# ================================================================
# ================================================================  

                                       
                                    
# ================================================================
# ================================================================
#      BUILD UI
# ================================================================
# ================================================================                                      
                                    
    def build_graphs_frame(self):
        self.log("Initiating MG Build Process.")
        
        self.graphs_frame = ttk.LabelFrame(self,text="Page")
        self.graphs_frame.grid(row=0,column=0)
        
        for n in range(0,4):
            slot = tk.LabelFrame(self.graphs_frame,text=str(n+1))
            rowx = int(n/2)
            colx = int(n%2)
            self.bug("Build slot n={} - Rowx {}, colx {}".format(n,str(rowx),str(colx)))
            slot.grid(row=rowx,column=colx,sticky="nw",pady=0)
            
            slot.columnconfigure(0, weight=0)
            slot.rowconfigure(0, weight=0)
          
            canvas = tk.Canvas(slot,bg='#FFFFFF') 
                               
            hbar=tk.Scrollbar(slot,orient=tk.HORIZONTAL)
            hbar.pack(side=tk.BOTTOM,fill=tk.X)
            hbar.config(command=canvas.xview)
            vbar=tk.Scrollbar(slot,orient=tk.VERTICAL)
            vbar.pack(side=tk.RIGHT,fill=tk.Y)
            vbar.config(command=canvas.yview)
#            canvas.config()
            canvas.config(width=450,height=300,xscrollcommand=hbar.set, yscrollcommand=vbar.set,scrollregion=(0, 0, 450, 600))
                       
            self.graph_slots.append([canvas,"IMAGEPLACEHOLDER",[]])  
            
            canvas.pack(side=tk.LEFT,expand=True,fill=tk.BOTH) 
            canvas.update_idletasks()
#            wd = canvas.winfo_width()
            
        self.export_png = ttk.Button(
            self.graphs_frame,
            command=self.export_multigraph,
            text="Export Graphs to .png")
        self.export_png.grid(
            row=3, column=0, padx=0, pady=2, sticky="w")        
            
        self.update_graphs_button = ttk.Button(
            self.graphs_frame,
            command=self.update_all_graph_slots,
            text="update_graphs_button Graphs on Page")
        self.update_graphs_button.grid(
            row=4, column=0, padx=0, pady=2, sticky="w") 
                                    
    def build_tree_frame(self):
        self.log("Building Tree Frame")
        
        self.tree_frame = ttk.LabelFrame(self,text="Pages")
        self.tree_frame.grid(row=0,column=1,sticky="nsew")
        
        nav_tree_cols = [("METRIC",150),("BREAKDOWN",100),("AGGREGATION",150),("COMPARE TO",50)]     
        
        self.nav_tree = ttk.Treeview(self.tree_frame, columns=[aa[0] for aa in nav_tree_cols])
        self.nav_tree.grid(sticky="news")
        self.nav_tree.bind("<<TreeviewSelect>>", self.preview_page_at_selection)
  
        for header in nav_tree_cols:
            self.nav_tree.heading(header[0],text=header[0], command=lambda c=header: self.sortby(self.nav_tree, c, 0))
#            resizes
            self.nav_tree.column(header[0],
                                 width=header[1],
                                 minwidth=header[1],
                                 anchor="center",
                                 stretch="true") 

        self.nav_tree.tag_configure("box_item",background="lightgrey")
        self.nav_tree.column("#0",width=110)
        self.nav_tree.heading("#0",text="Page / Graph")
                              
        self.nav_tree.tag_configure("page",background="#d3d3d3") 
        self.nav_tree.tag_configure("slot",background="#f4f4f4"   )     

        rown = 0
        
        rown += 1
        self.create_new_page_button = ttk.Button(
            self.tree_frame,
            command=self.create_new_page,
            text="New Page")
        self.create_new_page_button.grid(
            row=rown, column=0, padx=0, pady=2, sticky="w")                              
                              
        rown += 1
        self.rename_page_button = ttk.Button(
            self.tree_frame,
            command=self.rename_page,
            text="Rename Page")
        self.rename_page_button.grid(
            row=rown, column=0, padx=0, pady=2, sticky="w")   
                              
        rown += 1        
        self.save_page_button = ttk.Button(
            self.tree_frame,
            command=self.send_presets_and_refresh,
            text="Save Pages")
        self.save_page_button.grid(
            row=rown, column=0, padx=0, pady=2, sticky="w")   
                              
        rown += 1
        self.reload_defaults_button = ttk.Button(
            self.tree_frame,
            command=self.reload_defaults,
            text="Reload Default")
        self.reload_defaults_button.grid(
            row=rown, column=0, padx=0, pady=2, sticky="w")         
                               
        rown += 1       
        self.swap_slots_buttons = ttk.Button(
            self.tree_frame,
            command=self.shift_slot_up,
            text="Move Slot Up")
        self.swap_slots_buttons.grid(
            row=rown, column=0, padx=0, pady=2, sticky="w")   

        rown += 1       
        self.delete_slot_button = ttk.Button(
            self.tree_frame,
            command=self.delete_slot,
            text="Delete Slot")
        self.delete_slot_button.grid(
            row=rown, column=0, padx=0, pady=2, sticky="w")  
        
        rown += 1       
        self.delete_page_button = ttk.Button(
            self.tree_frame,
            command=self.delete_page,
            text="Delete Page")
        self.delete_page_button.grid(
            row=rown, column=0, padx=0, pady=2, sticky="w")          
        
if __name__ == "__main__":
    logname = "debug-{}.log".format(datetime.datetime.now().strftime("%y%m%d"))
    ver = "v0.2.10.7 - 2018/07/22"
    if not os.path.exists(r"debug\\"):
        os.mkdir(r"debug\\")   
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
    dbcfg = config2.backend_settings
    app = tk.Tk()
    test_widget = MultiGrapher(app, app,dbcfg)
    test_widget.grid(padx=20)
    app.mainloop()          