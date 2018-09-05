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
    import tkinter.colorchooser as colorchooser
    import tkinter as tk
    import tkinter.ttk as ttk
    

# Standard Modules
import configparser 
from pprint import pprint as PPRINT
import logging
import os
import pickle
import datetime

# Project Modules    
from appwidget import AppWidget
import master_calendar.calendardialog as cal_dialog
"""
settingsmanager acts as a way to make changes to the default config2 dictionary. 
it loads user_settings.ini, and parses the section header and the key:value pairs 
by config2[SECTION_HEADER][key] = value, it replaces the config2 dict in memory 
BUT DOES NOT make changes to it directly. 

When user makes change:
.validate_and_set() - rewrite ini, and replace on disk. 
.settings_changed()
    .update_settings
        .engine.load_ini_settings
    .controller.propagate_settings()
"""
class SettingsManager(AppWidget):
    def __init__(self,parent,controller,config,dbvar=None):
        self.widget_name = "settingsmanager"
        super().__init__(parent,controller,config,dbvar)
            
        self.parser = configparser.ConfigParser()    
        self.setting_packs = []
        
        self.parser.read("settings//user_settings.ini")  
        self.engine.load_cfg_files_and_set_new_cfg(self.parser._sections)
        
        self._build_settings()
        self._build_entries()
        
#        pprint(self.engine.get_config()["multigrapher"])
        
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=0)
        self.columnconfigure(4, weight=0)
        self.columnconfigure(5, weight=0)
        self.columnconfigure(6, weight=0)
        self.columnconfigure(7, weight=0)
        self.columnconfigure(8, weight=0)
        self.columnconfigure(9, weight=0)
        self.columnconfigure(10, weight=0)
        self.columnconfigure(11, weight=1)        
        
#   API
    def get_latest_config(self):
        return self.engine.get_config()   

    def receive_new_presets(self,presetpageslist):
        with open('settings//presets.pickle', 'wb') as dbfile:
            pickle.dump(presetpageslist, dbfile) 
        self.engine.load_cfg_files_and_set_new_cfg(self.parser._sections)
        
#   UX EVENT HANDLERS AND HELPERS
    
    def set_new_color(self, settingrowcolumn):
        indexrow, indexcolor = settingrowcolumn
        self.log("Settings new color at indexrow: {}, indexcolor: {}".format(indexrow,indexcolor))
        header, label, stvar, set_type, entry_list = self.setting_packs[indexrow]
        get_color = colorchooser.askcolor()[1]
        stvar.set(get_color)
        button = entry_list[indexcolor]
        button["background"] = get_color
        self._validate_and_set(indexrow)
        
    def _validate_and_set(self,index):
        self.log("Validating and settings for index {}".format(index))
        header, label, stvar, set_type, entry_list = self.setting_packs[index]
        if set_type == "dirloc":
            dirloc = tk.filedialog.askdirectory() 
            dirloc = os.path.relpath(dirloc)
            stvar.set(dirloc)
        elif set_type == "fileloc":
            fileloc = tk.filedialog.askopenfilename()   
            fileloc = os.path.relpath(fileloc)
            stvar.set(fileloc)            
        elif set_type == "date":
            date_calendar = cal_dialog.CalendarDialog(self)
            new_date = date_calendar.result.date()
            stvar.set(str(new_date).replace("-",""))
        elif set_type == "colors":
            string = entry_list[0]["background"]
            for index, color_button in enumerate(entry_list):
                if index == 0:
                    continue
                string = string + "-" + color_button["background"]
            stvar.set(string)
        curr_val = stvar.get()
        self.log("For setting: {}, curr_val now: {}".format(label["text"],curr_val))
        self.parser.set(header,label["text"],curr_val+"$$"+set_type)
        with open('settings//user_settings.ini', 'w') as configfile:
            self.parser.write(configfile)
        self.settings_changed()
        return 1
    
    def settings_changed(self):
        self.engine.load_cfg_files_and_set_new_cfg(self.parser._sections)
        try:
            self.controller.propagate_cfg_var_change
            logging.info("Setting Page's Controller has .propagate_cfg_var_change method.")
        except:
            self.bug("No suitable controlelr to propagate_cfg_var")
        else:
            self.bug("Propagating updated settings to controller")
            self.controller.propagate_cfg_var_change(self.engine.get_config())      
                               
#   BUILD FUNCTIONS            
    def _build_settings(self):
        self.log("Building settings.")
        frame_row = 0
        curr_section = ""
        for user_setting_tuple in self.engine.user_settings:
            section_header,setting_header,final_val,set_type = user_setting_tuple
            self.log("Building settings: {}-{} = {}".format(section_header,setting_header,final_val))
            if not curr_section == section_header:
                curr_section = section_header
                section_text = section_header.replace("_config","")
                
                section_separator = ttk.Separator(self)
                section_separator.grid(row=frame_row,column=0,columnspan=10,sticky="ew",
                                       padx=(0,45),pady=(10,5))   
                frame_row += 1
                
                section_label = tk.Label(self,text=section_text,font=("Helvetica", 12))
                section_label.grid(row=frame_row, column=0, sticky="wn", padx=(0,25)) 
                frame_row += 1
            stvar_check_var = tk.StringVar()
            stvar_check_var.set(str(final_val))
            
            title_label = ttk.Label(self,text=setting_header)
            title_label.grid(row=frame_row, column=0, sticky="nw", padx=(15,25),pady=7)
            
            new_pack = [section_header, title_label, stvar_check_var, set_type, []]
            self.setting_packs.append(new_pack)
            frame_row += 1  
            
    def _build_entries(self):
        self.log("Building entries")
        #For some reason, in order for the Entry widgets to initialize with
        #their StVars, we have to initialize the two separate, thus,
        #the above workaround   
        iter_row = 0
        curr_section = ""
        for index, setting_pack in enumerate(self.setting_packs):
            section_header = setting_pack[0]
            setting_header = setting_pack[1]
            stvar = setting_pack[2] 
            set_type = setting_pack[3] 
            emptywidgetlist = setting_pack[4]
            
            self.log("{}. Unpacking: {}-{} = {}".format(index,section_header,setting_header["text"],stvar.get()))
            
            if not curr_section == section_header:
                curr_section = section_header
                iter_row += 2            
            
            def_lambda = lambda index = index: self._validate_and_set(index)
            
            if set_type == "dirloc" or set_type == "fileloc":
                widget = ttk.Button(self,command=def_lambda,textvariable=stvar)
                widget.grid(row=iter_row,column=1,sticky="w",columnspan=15) 
                emptywidgetlist.append(widget)
              
            elif set_type == "bool":
                on_widget = ttk.Radiobutton(self, variable=stvar, text="On",value="True", 
                                            command=def_lambda)
                on_widget.grid(row=iter_row,column=1,sticky="w",padx=(0,5),columnspan=10) 
                emptywidgetlist.append(on_widget)
                
                off_widget = ttk.Radiobutton(self, variable=stvar, text="Off",value="False",
                                             command=def_lambda)
                off_widget.grid(row=iter_row,column=3,sticky="w",padx=(0,5),columnspan=10)  
                emptywidgetlist.append(off_widget)
                
            elif set_type == "colors": 
                split_colors = stvar.get().split("-")
                for clindex, color in enumerate(split_colors):
                    settingrowcolumn = (index,clindex)
                    color_lambda = lambda settingrowcolumn = settingrowcolumn: self.set_new_color(settingrowcolumn)
                    butt = tk.Button(self, width=2, command=color_lambda, background=split_colors[clindex])
                    butt.grid(row=iter_row,column=clindex+1,sticky="w",padx=(0,5))
                    emptywidgetlist.append(butt)
                    
            elif set_type == "date":
                date_widget = ttk.Button(self,command=def_lambda,textvariable=stvar)         
                date_widget.grid(row=iter_row,column=1,sticky="w",columnspan=15)
                emptywidgetlist.append(date_widget)
                
            elif set_type == "int":
                days_widget = tk.Spinbox(self, from_=1.0, to=30.0, wrap=True, width=4, 
                                         validate="key", state="readonly",
                                         textvariable = stvar, command=def_lambda)  
                days_widget.grid(row=iter_row,column=1,sticky="w",columnspan=15) 
                emptywidgetlist.append(days_widget)
            
            iter_row += 1 
                  
if __name__ == "__main__":
    logname = "debug-{}.log".format(datetime.datetime.now().strftime("%y%m%d"))
    ver = "v0.2.10.7 - 2018/07/22"
    
    logging.basicConfig(filename=r"debuglogs\\{}".format(logname),
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
#    dbfile =  open(r"databases/DH_DBS.pickle", "rb")
#    dbs = pickle.load(dbfile)  
    app = tk.Tk()
    test_widget = SettingsManager(app, app,controls_config)
    test_widget.grid(padx=20)
    app.mainloop()   
        

                                    
            
        