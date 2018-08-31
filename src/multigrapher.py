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

# Non-standard Modules
import PIL

# Project Modules
from appwidget import AppWidget

class MultiGrapher(AppWidget):
    def __init__(self,parent,controller,config,dbvar=None):
        self.widget_name = "multigrapher"
        super().__init__(parent,controller,config,dbvar)  
            
        self.slots = []
        
        self.build()
        self.build2()
#        self.columnconfigure(0, weight=1)
#        self.columnconfigure(1, weight=1)   
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)   
            
    def build(self):
        self.log("Initiating MG Build Process.")
#        order = "nesw"
        for n in range(0,4):
            self.bug("MG Build n={}".format(n))
            slot = tk.LabelFrame(self,text=str(n+1))
            rowx = int(n/2)
            colx = int(n%2)
            self.bug("Rowx {}, colx {}".format(str(rowx),str(colx)))
            slot.grid(row=rowx,column=colx,sticky="nw",pady=0)
            
            slot.columnconfigure(0, weight=1)
            slot.rowconfigure(0, weight=1)
          
            canvas = tk.Canvas(slot)        
#            we leave a blank second element to be the placeholder for the image
#            objects, to prevent loss in garbage collection
            self.slots.append([canvas,"IMAGE","PATH"])  
            
        self.export_png = ttk.Button(
            self,
            command=self.export_multigraph,
            text="Export Graphs to .png")
        self.export_png.grid(
            row=3, column=0, padx=0, pady=2, sticky="w")

#        BUILD EXPORT BUTTON
#        On third row add a button, it calls a command called self.export_multigraph
            
    def build2(self):
      for slot in self.slots:
        canvas = slot[0]
        canvas.grid(row=0,column=0,sticky="wnse",padx=10,pady=10)
        canvas.update_idletasks()
        wd = canvas.winfo_width()
        self.bug(str(wd) + " width")
            
#    def resize(self, event):
#        size = (event.width, event.height)
#        resized = self.original.resize(size,Image.ANTIALIAS)
#        self.image = ImageTk.PhotoImage(resized)
#        self.display.delete("IMG")
#        self.display.create_image(0, 0, image=self.image, anchor=NW, tags="IMG")
      
            
    def get_TKimage(self,path,size):
          self.log("Resizing to: {}".format(size))
          PILim = PIL.Image.open(path)
          PILim = PILim.resize(size,PIL.Image.ANTIALIAS)
          TKim = PIL.ImageTk.PhotoImage(image=PILim)         
          return TKim       

    def receive_image(self,path,slot):
        self.log("Received image from path: {}".format(path))
        self.log("For slot: {}".format(slot))
        
        for index,slot in enumerate(self.slots):
          if not slot[1] == "IMAGE":
            self.bug("Slot in index: {} skipping because not 'image'.".format(str(index)))
            continue
          else:
            self.bug("Else at index:{}".format(str(index)))
            canvas = slot[0]
            canvas.update_idletasks()
#            wd = canvas.winfo_width()
#            print(wd)
#            ht = canvas.winfo_height()
#            print(ht)
#            size = (int(wd),int(ht))
            size = 400,250
            im = self.get_TKimage(path,size)
            cimg = canvas.create_image(0, 0, image=im, anchor="nw", tags="IMG")
            slot[1] = im
            slot[2] = path
            break
#        If slot = 0, FIND NEXT APPROPRIATE SLOT
#        If not, appropriate slot = slot
#        At target slot, remove image from label. 
#        Load image from path into tkImage. 
#        Replace label image with new image.
        
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
#            x = index // 2 * 805
            y = int(index / 2) *510
            x = int(index % 2) * 805            
#            y = index % 2 * 510
            w, h = img.size
            self.bug('index {0} pos {1},{2} size {3},{4}'.format(index, x, y, w, h))
            result.paste(img, (x, y, x + w, y + h))
        result.save(("image.jpg"))
        
if __name__ == "__main__":
    import config2
    dbcfg = config2.backend_settings
    app = tk.Tk()
    test_widget = MultiGrapher(app, app,dbcfg)
    test_widget.grid(padx=20)
    app.mainloop()          