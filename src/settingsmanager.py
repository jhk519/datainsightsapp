# -*- coding: utf-8 -*-
"""
Created on Mon Oct  8 09:20:22 2018

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
from pprint import pprint as PRETTYPRINT
import logging
import os
import pickle
import datetime
import copy 
import codecs

# Project Modules    
from appwidget import AppWidget,CreateToolTip
import master_calendar.calendardialog as cal_dialog

class SettingsManager(AppWidget):
    def __init__(self,parent,controller,config,dbvar=None):
        self.widget_name = "settingsmanager"
        super().__init__(parent,controller,config,dbvar)
        self.engine = SettingsManagerEngine()
        
        # AppWidget will take settingmanager's specific cfg, but we
        # also need to store a copy of the "app"'s config separately.
        
        has_user_config = self.engine.load_full_config()
        if not has_user_config:
            self.full_config = config
            self.bug("User's user_config.pickle file is missing. Using default settings.")
        else:
            self.full_config = has_user_config
        
        self.setting_packs = []
        self.nums_indx = None
        self.nums_list = []
        self.evnt_indx = None
        self.events_list = []
        
        self.settings_menu = tk.LabelFrame(self, text="Menu")
        self.settings_menu.grid(row=0,column=0,sticky="nw")
        
        self.extra_window = tk.LabelFrame(self,text="More Details")
        self.extra_window.grid(row=0,column=1,sticky="nsew",padx=(15,0))
        tk.Label(self.extra_window,text=":)").grid()
        
        self.populate_settings_menu()
        self.build_entries()

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
        
    def get_latest_config(self,needcopy=True):
        if needcopy:
            return copy.deepcopy(self.full_config)
        return self.app_cfg          

    def save_events(self):
        self.log("Saving events, located at masterindex:{}".format(self.evnt_indx))
        all_events_str = ""
        temp_iter = []
        
        for event_tuple in self.events_list:
            add_str = ",".join([event_tuple[0].get(),event_tuple[1],event_tuple[2]])
            temp_iter.append(add_str)
        all_events_str = "%%".join(temp_iter)
        
        self.setting_packs[self.evnt_indx][2].set(all_events_str)
        self._ux_settings_changed(self.evnt_indx)     
        
    def set_new_color(self, settingrowcolumn):
        indexrow, indexcolor = settingrowcolumn
        self.log("Settings new color at indexrow: {}, indexcolor: {}".format(indexrow,indexcolor))
        section,setting,stvar, set_type, widget_list,rown = self.setting_packs[indexrow]
        get_color = colorchooser.askcolor()[1]
        widget_list[indexcolor]["background"] = get_color
        self._ux_settings_changed(indexrow)     
        
    def set_new_stvar_value(self,index):
        self.log("Validating and settings for index {}".format(index))
        section,setting,stvar, set_type, widget_list,rown = self.setting_packs[index]
        
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
            string = widget_list[0]["background"]
            for index, color_button in enumerate(widget_list[1:]):
                string = string + "-" + color_button["background"]
            stvar.set(string)        
        return True        
    
    def _ux_settings_changed(self,index):
        if self.set_new_stvar_value(index):
            self.update_full_config()
            self.engine.save_full_config(self.full_config)
            try:
                self.controller.propagate_cfg_var_change
                logging.info("Setting Page's Controller has .propagate_cfg_var_change method.")
            except:
                self.bug("No suitable controlelr to propagate_cfg_var")
            else:
                self.bug("Propagating updated settings to controller")
                self.controller.propagate_cfg_var_change(self.full_config)  
        else:
            self.bug("Error with setting new var at index: {}".format(index))
            
        return True       

    def update_full_config(self):
        for setting_pack in self.setting_packs:
            section,setting,stvar, set_type, empty_widget_list,rown = setting_pack
            python_val = self.engine._get_clean_val(stvar.get(),set_type)
            self.full_config[section][setting] = python_val    
            
    def open_numbers_list(self):
        self.log("Editing Events, located at index: {}".format(self.nums_indx))
        raw_nums_list = self.setting_packs[self.nums_indx][2].get().split("%%")

        self.extra_window["text"] = "Edit Ignore Numbers"
        self.nums_list = []
        
        for child in self.extra_window.winfo_children():
            child.destroy()  
            
#        raw_nums_list = ["010-0000-0000",
#                           "000-0000-0000",
#                           "010-000-0000",
#                           "010-1111-1111",
#                           "010-111-1111",
#                           "010-0000-0000",
#                           "nan",
#                           "0"]            
            
        rown = 0
        for num in raw_nums_list:
            namevar = tk.StringVar()
            namevar.set(num)
            name_str_widget = ttk.Entry(self.extra_window,textvariable=namevar)  
            name_str_widget.grid(row=rown,column=0,sticky="ew",
                                 columnspan=1,padx=(15,10),pady=(5,0))  
            rown += 1            
            
            self.nums_list.append(namevar)

        ttk.Button(self.extra_window,text="Add Number",command=self.add_num).grid(
                row=rown,column=0,sticky="nw",pady=(15,0),padx=(15,15))
        
        ttk.Button(self.extra_window,text="Save Number",command=self.save_nums).grid(
                row=rown,column=1,sticky="nw",columnspan=1,pady=(15,0))   
        
    def add_num(self):
        nums_str = self.setting_packs[self.nums_indx][2].get()
        nums_str += "%%000-000-000"
        self.setting_packs[self.nums_indx][2].set(nums_str)
        self.open_numbers_list()
        
    def save_nums(self):
        num_str = "%%".join([numvar.get() for numvar in self.nums_list])
        self.setting_packs[self.nums_indx][2].set(num_str)
        self._ux_settings_changed(self.nums_indx)
            
    def open_events_list(self):     
        self.log("Editing Events, located at index: {}".format(self.evnt_indx))

        self.events_list = []
        for child in self.extra_window.winfo_children():
            child.destroy()   
        events_tuples = self.setting_packs[self.evnt_indx][2].get().split("%%")
        
        for index, event in enumerate(events_tuples):
            event_parts = event.split(",")
            name_var = tk.StringVar(value=event_parts[0])
            start_date = event_parts[1]
            end_date = event_parts[2]
            self.events_list.append([name_var,start_date,end_date])  
            
        self.extra_window["text"] = "Edit Events"
        self.populate_extra_window_for_events()

    def populate_extra_window_for_events(self):
        real_row_count = 0
        for index, event in enumerate(self.events_list):
            namevar = event[0]
            start_date = event[1]
            end_date = event[2]
            
            arg = index,0
            name_str_widget = ttk.Entry(self.extra_window,textvariable=namevar)  
            name_str_widget.grid(row=real_row_count,column=0,sticky="ew",
                                 columnspan=1,padx=(15,10),pady=(5,0))  
            
            
            arg = index,1
            start_date_widget = ttk.Button(self.extra_window,text=start_date,
               command=lambda arg=arg: self.event_date_change(arg))  
            start_date_widget.grid(row=real_row_count,column=1,sticky="w",
                                   columnspan=1,padx=(10,0),pady=(5,0))      
            
            arg = index,2
            end_date_widget = ttk.Button(self.extra_window,text=end_date, 
               command=lambda arg=arg: self.event_date_change(arg))    
            end_date_widget.grid(row=real_row_count,column=2,sticky="w",
                                 columnspan=1,padx=(10,15),pady=(5,0)) 
            
    
            event_separator = ttk.Separator(self.extra_window)
            event_separator.grid(row=real_row_count+1,column=0,columnspan=3,sticky="ew"
                                   ,pady=(5,0),padx=10)       

            real_row_count += 2
            
        add_events_button = ttk.Button(self.extra_window,text="Add An Event",
            command=self.add_events)         
        add_events_button.grid(row=real_row_count,column=0,sticky="nw",pady=(15,0),padx=(15,15))
        
        save_events_button = ttk.Button(self.extra_window,text="Save Events",
            command=self.save_events)         
        save_events_button.grid(row=real_row_count,column=1,sticky="nw",columnspan=1,pady=(15,0))             
            
    
    def event_date_change(self,arg):
        eventindex,infotype = arg
        event_tuple = self.events_list[eventindex]
        event_info = event_tuple[infotype]
        year,month =  int(event_info[0:4]), int(event_info[4:6])
        date_calendar = cal_dialog.CalendarDialog(self,year=year, month=month)
        self.log("Getting new start date")
        try:
            result_date = date_calendar.result.date()
#            print(result_date)
        except AttributeError:
            self.bug("Date returned from calendar not functional: {}".format(result_date))
        self.events_list[eventindex][infotype] = result_date.strftime("%Y%m%d")
#        print(self.events_list)
        self.populate_extra_window_for_events()    
        
    def add_events(self):
         self.log("Adding event, located at masterindex:{}".format(self.evnt_indx))
         events_string = self.setting_packs[self.evnt_indx][2].get()     
         new_events_string = events_string + "%%New Event,20180101,20180101"
         self.setting_packs[self.evnt_indx][2].set(new_events_string)
         self.open_events_list() 
         
#    def add_num(self):
        
            
    def populate_settings_menu(self):
        self.log("Building settings.")
        
        rown = 0

        for section,section_cfg in self.get_config().items():
            section_separator = ttk.Separator(self.settings_menu)
            section_separator.grid(row=rown,column=0,columnspan=10,sticky="ew",
                                   padx=(5,45),pady=(15,10))   
            rown += 1
            
            section_label = tk.Label(self.settings_menu,text=section_cfg["proper_title"],font=("Helvetica", 12))
            section_label.grid(row=rown, column=0, sticky="wn", padx=(5,25)) 
            rown += 1

            for setting,setting_cfg in section_cfg["settings"].items():
                title_label = ttk.Label(self.settings_menu,text=setting_cfg["proper_title"])
                title_label.grid(row=rown, column=0, sticky="nw", padx=(15,25),pady=7)
                
                desc = setting_cfg["description"]
                s = CreateToolTip(title_label, desc)
                set_type = setting_cfg["type"]
                
                stvar = tk.StringVar()
                stvar.set(str(self.full_config[section][setting]))  
                empty_widget_list = []
                
                self.setting_packs.append([section,setting,stvar, set_type, empty_widget_list,rown]) 
                rown += 1
                
    def build_entries(self):
        frm = self.settings_menu
        
        for index, setting_pack in enumerate(self.setting_packs):
            section,setting,stvar, set_type, empty_widget_list,rown = setting_pack
            
            def_lambda = lambda index = index: self._ux_settings_changed(index)
            
            if set_type == "dirloc" or set_type == "fileloc":
                widget = ttk.Button(frm,command=def_lambda,textvariable=stvar)
                widget.grid(row=rown,column=1,sticky="w",columnspan=15) 
                empty_widget_list.append(widget)
              
            elif set_type == "bool":
                on_widget = ttk.Radiobutton(frm, variable=stvar, text="On",value="True", 
                                            command=def_lambda)
                on_widget.grid(row=rown,column=1,sticky="w",padx=(0,5),columnspan=10) 
                empty_widget_list.append(on_widget)
                
                off_widget = ttk.Radiobutton(frm, variable=stvar, text="Off",value="False",
                                             command=def_lambda)
                off_widget.grid(row=rown,column=3,sticky="w",padx=(0,5),columnspan=10)  
                empty_widget_list.append(off_widget)
                
            elif set_type == "colors": 
                split_colors = stvar.get().split("-")
                for clindex, color in enumerate(split_colors):
                    settingrowcolumn = (index,clindex)
                    color_lambda = lambda settingrowcolumn=settingrowcolumn: self.set_new_color(settingrowcolumn)
                    butt = tk.Button(frm, width=2, command=color_lambda, background=split_colors[clindex])
                    butt.grid(row=rown,column=clindex+1,sticky="w",padx=(0,5),pady=7)
                    empty_widget_list.append(butt)
                    
            elif set_type == "date":
                date_widget = ttk.Button(frm,command=def_lambda,textvariable=stvar)         
                date_widget.grid(row=rown,column=1,sticky="w",columnspan=15)
                empty_widget_list.append(date_widget)
                
            elif set_type == "int":
                days_widget = tk.Spinbox(frm, from_=1.0, to=30.0, wrap=True, width=4, 
                                         validate="key", state="readonly",
                                         textvariable = stvar, command=def_lambda)  
                days_widget.grid(row=rown,column=1,sticky="w",columnspan=15) 
                empty_widget_list.append(days_widget)
                
            elif set_type == "event_dates":
                self.evnt_indx = index
#                event_lambda = self.open_events_list
                edit_events_button = ttk.Button(frm,command=self.open_events_list,text="See Events List")  
                edit_events_button.grid(row=rown,column=1,sticky="w",columnspan=10)
                empty_widget_list.append(edit_events_button)
                
            elif set_type == "phone_numbers":
                self.nums_indx = index
                edit_numbers_button = ttk.Button(frm, command=self.open_numbers_list, text="See Ignore Numbers List")
                edit_numbers_button.grid(row=rown,column=1,sticky="w",columnspan=10)
                empty_widget_list.append(edit_numbers_button)
                
                
class SettingsManagerEngine():
    def __init__(self):    
        self.log = logging.getLogger(__name__).info
        self.log("Init.")
        self.bug = logging.getLogger(__name__).debug    
        
    def load_full_config(self):
        try:
            with open('user_config.pickle',"rb") as user_config:
                self.log("user_config pickle file found.")
                return pickle.load(user_config) 
        except FileNotFoundError:
            self.bug("No preset pickle file found. Skipping.")     
            return False
        
    def save_full_config(self,new_config):
        with open('user_config.pickle', 'wb') as dbfile:
            pickle.dump(new_config, dbfile) 
        
    def _get_clean_val(self,setting_val,setting_type):
        if setting_type == "bool":
            if setting_val == "True":
                val = True
            elif setting_val == "False":
                val = False
            else:
                self.bug("ERROR, {} NOT SUITABLE VAL: FOR {}".format(setting_val,setting_type))
                raise ValueError
        elif setting_type == "int":
            val = int(setting_val)
        elif setting_type in ["list","date","str","dirloc","fileloc","colors","event_dates","phone_numbers"]:
            val = setting_val
        else:
            self.bug("INVALID TYPE FOR SETTING! - {} - {}".format(setting_type, setting_val))
            val = None   
        return val                

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
    app = tk.Tk()
    test_widget = SettingsManager(app, app,controls_config)
    test_widget.grid(padx=20)
    app.mainloop()          