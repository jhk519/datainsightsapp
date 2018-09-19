# -*- coding: utf-8 -*-
"""
Created on Fri Jun 22 13:12:47 2018

@author: Justin H Kim
"""
import datetime
from pprint import pprint
import os
import urllib
import io
import pickle

import sqlite3
import pandas as pd
import numpy as np
import PIL
import requests
import copy
import pandastable
import logging

import queries
import exceltodataframe as etdf

class DefaultEngine:
    def __init__(self,init_config = None,init_dbvar=None,name=""):
        self.engine_name = "DefaultEngine-{}".format(name   )
        self.log = logging.getLogger(self.engine_name).info
        self.log("{} Init.".format(self.engine_name))    
        self.bug = logging.getLogger(self.engine_name).debug
        
        self.__cfgvar = init_config      
        self.__dbvar = init_dbvar
        self.__req_headers = []        

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
             
    def time_str(self,key="now"):
        if key == "now":
            return datetime.datetime.now().strftime("%y%m%d-%H%M%S") 
        
    def get_cfg_val(self,key):
        try: 
            value = self.__cfgvar[key]
            
        except TypeError:
            self.bug("Could not get cfg_val for: {} for {} config.".format(key,self.engine_name))
        return value
    
    def get_export_full_name(self,base_string,ftype="excel",outdir=None):
        if ftype == "excel":
            ext = ".xlsx"
        elif ftype =="image":
            ext = ".png"
        elif ftype =="sqlite":
            ext = ".db"
            
        outname = base_string + self.time_str() + ext
        if not outdir:
            outdir = self.get_cfg_val("automatic export location")
            self.log("outdir from config: {}".format(outdir))
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        fullname = os.path.join(outdir, outname)      
        return fullname  
             
    def _check_req_headers(self,config_to_check=None):
        if not config_to_check:
            config_to_check = self.__config
        passed = True
        for target in self.__req_headers:
            if not config_to_check.get(target,False):
                self.bug("MISSING HEADER: {}".format(target))
                passed = False
        return passed

             