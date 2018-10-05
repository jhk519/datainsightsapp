# -*- coding: utf-8 -*-
"""
Created on Wed May  2 22:57:53 2018

@author: Justin H Kim

settingsmanager acts as a way to make changes to the default config2 dictionary. 
it loads user_settings.ini, and parses the section header and the key:value pairs 
by config2[SECTION_HEADER][key] = value, it replaces the config2 dict in memory 
BUT DOES NOT make changes to it directly. 

When user makes change:
(Possible setting change handler before validating, see: .set_new_color )
.validate_and_set() - rewrite ini, and replace on disk. 
.reload_ini_and_propagate_new_cfg()
    .update_settings
        .engine.load_ini_settings
    .controller.propagate_settings()
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
import copy 

# Project Modules    
from appwidget import AppWidget,CreateToolTip
import master_calendar.calendardialog as cal_dialog

class SettingsManager(AppWidget):
    def __init__(self,parent,controller,config,dbvar=None):
        self.widget_name = "settingsmanager"
        super().__init__(parent,controller,config,dbvar)
            
        self.parser = configparser.ConfigParser()   
        self.app_cfg = config
        self.setting_packs = []
        self.user_settings = []
        
        self.events_list = []
        
        self.parser.read("settings//user_settings.ini")  
        self.app_cfg, self.user_settings = self.engine.get_updated_config(self.app_cfg, self.parser._sections)
        
        
        self.settings_menu = tk.LabelFrame(self, text="Menu")
        self.settings_menu.grid(row=0,column=0,sticky="w")
        self._build_settings(self.settings_menu)
        self._build_entries(self.settings_menu)
        
        self.extra_window = tk.LabelFrame(self,text="More Details")
        self.extra_window.grid(row=0,column=1,sticky="nsew")
        
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
        
# ================================================================
# ================================================================
#       API
# ================================================================
# ================================================================   
        
    def get_latest_config(self,needcopy=True):
        if needcopy:
            return copy.deepcopy(self.app_cfg)
        return self.app_cfg   

    def set_new_presets(self,presetpageslist):
        self.log("Setting new presets")
        with open('settings//presets.pickle', 'wb') as dbfile:
            pickle.dump(presetpageslist, dbfile) 
        self.user_settings = []            
        self.app_cfg, self.user_settings = self.engine.get_updated_config(self.app_cfg, self.parser._sections)
        
# ================================================================
# ================================================================
#       UX EVENT 
# ================================================================
# ================================================================   
        
    def event_date_change(self,arg):
        eventindex,infotype = arg
        event_tuple = self.events_list[eventindex]
        event_info = event_tuple[infotype]
        year,month =  int(event_info[0:4]), int(event_info[4:6])
        date_calendar = cal_dialog.CalendarDialog(self,year=year, month=month)
        self.log("Getting new start date")
        try:
            result_date = date_calendar.result.date()
        except AttributeError:
            self.bug("Date returned from calendar not functional: {}".format(result_date))
        self.events_list[eventindex][infotype] = result_date.strftime("%Y%m%d")
        self.populate_extra_window_for_events(self.events_list)
    
    def edit_events(self,masterindex):
        self.log("Editing Events, located at index: {}".format(masterindex))
        self.events_list = []
        
        events_string = self.setting_packs[masterindex][2].get()
        
        for index, event in enumerate(events_string.split("%%")):
            event_parts = event.split(",")
            name_var = tk.StringVar(value=event_parts[0])
            start_date = event_parts[1]
            end_date = event_parts[2]
            self.events_list.append([name_var,start_date,end_date])            
        self.extra_window["text"] = "Edit Events"
        
        for child in self.extra_window.winfo_children():
            child.destroy()        
 
        last_row = self.populate_extra_window_for_events(self.events_list,index)
        
        add_events_button = ttk.Button(self.extra_window,text="Add An Event",
            command=lambda index=index: self.add_events(masterindex))         
        add_events_button.grid(row=last_row,column=0,sticky="nw",pady=(15,0),padx=(15,15))
        
        save_events_button = ttk.Button(self.extra_window,text="Save Events",
            command=lambda index=index: self.save_events(masterindex))         
        save_events_button.grid(row=last_row,column=1,sticky="nw",columnspan=1,pady=(15,0))  
        
    def populate_extra_window_for_events(self,events_list,masterindex=0):

        real_row_count = 0
        for index, event in enumerate(events_list):
            namevar = event[0]
            start_date = event[1]
            end_date = event[2]
            
            arg = index,0
            name_str_widget = ttk.Entry(self.extra_window,textvariable=namevar)  
            name_str_widget.grid(row=real_row_count,column=0,sticky="ew",
                                 columnspan=1,padx=(15,10),pady=(15,0))  
            
            
            arg = index,1
            start_date_widget = ttk.Button(self.extra_window,text=start_date,
               command=lambda arg=arg: self.event_date_change(arg))  
            start_date_widget.grid(row=real_row_count,column=1,sticky="w",
                                   columnspan=1,padx=(10,0),pady=(15,0))      
            
            arg = index,2
            end_date_widget = ttk.Button(self.extra_window,text=end_date, 
               command=lambda arg=arg: self.event_date_change(arg))    
            end_date_widget.grid(row=real_row_count,column=2,sticky="w",
                                 columnspan=1,padx=(10,15),pady=(15,0)) 
            
    
            event_separator = ttk.Separator(self.extra_window)
            event_separator.grid(row=real_row_count+1,column=0,columnspan=3,sticky="ew"
                                   ,pady=(15,0))       

            real_row_count += 2
            
        return real_row_count
    
    def add_events(self,masterindex):
         self.log("Adding event, located at masterindex:{}".format(masterindex))
         events_string = self.setting_packs[masterindex][2].get()     
         new_events_string = events_string + "%%New Event,20180101,20180101"
         self.setting_packs[masterindex][2].set(new_events_string)
         
         self.edit_events(masterindex)

    def save_events(self,masterindex):
        self.log("Saving events, located at masterindex:{}".format(masterindex))
        all_events_str = ""
        temp_iter = []
        
        for event_tuple in self.events_list:
            add_str = ",".join([event_tuple[0].get(),event_tuple[1],event_tuple[2]])
#            self.log("Adding {}".format(add_str))
            temp_iter.append(add_str)
        all_events_str = "%%".join(temp_iter)
        
        self.setting_packs[masterindex][2].set(all_events_str)
        self._validate_and_set(masterindex)
#        self.log("Final string: {}".format(all_events_str))
            
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
            last_dt = stvar.get()
            yr,mo = int(last_dt[0:4]),int(last_dt[4:6])
            date_calendar = cal_dialog.CalendarDialog(self,year=yr, 
                                                      month=mo)
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
        try:
            self.log("For setting: {}, curr_val now: {}".format(label["text"],curr_val))
        except UnicodeEncodeError:
            self.log("For setting: {}, curr_Val changed.".format(label["text"],curr_val))
        self.parser.set(header,label["text"],set_type+"$$"+curr_val)
        with open('settings//user_settings.ini', 'w') as configfile:
            self.parser.write(configfile)
        self.reload_ini_and_propagate_new_cfg()
        return 1
    
    def reload_ini_and_propagate_new_cfg(self):
        self.app_cfg, self.user_settings = self.engine.get_updated_config(self.app_cfg, self.parser._sections)
        try:
            self.controller.propagate_cfg_var_change
            logging.info("Setting Page's Controller has .propagate_cfg_var_change method.")
        except:
            self.bug("No suitable controlelr to propagate_cfg_var")
        else:
            self.bug("Propagating updated settings to controller")
            self.controller.propagate_cfg_var_change(self.app_cfg)          
                   
# ================================================================
# ================================================================
#       BUILD 
# ================================================================
# ================================================================   
           
    def _build_settings(self,frame):
        self.log("Building settings.")
        frame_row = 0
        curr_section = ""
        for user_setting_tuple in self.user_settings:
            section_header,setting_header,final_val,set_type = user_setting_tuple
            self.log("Building settings: {}-{} = {}".format(section_header,setting_header,final_val))
            if not curr_section == section_header:
                curr_section = section_header
                section_text = section_header.replace("_config","")
                
                section_separator = ttk.Separator(frame)
                section_separator.grid(row=frame_row,column=0,columnspan=10,sticky="ew",
                                       padx=(0,45),pady=(10,5))   
                frame_row += 1
                
                section_label = tk.Label(frame,text=section_text,font=("Helvetica", 12))
                section_label.grid(row=frame_row, column=0, sticky="wn", padx=(0,25)) 
                
                
                frame_row += 1
            stvar_check_var = tk.StringVar()
            stvar_check_var.set(str(final_val))
            
            title_label = ttk.Label(frame,text=setting_header)
            title_label.grid(row=frame_row, column=0, sticky="nw", padx=(15,25),pady=7)
            
            try:
                s = CreateToolTip(title_label, self.get_cfg_val("descriptions")[section_header][setting_header])
            except KeyError:
                self.bug("Missing settingsmanager description for: {}-{}".format(section_header,setting_header))
            section_header,setting_header
            new_pack = [section_header, title_label, stvar_check_var, set_type, []]
            self.setting_packs.append(new_pack)
            frame_row += 1  
            
    def _build_entries(self,frame):
        self.log("Building entries")
        #For some reason, in order for the Entry widgets to initialize with
        #their StVars, we have to initialize the two separate, thus,
        #the above workaround   
        # new_pack = [section_header, title_label, stvar_check_var, set_type, []]
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
                widget = ttk.Button(frame,command=def_lambda,textvariable=stvar)
                widget.grid(row=iter_row,column=1,sticky="w",columnspan=15) 
                emptywidgetlist.append(widget)
              
            elif set_type == "bool":
                on_widget = ttk.Radiobutton(frame, variable=stvar, text="On",value="True", 
                                            command=def_lambda)
                on_widget.grid(row=iter_row,column=1,sticky="w",padx=(0,5),columnspan=10) 
                emptywidgetlist.append(on_widget)
                
                off_widget = ttk.Radiobutton(frame, variable=stvar, text="Off",value="False",
                                             command=def_lambda)
                off_widget.grid(row=iter_row,column=3,sticky="w",padx=(0,5),columnspan=10)  
                emptywidgetlist.append(off_widget)
                
            elif set_type == "colors": 
                split_colors = stvar.get().split("-")
                for clindex, color in enumerate(split_colors):
                    settingrowcolumn = (index,clindex)
                    color_lambda = lambda settingrowcolumn = settingrowcolumn: self.set_new_color(settingrowcolumn)
                    butt = tk.Button(frame, width=2, command=color_lambda, background=split_colors[clindex])
                    butt.grid(row=iter_row,column=clindex+1,sticky="w",padx=(0,5))
                    emptywidgetlist.append(butt)
                    
            elif set_type == "date":
                date_widget = ttk.Button(frame,command=def_lambda,textvariable=stvar)         
                date_widget.grid(row=iter_row,column=1,sticky="w",columnspan=15)
                emptywidgetlist.append(date_widget)
                
            elif set_type == "int":
                days_widget = tk.Spinbox(frame, from_=1.0, to=30.0, wrap=True, width=4, 
                                         validate="key", state="readonly",
                                         textvariable = stvar, command=def_lambda)  
                days_widget.grid(row=iter_row,column=1,sticky="w",columnspan=15) 
                emptywidgetlist.append(days_widget)
                
            elif set_type == "event_dates":
                event_lambda = lambda index = index: self.edit_events(index)
                edit_events_button = ttk.Button(frame,command=event_lambda,text="Edit Events")  
                edit_events_button.grid(row=iter_row,column=1,sticky="w",columnspan=10)

#                    iter_row += 1
                    
#                    end_date_widget = ttk.Button(self,command=def_lambda,textvariable=)  
#                    end_date_widget.grid(row=iter_row,column=2,sticky="w",columnspan=1)                    
                    
            iter_row += 1 

if __name__ == "__main__":
    logname = "debug-{}.log".format(datetime.datetime.now().strftime("%y%m%d"))
    ver = "v0.2.10.7 - 2018/07/22"
    
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
    controls_config = config2.backend_settings
#    dbfile =  open(r"databases/DH_DBS.pickle", "rb")
#    dbs = pickle.load(dbfile)  
    app = tk.Tk()
    test_widget = SettingsManager(app, app,controls_config)
    test_widget.grid(padx=20)
    app.mainloop()   
        

                                    
            
        