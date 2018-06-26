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
import configparser 
from pprint import pprint as PPRINT

# Project Modules    
from default_engines import SettingsManagerEngine

class SettingsManager(ttk.LabelFrame):
    def __init__(self,parent,controller=None,engine="default",config=None):
        super().__init__(parent)
        self.parent = parent
        if not controller:
            self.controller = parent
        else:
            self.controller = controller
            
        if str(engine) == "default":
            self.engine = SettingsManagerEngine()
        else:
            self.engine = engine         
            
        if config:
            self.engine.set_build_config(raw_config = config)  
            
        self.parser = configparser.ConfigParser()    
        self.setting_packs = []
            
        self.update_settings()
        self.build_settings()
        
#   API
    def get_config(self):
        return self.engine.get_config()        
        
#   UX EVENT HANDLERS AND HELPERS
    def update_settings(self):
        self.parser.read("fcfg.ini")       
        self.engine.load_ini_settings(self.parser._sections)

    def settings_changed(self,index):
        self.update_settings()
        try:
            self.controller.propagate_cfg_var_change
        except:
            print("No suitable controlelr to propagate_cfg_var")
        else:
            self.controller.propagate_cfg_var_change(self.engine.get_config())      
               
    def _validate_and_set(self,index):
        header, label, stvar, set_type, entry_list = self.setting_packs[index]
        curr_val = stvar.get()
        self.parser.set(header,label["text"],curr_val+":"+set_type)
        with open('fcfg.ini', 'w') as configfile:
            self.parser.write(configfile)
        self.settings_changed(index)
        return 1
            
#   BUILD FUNCTIONS    
    def build_settings(self):
        self._build_settings()
        self._build_entries()
        
    def _build_settings(self):
        frame_row = 0

        for user_setting_tuple in self.engine.user_settings:
            section_header,setting_header,final_val,set_type = user_setting_tuple
            
            stvar_check_var = tk.StringVar()
            stvar_check_var.set(str(final_val))
            
            title_label = ttk.Label(self,text=setting_header)
            title_label.grid(row=frame_row, column=0, sticky="nw", padx=(15,25),pady=7)
            
            new_pack = [section_header, title_label, stvar_check_var, set_type, []]
            self.setting_packs.append(new_pack)
            frame_row += 1  
            
    def _build_entries(self):
        #For some reason, in order for the Entry widgets to initialize with
        #their StVars, we have to initialize the two separate, thus,
        #the above workaround        
        for index, setting_pack in enumerate(self.setting_packs):
            section_header = setting_pack[0] 
            title_label = setting_pack[1] 
            stvar = setting_pack[2] 
            set_type = setting_pack[3] 
            entry_list = []
            
            lambdafunc = lambda index = index: self._validate_and_set(index)
            
            if set_type == "str":
                entry_list.append(ttk.Entry(self, textvariable=stvar,
                                            validate="focusout",
                                            validatecommand=lambdafunc,width=30))
            elif set_type == "bool":
                entry_list.append(ttk.Radiobutton(self, variable=stvar, text="Yes",
                                                  value="True", command=lambdafunc))
                
                entry_list.append(ttk.Radiobutton(self, variable=stvar, text="No",
                                                  value="False",
                                                  command=lambdafunc))
                    
            elif set_type == "list": 
                entry_list.append(ttk.Entry(self, textvariable=stvar,
                                            validate="key",
                                            validatecommand=lambdafunc, width=90))
                    
            elif set_type == "date":
                entry_list.append(ttk.Entry(self, textvariable=stvar,
                                            validate="focusout",
                                            validatecommand=lambdafunc, width=30))
                    
            elif set_type == "int":
                entry_list.append(tk.Spinbox(self, from_=1.0, to=30.0, wrap=True, 
                                             width=4, validate="key", state="readonly",    
                                             textvariable = stvar,
                                             command=lambdafunc))
                
            for colcount,value_widget in enumerate(entry_list):
                if type(value_widget) is ttk.Entry:
                    value_widget.grid(row=index,column=colcount+1,sticky="w",
                        columnspan=3)
                else:
                    value_widget.grid(row=index,column=colcount+1,sticky="w")     
        
if __name__ == "__main__":
    import config2
    dbcfg = config2.backend_settings
    app = tk.Tk()
    test_widget = SettingsManager(app, config=dbcfg)
    test_widget.grid(padx=20)
    app.mainloop()   
        

                                    
            
        