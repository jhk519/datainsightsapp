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
from pprint import pprint
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
    
    def __init__(self,parent,controller,config,dbvar=None):
        self.widget_name = "multigrapher"
        super().__init__(parent,controller,config,dbvar)  

        self.build_tree_frame()
        self.build_graphs_frame()
        
        self.refresh_nav_tree() 
#        self.update_all_graph_slots(0)
        
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)   
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)   

# ================================================================
# ================================================================
#       API
# ================================================================
# ================================================================  
        
    def receive_image(self,path,request_pack,slotnum=None):
        self.log("Received image from path: {} and slotnum {}".format(path,slotnum))
        the_graph_slot = None
        slot_pack = self.engine.convert_request_pack_to_slot_pack(request_pack)
        slot_pack["last_path"] = path

#       Locate the required graph slot we need to change. If none given, find
#       the next empty slot. 
        if not slotnum:
            self.log("No slotnum given")
            for index,slot in enumerate(self.graph_slots):
                if not slot[1] == "IMAGE":
                    self.bug("Slot in index: {} skipping because not 'image'.".format(str(index)))
                    continue
                else:
                    the_graph_slot = slot
            #       Edit cfg with new slot_pack
                    try:
                        self.engine.get_cfg_val("presetpages")[self.curr_pageslotindex]["slots"][index] = slot_pack
                    except IndexError:
                        self.bug("No slot currently in config. Appending to list.")
                        self.engine.get_cfg_val("presetpages")[self.curr_pageslotindex]["slots"].append(slot_pack)                       
                    break
        elif slotnum:
            the_graph_slot = self.graph_slots[slotnum]    

        self.load_graph_in_slot(path,the_graph_slot)
        self.send_presets_and_refresh()        
        
    def send_presets_and_refresh(self):
        try:
            self.controller.send_new_presets
        except AttributeError:
            self.bug("No controller to send new presets.")
        else:
            self.controller.send_new_presets(self.engine.get_cfg_val("presetpages")) 
        self.refresh_nav_tree()    
        
# ================================================================
# ================================================================
#       GRAPH UX
# ================================================================
# ================================================================ 
          
    def update_all_graph_slots(self):
        self.log("APPLY ALL SLOTS")        
        page =  self.engine.get_cfg_val("presetpages")[self.curr_pageslotindex]
        for index,slot_pack in enumerate(page["slots"]):
            self.log("Applying for slot index {}.".format(index ))
            request_pack = self.engine.convert_slot_pack_to_request_pack(slot_pack)
            new_path = self.update_graph(request_pack,index)
            slot_pack["last_path"] = new_path      
          
    def export_multigraph(self):
        self.log("Exporting Stiched Graphs")
        result = PIL.Image.new("RGB", (1620, 1020),"white")
        for index, slot in enumerate(self.graph_slots):
            self.bug("slot[1] == {}".format(slot[1]))
            if slot[1] == "IMAGE":
              continue
            path = self.engine.get_cfg_val("presetpages")[0]["slots"][index]["last_path"]
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
        canvas.update_idletasks()
        size = 400,250
        im = self.get_TKimage(path,size)
        graphslot[1] = im
        cimg = canvas.create_image(0, 0, image=im, anchor="nw", tags="IMG")
        
    def get_TKimage(self,path,size):
          self.log("Resizing to: {}".format(size))
          PILim = PIL.Image.open(path)
          PILim = PILim.resize(size,PIL.Image.ANTIALIAS)
          TKim = PIL.ImageTk.PhotoImage(image=PILim)         
          return TKim   
         
    def load_previews(self,pageindex):
#        print("----")
        self.curr_pageslotindex = pageindex
        cur_page = self.engine.get_cfg_val("presetpages")[pageindex]

        for ind,graph_slot in enumerate(self.graph_slots):
            canvas = graph_slot[0]
            graph_slot[1] = "IMAGE"
            graph_slot[2] = []
            self.clear_canvas(canvas)
            try:
                cfg = cur_page["slots"][ind]
            except IndexError:
                self.bug("No more slots left in config.")
                continue
            else: 
                graph_slot[1] = "PREVIEW"
                self.recursive_unpack(canvas,cfg,graph_slot[2])
#                path = cfg["last_path"]
#                if path:
#                    self.load_graph_in_slot(path,graph_slot)
#                else:
#                    self.recursive_unpack(canvas,cfg,graph_slot[2])
            canvas.update_idletasks()
        
    def recursive_unpack(self, canvas, obj,var_ref):
        if type(obj) is dict:
            for k,v in obj.items():
                typev = type(v)
                if typev is str or typev is int:   
                    var_ref.append(self.gen_canvas_text(canvas,len(var_ref), key=k,value=v))
                elif typev is list:
                    for tupleitem in v:
                        var_ref.append(self.gen_canvas_text(canvas, len(var_ref),key=tupleitem[0]))
                elif typev is dict:
                    var_ref.append(self.gen_canvas_text(canvas, len(var_ref),key=k))
                    self.recursive_unpack(canvas,v,var_ref) 
#        else:
#            return        
            
    def clear_canvas(self,canvas):
        canvas.delete("all")
#        for graphslot in self.graph_slots:
#            slot
    #        allitems = canvas.find_all()
#        print(allitems)
#        for item in allitems:
#            canvas.delete(item)
#            
    def gen_canvas_text(self,canvas,row,key="",value=""):
#        self.log("{} {} {}".format(self.preview_row,key,value))
        ypos = (row * 25 + 15)
        textv = "{} - {}".format(key,value)
        textid = canvas.create_text(20,ypos,text=textv,anchor="w")  
        return textid
# ================================================================
# ================================================================
#      TREEVIEW UX
# ================================================================
# ================================================================ 

    def create_new_page(self):
        self.log("Creating new page...")
        pgs = self.engine.get_cfg_val("presetpages")
        pgnm = "PAGE{}".format(str(len(pgs)))
        cnt = 1
        while self.nav_tree.exists(pgnm):
            cnt += 1
            pgnm = "PAGE{}".format(str(cnt))
                
        pgs.append({"pagename":pgnm,"slots": []})
        self.send_presets_and_refresh()

    def rename_page(self):
        curItemId = self.nav_tree.focus()
        if curItemId != None:
            slot_num = self.nav_tree.index(curItemId)
            newtitlelambda = lambda slot_num = slot_num:self.new_page_title_listener(slot_num)
            if "page" in self.nav_tree.item(curItemId)["tags"]:
                title = "Edit Graph Title"
                text = "Please Enter New Title."
                self.create_popup(title,text,entrycommand=newtitlelambda)   

    def preview_page(self,e=None):
        curItemId = self.nav_tree.focus()
        self.log("Previewing pageid {}".format(curItemId))
        if curItemId != None and "page" in self.nav_tree.item(curItemId)["tags"]:
            pageindex = self.nav_tree.index(curItemId)
            self.log("Current tree focus is a page at index {}".format(pageindex))
            self.load_previews(pageindex)  
                
# ================================================================
# ================================================================
#      TREEVIEW HELPERS
# ================================================================
# ================================================================          
        
    def new_page_title_listener(self,slot_num):
        new_name = self.popupentryvar.get()
        if self.nav_tree.exists(new_name):  
            self.bug("{} already exists. Cannot rename at slot_num: {}".format(new_name,slot_num))
        else:
            self.engine.get_cfg_val("presetpages")[slot_num]["pagename"] = self.popupentryvar.get()
            self.send_presets_and_refresh()

    def refresh_nav_tree(self):
        cfg = self.engine.get_cfg_val("presetpages")
        self.nav_tree.delete(*self.nav_tree.get_children())
        
        for ind,page in enumerate(cfg):
            name = page["pagename"]
            pagenameid = self.nav_tree.insert("","end",name,text=name,tags=("page",str(ind)))
            for index, slot in enumerate(page["slots"]):
                pcode = slot["extra"]
                mirror_days = slot["mirror_days"]
                days_back = slot["days_back"]
                if slot["title"]:
                    slottext = slot["title"]
                else:
#                    slottext = "Slot {}".format(str(index+1))
                    slottext = "Autoname{}".format(str(index+1))

                slotval = ["","","",pcode,days_back,mirror_days]
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
            self.bug("MG Build n={}".format(n))
            slot = tk.LabelFrame(self.graphs_frame,text=str(n+1))
            rowx = int(n/2)
            colx = int(n%2)
            self.bug("Rowx {}, colx {}".format(str(rowx),str(colx)))
            slot.grid(row=rowx,column=colx,sticky="nw",pady=0)
            
            slot.columnconfigure(0, weight=1)
            slot.rowconfigure(0, weight=1)
          
            canvas = tk.Canvas(slot,bg='#FFFFFF') 
            hbar=tk.Scrollbar(slot,orient=tk.HORIZONTAL)
            hbar.pack(side=tk.BOTTOM,fill=tk.X)
            hbar.config(command=canvas.xview)
            vbar=tk.Scrollbar(slot,orient=tk.VERTICAL)
            vbar.pack(side=tk.RIGHT,fill=tk.Y)
            vbar.config(command=canvas.yview)
#            canvas.config(width=300,height=300)
            canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
                       
            self.graph_slots.append([canvas,"IMAGE",[]])  
            
        self.export_png = ttk.Button(
            self.graphs_frame,
            command=self.export_multigraph,
            text="Export Graphs to .png")
        self.export_png.grid(
            row=3, column=0, padx=0, pady=2, sticky="w")
        
        for slot in self.graph_slots:
            canvas = slot[0]
            canvas.pack(side=tk.LEFT,expand=True,fill=tk.BOTH) 
            canvas.update_idletasks()
            wd = canvas.winfo_width()
            self.bug(str(wd) + " width")        
            
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
        
        nav_tree_cols = [("AXIS",50),("QUERY",100),("COLOR",50),("PCODE",80),("DAYS",60),("MIRROR",60)]     
        
        self.nav_tree = ttk.Treeview(self.tree_frame, columns=[aa[0] for aa in nav_tree_cols])
        self.nav_tree.grid(sticky="news")
        self.nav_tree.bind("<<TreeviewSelect>>", self.preview_page)
  
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
                              
        self.create_new_page_button = ttk.Button(
            self.tree_frame,
            command=self.create_new_page,
            text="New Page")
        self.create_new_page_button.grid(
            row=1, column=0, padx=0, pady=2, sticky="w")                              
                              
        self.rename_page_button = ttk.Button(
            self.tree_frame,
            command=self.rename_page,
            text="Rename Page")
        self.rename_page_button.grid(
            row=2, column=0, padx=0, pady=2, sticky="w")   
        
        self.preview_page_button = ttk.Button(
            self.tree_frame,
            command=self.preview_page,
            text="Preview Page")
        self.preview_page_button.grid(
            row=3, column=0, padx=0, pady=2, sticky="w")           

#        self.vsb = ttk.Scrollbar(self.tree_frame,orient="vertical",
#            command=self.nav_tree.yview)
#        self.nav_tree.configure(yscrollcommand=self.vsb.set)     
##        self.vsb.grid(column=0, row=0, sticky='nes',in_=self.tree_frame,rowspan=2)                         
#
#        self.s13 = ttk.Separator(self.tree_frame, orient=tk.VERTICAL)
#        self.s13.grid(row=0,column=2,rowspan=2,sticky="nesw")        
            
            

      
        
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