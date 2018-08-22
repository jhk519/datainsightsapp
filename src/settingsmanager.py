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

# Project Modules    
from default_engines import SettingsManagerEngine
import master_calendar.calendardialog as cal_dialog

class SettingsManager(ttk.LabelFrame):
    def __init__(self,parent,controller=None,engine="default",config=None):
        super().__init__(parent)
        
        self.parent = parent
        if not controller:
            self.controller = parent
        else:
            self.controller = controller
            
        self.log = logging.getLogger(__name__).info
        self.log("{} Init.".format(__name__))    
        self.bug = logging.getLogger(__name__).debug             
            
        if str(engine) == "default":
            self.engine = SettingsManagerEngine()
        else:
            self.engine = engine         
            
        if config:
            self.engine.set_build_config(raw_config = config)  
            
        self.parser = configparser.ConfigParser()    
        self.setting_packs = []
            
        self.update_settings()
        
        self._build_settings()
        self._build_entries()
        
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
    def get_config(self):
        return self.engine.get_config()        
        
#   UX EVENT HANDLERS AND HELPERS
    def update_settings(self):
        self.parser.read("user_settings.ini")       
        self.engine.load_ini_settings(self.parser._sections)

    def settings_changed(self,index):
        self.update_settings()
        try:
            self.controller.propagate_cfg_var_change
            logging.info("Setting Page's Controller has .propagate_cfg_var_change method.")
        except:
            print("No suitable controlelr to propagate_cfg_var")
        else:
            print("Propagating updated settings to controller")
            self.controller.propagate_cfg_var_change(self.engine.get_config())      
               
    def _validate_and_set(self,index):
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
        self.parser.set(header,label["text"],curr_val+"$$"+set_type)
        with open('user_settings.ini', 'w') as configfile:
            self.parser.write(configfile)
        self.settings_changed(index)
        return 1
    
    def set_new_color(self, indexrow, indexcolor):
        header, label, stvar, set_type, entry_list = self.setting_packs[indexrow]
        get_color = colorchooser.askcolor()[1]
        stvar.set(get_color)
        button = entry_list[indexcolor]
        button["background"] = get_color
        self._validate_and_set(indexrow)
        
#   BUILD FUNCTIONS            
    def _build_settings(self):
        frame_row = 0
        curr_section = ""
        for user_setting_tuple in self.engine.user_settings:
            section_header,setting_header,final_val,set_type = user_setting_tuple
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
        #For some reason, in order for the Entry widgets to initialize with
        #their StVars, we have to initialize the two separate, thus,
        #the above workaround   
        iter_row = 0
        curr_section = ""
        for index, setting_pack in enumerate(self.setting_packs):
            section_header = setting_pack[0]
            stvar = setting_pack[2] 
            set_type = setting_pack[3] 
            emptywidgetlist = setting_pack[4]
            
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
                    color_lambda = lambda clindex = clindex: self.set_new_color(index, clindex)
                    butt = tk.Button(self, width=2, command=color_lambda,background=split_colors[clindex])
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
    import config2
    dbcfg = config2.backend_settings
    app = tk.Tk()
    test_widget = SettingsManager(app, config=dbcfg)
    test_widget.grid(padx=20)
    app.mainloop()   
        

                                    
            
        