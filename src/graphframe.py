# -*- coding: utf-8 -*-
"""
Created on Thu May 31 16:36:43 2018

@author: Justin H Kim
"""
# Tkinter Modules
try:
    import Tkinter as tk
    import ttk
except ImportError:  # Python 3
    import tkinter as tk
    import tkinter.ttk as ttk

# Non-Standard Modules
from matplotlib import ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from pprint import pprint as PRETTYPRINT
import logging
import datetime

log = logging.getLogger(__name__).info
log("{} Init.".format(__name__))    
bug = logging.getLogger(__name__).debug   

class GraphFrame(tk.LabelFrame):
    def __init__(self, parent, wd=11, ht=7):
        super().__init__(parent, text='Graph')

        self.my_figure = Figure(figsize=(wd, ht), dpi=85)

        self.axis_prime = self.my_figure.add_subplot(1, 1, 1)
        self.axis_prime.set_title("No Query Selected")

        self.my_legend = self.my_figure.legend()

        self.axis_secondary = self.my_figure.add_subplot(
            111, sharex=self.axis_prime, frameon=False)

        self.canvas = FigureCanvasTkAgg(self.my_figure, self)
        self.canvas.draw()

        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        self.toolbar.update()
        self.canvas._tkcanvas.pack()

    def update_graph(self,analysis_pack ):
        #       CLEAN UP AND RESET
        log("Update graph call.")
        prp, srp= analysis_pack      
        prev_prime_y_axis_lims = self.axis_prime.get_ylim()
        prev_secondary_y_axis_lims = self.axis_secondary.get_ylim()

        try:
            self.my_legend.remove()
        except BaseException:
            bug("My legend doesn't exist yet. Likely first time calling _update_plot()")

        self.axis_prime.cla()
        self.axis_secondary.cla()
        self.axis_secondary.xaxis.set_visible(False)
        self.axis_secondary.yaxis.set_visible(False)

#       PREPARE NEW RESULTS
        """
        rp  = {
            "start":start,
            "end":end,
            "met": axis["metric"],
            "gtype": axis["gtype"],
            "str_x": pack["x_axis_label"],
            "str_y": axis["metric"],
            "line_labels":ls_queries,
            "x_data": x_data,
            "y_data": y_data_lists,
            "colors":colors_to_plot,
            "title": None or string
            "linestyles":[STYLESTR,STYLESTR]
            "event_dates":[('20180522',1),('20180601',5)]
        }
        """
        if prp:
            try: 
                prp["y_data"][0]
            except IndexError:
                title = "No Results for these Dates"
                text ="No results for the selected date range filters."
                self.create_popup(title,text)
                return None
        else:
            bug("WARNING! User searched for no queries in prp")
            return None
        
#       TITLING
        if prp["title"]:
            title = prp["title"]
        else:
            title = prp["met"]
            if srp:
                title += " vs. " + srp["met"]
        self.axis_prime.set_title(title)

        self.axis_prime.xaxis.set_label_text(prp["str_x"])
        self.axis_prime.yaxis.set_label_text(prp["str_y"])

#       GRAPH PRP
        prp_colors = prp["colors"]
        start = prp["start"]
        end = prp["end"]
        color_c = 0
#        print("GTYPE ", prp["gtype"])
#        print(prp["gtype"])
        if prp["gtype"] == "line":
            for x in range(0, len(prp["y_data"])):
                if "_Mirror" in prp["line_labels"][x]:
                    linewidth = 0.85
                else:
                    linewidth = 1.45
                self.axis_prime.plot(prp["x_data"],
                                     prp["y_data"][x],
                                     color=prp_colors[color_c],
                                     ls=prp["linestyles"][x],
                                     lw=linewidth,
                                     label=prp["line_labels"][x])
                color_c += 1

            self.axis_prime.set_xlim(prp["x_data"][0], prp["x_data"][-1])

        elif prp["gtype"] == "string-bar" or prp["gtype"] == "bar":
            self.axis_prime.bar(prp["x_data"],
                                prp["y_data"][0],
                                color=prp_colors[color_c])
            self.axis_prime.set_xlim(prp["x_data"][0], prp["x_data"][-1])
            color_c += 1   
        elif prp["gtype"] == "pie":
            self.axis_prime.pie(prp["y_data"][0],labels=prp["x_data"])

        if srp:
            self.axis_secondary.yaxis.set_visible(True)
            self.axis_secondary.yaxis.tick_right()
            self.axis_secondary.yaxis.set_label_position("right")
            self.axis_secondary.yaxis.set_label_text(srp["str_y"])            
            srp_colors = srp["colors"]
            color_c = 0
            if srp["gtype"] == "line":
                for x in range(0, len(srp["y_data"])):
                    if "_Mirror" in srp["line_labels"][x]:
                        linewidth = 0.85
                    else:
                        linewidth = 1.45                 
                    self.axis_secondary.plot(srp["x_data"],
                                             srp["y_data"][x],
                                             color=srp_colors[color_c],
                                             ls=srp["linestyles"][x],
                                             lw=linewidth,
                                             label=srp["line_labels"][x])
                    color_c += 1

            elif srp["gtype"] == "string-bar" or "bar":
                self.axis_secondary.bar(srp["x_data"],
                                        srp["y_data"][0],
                                        srp_colors[color_c])
                self.axis_secondary.set_xlim(
                    srp["x_data"][0], srp["x_data"][-1])
                color_c += 1

#       POST PLOTTING FORMATTING
        if not prp["gtype"] == "pie":
            # Y-AXIS FORMATTING            
            if prp["set_y"][0]:
                self.axis_prime.set_ylim(bottom=prp["set_y"][1],top=prp["set_y"][2])
            elif not prp["set_y"][0]:
                if self.axis_prime.get_ylim()[1] >= 1000:
                    self.axis_prime.get_yaxis().set_major_formatter(
                    ticker.FuncFormatter(lambda x, p: format(int(x), ',')))    
                if self.axis_prime.get_ylim()[0] <= 0:
                    self.axis_prime.set_ylim(bottom=0)       
                    
            if srp:
                if srp["set_y"][0]:
                    self.axis_secondary.set_ylim(bottom=srp["set_y"][1],top=srp["set_y"][2])
                elif not srp["set_y"][0]:
                    if self.axis_secondary.get_ylim()[1] >= 1000:
                        self.axis_secondary.get_yaxis().set_major_formatter(
                        ticker.FuncFormatter(lambda x, p: format(int(x), ',')))    
                    if self.axis_secondary.get_ylim()[0] <= 0:
                        self.axis_secondary.set_ylim(bottom=0)                     
            for tick in self.axis_prime.get_xticklabels():
                tick.set_fontsize(8)
                tick.set_rotation(30)
                
            # EVENT HIGHLIGHTS
            for date_tuple in prp["event_dates"]:
                start_str = date_tuple[0]
                end_str = date_tuple[1]
                start_date = datetime.date(int(start_str[0:4]),int(start_str[4:6]),int(start_str[6:8]))
                end_date = datetime.date(int(end_str[0:4]),int(end_str[4:6]),int(end_str[6:8]))
                
                self.axis_prime.axvspan(start_date, end_date, alpha=0.3, color='red',lw=4)
#            self.axis_prime.axvspan(datetime(2018,4,29), datetime(2018,5,20), alpha=0.5, color='blue')
            
            
    #       GENERAL FORMATTING
            self.axis_prime.grid(b=True)
            self.axis_secondary.grid(b=False)
            self.my_legend = self.my_figure.legend(
                loc='lower right',
                ncol=3,
                fontsize="small",
                borderaxespad=0.5,
                framealpha=0.85
            )

        self.canvas.draw()

#        PREP FINAL MERGED DATA PACK
        if srp:
            labels = [prp["str_x"]] + prp["line_labels"] + srp["line_labels"]
            datas = [prp["x_data"]] + prp["y_data"] + srp["y_data"]
        else:
            labels = [prp["str_x"]] + prp["line_labels"]
            datas = [prp["x_data"]] + prp["y_data"]

        merged_export_results_pack = {
            "start":start,
            "end":end,
            "title": title,
            "line_labels": labels,
            "data_list_of_lists": datas
        }
        log("Completed merged results pack.")
        return merged_export_results_pack
