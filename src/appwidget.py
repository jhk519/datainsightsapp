# -*- coding: utf-8 -*-
"""
Created on Thu Aug 30 12:59:56 2018

@author: Justin H Kim
"""
import tkinter as tk
import tkinter.ttk as ttk

import logging
import datetime
import os
import pickle
import sqlite3
import PIL
import requests
import copy
import urllib
import io
import numpy as np
import pandas as pd
from pprint import pprint as PRETTYPRINT

import queries
#import newqueries


class AppWidget(tk.Frame):
    def __init__(self,parent,controller,config,dbvar,usedebuglog=True):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        
        if not usedebuglog:
            self.log = print
        else:
            self.log = logging.getLogger(__name__ + "-" + self.widget_name).info
            self.log("Init.")
        self.bug = logging.getLogger(self.widget_name).debug   
        
        self._req_headers = []  
        self.config_chain = []
        self.popupentryvar = tk.StringVar()        
        
#        PRETTYPRINT(config["dbmanager"])
        
        try:
            config[self.widget_name]
        except KeyError:
            self.bug("{} not in config. Check config2 file.".format(self.widget_name))
            self.set_build_config({})
        else:
            self.log("Setting build config for {}".format(self.widget_name))
            self.set_build_config(config[self.widget_name])
            
        self.__dbvar = dbvar  

#   API
    def set_build_config(self,raw_config):
        if self._check_req_headers(config_to_check=raw_config):
            self.log("Passed Check Req Headers.")
            self.__cfgvar = raw_config
        else:
            self.bug("New Config is Incompatible. Setting new Config terminated.")
            
    def set_dbvar(self,new_dbdata):
        self.__dbvar = new_dbdata    
        
    def get_dbvar(self):
        return self.__dbvar
    
    def get_config(self,need_copy=False):
        if need_copy:
            return copy.deepcopy(self.__cfgvar)
        else:
            return self.__cfgvar
             
    def get_time_str(self,key="now"):
        if key == "now":
            return datetime.datetime.now().strftime("%y%m%d-%H%M%S") 
        
    def get_cfg_val(self,key):
        try: 
            value = self.__cfgvar[key]
        except TypeError:
            self.bug("Could not get cfg_val for: {} for {} config.".format(key,__name__ + "-" + self.widget_name))
            return None
        except KeyError:
            self.bug("This key is not found in cfg! {}".format(key))
            return None
        else:
            return value
    
    def get_export_full_name(self,base_string,ftype="excel",outdir=None):
        if ftype == "excel":
            ext = ".xlsx"
        elif ftype =="image":
            ext = ".png"
        elif ftype =="sqlite":
            ext = ".db"
            
        outname = base_string + self.get_time_str() + ext
        if not outdir:
            outdir = self.get_cfg_val("automatic export location")
            self.log("outdir from config: {}".format(outdir))
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        fullname = os.path.join(outdir, outname)      
        return fullname  
             
    def _check_req_headers(self,config_to_check=None):
        if not config_to_check:
            config_to_check = self.__cfgvar
        passed = True
        for target in self._req_headers:
            if not config_to_check.get(target,False):
                self.bug("MISSING HEADER: {}".format(target))
                passed = False
        return passed    
    
    #   API       
    def set_cfgvar(self,new_cfgvar):
        self.log("Changing cfg.")
        self.set_build_config(new_cfgvar[self.widget_name]) 
        for widget in self.config_chain:
            widget.set_cfgvar(new_cfgvar)
        
    def create_popup(self,title,text,entrycommand=False,firstb=None,secondb=None):
        #firstb secondb is ("BUTTONTEXT",BUTTONCOMMAND)        
        self.popup = tk.Toplevel()
        self.popup.title(title)
        tk.Message(self.popup,text=text).pack()
        if firstb and secondb:
            tk.Button(self.popup,text=firstb[0],command=firstb[1]).pack()
            tk.Button(self.popup,text=secondb[0],command=secondb[1]).pack()
            tk.Button(self.popup,text="OK",command=self.popup.destroy).pack()
        elif entrycommand:
            tk.Entry(self.popup,textvariable=self.popupentryvar).pack()
            tk.Button(self.popup,text="Set",command=entrycommand).pack()
            tk.Button(self.popup,text="Close",command=self.popup.destroy).pack()
        else:
            tk.Button(self.popup,text="Close",command=self.popup.destroy).pack()
            
        return self.popup
            
    def _sortby(self, tree, col, descending):
        """sort tree contents when a column header is clicked on
        please note this function was taken online and not my own. 
        """
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
        
class CreateToolTip(object):
    """
    create a tooltip for a given widget
    CREDIT FOR THIS CLASS HERE:
    crxguy52 @ https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tkinter
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 400     #miliseconds
        self.wraplength = 280   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_pointerx() + 5
        y += self.widget.winfo_rooty() + 25
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()        
            

 

