# -*- coding: utf-8 -*-
"""
Created on Wed May  2 22:57:53 2018

@author: Justin H Kim
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Apr 26 17:12:28 2018

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
import datetime

class SettingsFrame(ttk.LabelFrame):
    def __init__(self, notebook_parent, configger):
        super().__init__(notebook_parent,text="Settings")
        self.str_name = "settings_frame"
        self.configger = configger
        self.time_created = datetime.datetime.now()
        self.setting_packets = []
        
        self.settings_dict = {}
        for x,y in self.configger._sections["INIT"].items():
            self.settings_dict[x] = [y.split(":")[0],y.split(":")[1]]  
        self._init_settings()
        self._init_entries()
        self.update()
        
    def _init_settings(self):
        frame_row = 0

        for key,value in self.settings_dict.items():
            cfgval = value[0]
            val_type = value[1]
            stvar_check_var = tk.StringVar()
            stvar_check_var.set(str(cfgval))
            
            title = ttk.Label(self,text=key)
            title.grid(row=frame_row, column=0, sticky="nw", padx=(15,25),pady=7)

            setting_pack = [key,cfgval,val_type,title,stvar_check_var,[]]
            self.setting_packets.append(setting_pack)
            frame_row += 1  
            
    def _init_entries(self):
        #For some reason, in order for the Entry widgets to initialize with
        #their StVars, we have to initialize the two separate, thus,
        #the above workaround        
        for index, value in enumerate(self.setting_packets):
            val_type = value[2]
            stvar_check_var = value[4]
            values_list = value[5]
            lambdafunc = lambda index = index: self._validate_and_set(index)
            
            if val_type == "str":
                values_list.append(
                    ttk.Entry(self, textvariable=stvar_check_var,validate="focusout",
                        validatecommand=lambdafunc,width=30))
            elif val_type == "bool":
                values_list.append(ttk.Radiobutton(self,
                    variable=stvar_check_var,
                    text="Yes",
                    value="True",
                    command=lambdafunc))
                
                values_list.append(ttk.Radiobutton(self,
                    variable=stvar_check_var,
                    text="No",
                    value="False",
                    command=lambdafunc))  
            elif val_type == "list": 
                values_list.append(
                    ttk.Entry(self, textvariable=stvar_check_var,validate="key",
                        validatecommand=lambdafunc,width=90))
            elif val_type == "date":
                values_list.append(
                    ttk.Entry(self, textvariable=stvar_check_var,validate="focusout",
                        validatecommand=lambdafunc,width=30))
            elif val_type == "int":
                values_list.append(
                    tk.Spinbox(self, from_=1.0, to=30.0,
                               wrap=True, width=4, validate="key",
                               state="readonly",    
                               textvariable = stvar_check_var,
                               command=lambdafunc))
                
            for colcount,value_widget in enumerate(values_list):
                if type(value_widget) is ttk.Entry:
                    value_widget.grid(row=index,column=colcount+1,sticky="w",
                        columnspan=3)
                else:
                    value_widget.grid(row=index,column=colcount+1,sticky="w")     
                    
    def _validate_and_set(self,index):
        #setting_pack = [key,cfgval,val_type,title_wgt,stvar_check_var,[widgets]]
        pack = self.setting_packets[index]
        curr_val = pack[4].get()
        self.configger.set("INIT",pack[0],curr_val+":"+pack[2])
        with open('fcfg.ini', 'w') as configfile:
            self.configger.write(configfile)
        
        return 1
        

        

                                    
            
        