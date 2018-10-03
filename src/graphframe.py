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
import matplotlib
from matplotlib import ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
matplotlib.rcParams['font.sans-serif'] = ['Source Han Sans TW', 'sans-serif']
from pprint import pprint as PRETTYPRINT
import logging
import datetime
import pandas as pd
import numpy as np

# Project Modules
from appwidget import AppWidget 

class GraphFrame(AppWidget):
    def __init__(self,parent,controller,config,dbvar=None, wd=14, ht=8):
        self.widget_name = "graphframe"
        super().__init__(parent,controller, config,dbvar=None)

        self.my_figure = Figure(figsize=(wd, ht), dpi=85)

        self.axis_prime = self.my_figure.add_subplot(1, 1, 1)
        self.axis_prime.set_title("No Query Selected")

        self.my_legend = self.my_figure.legend()

        self.axis_secondary = self.my_figure.add_subplot(
            111, sharex=self.axis_prime, frameon=False)

        self.canvas = FigureCanvasTkAgg(self.my_figure, self)
        self.canvas.draw()
        
        self.lines_list = []
        self.bars_list = []
        self.event_polygon_list = []

        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        self.toolbar.update()
        self.canvas._tkcanvas.pack()
        
    def update_annot(self,hover_obj,ind,kind="line"):
        text = "DEFAULT"
        if kind == "line":
            x,y = hover_obj.get_data() 
            coords = (x[ind["ind"][0]], y[ind["ind"][0]])
            yshort = '%.2f' % coords[1]
            self.annot.xy = coords
            text = "{}\n{},{}".format(hover_obj.get_label(),coords[0],yshort)
            self.annot.set_text(text)
            self.annot.get_bbox_patch().set_alpha(0.4)
        elif kind == "bar":
            coords = hover_obj.get_xy()
            ynew = coords[1] + hover_obj.get_height()
            self.annot.xy = coords[0]+hover_obj.get_width()/2,ynew
            text = "{}-{}".format(self.axis_prime.get_xticklabels()[ind].get_text(),ynew)
            self.annot.set_text(text)
            self.annot.get_bbox_patch().set_alpha(0.4)                   
    
    
    def hover(self,event):
        vis = self.annot.get_visible()
        if str(event.inaxes) == str(self.axis_prime): 
            for line2d in self.lines_list:
                cont, ind = line2d.contains(event) 
                if cont:
                    self.update_annot(line2d, ind)
                    self.annot.set_visible(True)
                    self.canvas.draw_idle()
                    return
            for index, rec in enumerate(self.bars_list):
                cont,ind = rec.contains(event)
                if cont:
                    self.update_annot(rec, index,kind="bar")
                    self.annot.set_visible(True)
                    self.canvas.draw_idle()
                    return

        if vis:
            self.annot.set_visible(False)
            self.canvas.draw_idle()                    

    def update_graph(self,analysis_pack ):
        #       CLEAN UP AND RESET
        self.log("Update graph call.")
        self.lines_list = []
        self.event_polygon_list = []
        prp = analysis_pack      
        srp = None
        try:
            self.my_legend.remove()
        except BaseException:
            self.bug("My legend doesn't exist yet. Likely first time calling _update_plot()")

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
#        PRETTYPRINT(prp)
        if prp:
            try: 
                prp["y_data"][0]
            except IndexError:
                title = "No Results for these Dates"
                text ="No results for the selected date range filters."
                self.create_popup(title,text)
                return None
        else:
            self.bug("WARNING! User searched for no queries in prp")
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
        if prp["gtype"] == "date_series":
            for x in range(0, len(prp["y_data"])):
                if "m_" in prp["line_labels"][x]:
                    linewidth = 0.75
                else:
                    linewidth = 1.45
                self.lines_list.append(self.axis_prime.plot_date(prp["x_data"],
                                     prp["y_data"][x],
                                     color=prp_colors,
                                     ls=prp["linestyles"],
                                     lw=linewidth,
                                     label=prp["line_labels"][x])[0])
#                print(self.line)
                color_c += 1

            self.axis_prime.set_xlim(prp["x_data"][0], prp["x_data"][-1])

        elif prp["gtype"] == "string-bar" or prp["gtype"] == "bar":
            self.bars_list = self.axis_prime.bar(prp["x_data"],
                                prp["y_data"][0],
                                color=prp_colors[color_c]).patches
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

#       POST PLOTTING FORMATTING
        if not prp["gtype"] == "pie":
            # Y-AXIS FORMATTING            
#            if prp["set_y"][0]:
#                self.axis_prime.set_ylim(bottom=prp["set_y"][1],top=prp["set_y"][2])
#            elif not prp["set_y"][0]:
#                if self.axis_prime.get_ylim()[1] >= 1000:
#                    self.axis_prime.get_yaxis().set_major_formatter(
#                    ticker.FuncFormatter(lambda x, p: format(int(x), ',')))    
#                if self.axis_prime.get_ylim()[0] <= 0:
#                    self.axis_prime.set_ylim(bottom=0)       
                    
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
            if prp["str_x"] == "Date":
#                event_colors = self.get_cfg_val("event_colors").split("-")
                invDisToAxFrac = self.axis_prime.transAxes.inverted()
                axis_left_lim = matplotlib.dates.num2date(self.axis_prime.get_xlim()[0]).date()   
                for e_index, event_tuple in enumerate(prp["event_dates"]):
                    name_str = event_tuple[0]
                    start_str = event_tuple[1]
                    end_str = event_tuple[2]
                    
                    self.log("{}: {} -> {}".format(name_str,start_str,end_str))
                    start_date = datetime.date(int(start_str[0:4]),int(start_str[4:6]),int(start_str[6:8]))
                    end_date = datetime.date(int(end_str[0:4]),int(end_str[4:6]),int(end_str[6:8]))
                    axis_left_lim = matplotlib.dates.num2date(self.axis_prime.get_xlim()[0]).date()      
                    if start_date < axis_left_lim:
                        start_date = axis_left_lim
                    event_polygon = self.axis_prime.axvspan(start_date, end_date, 
                                    alpha=0.08, color="red",lw=7,linestyle=(115,(20,2)))
                    self.event_polygon_list.append(event_polygon)
                    
                    left_top = event_polygon.get_verts()[1]
                    right_top = event_polygon.get_verts()[2]
                    # from display to axis decimal-fraction                    
                    ax_left_top = invDisToAxFrac.transform(left_top)
                    ax_right_top = invDisToAxFrac.transform(right_top)

                    final_left_top = list(ax_left_top)
                    if ax_left_top[0] <= 0:
                        if ax_right_top[0] < 0:
                            continue
                        else:
                            final_left_top[0] = 0
                    elif ax_left_top[0] >= 1:
                        self.log("Too far in future, skipping.")
                        continue
                    self.log("LEFT: {} -> {} -> {}".format(left_top,ax_left_top,final_left_top))
                    self.log("RIGHT: {} -> {}".format(right_top,ax_right_top))                     
                    self.axis_prime.text(final_left_top[0]+ 0.01, 0.95,
                        s=name_str,horizontalalignment="left",
                        transform=self.axis_prime.transAxes)

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
        
        self.annot = self.axis_prime.annotate("", xy=(0,0), xytext=(-20,20),
#                        xycoords="data",
                        textcoords="offset points", bbox=dict(boxstyle="round", 
                        fc="w"),arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)
        self.canvas.mpl_connect("motion_notify_event", self.hover)        

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
        self.log("Completed merged results pack.")
        return merged_export_results_pack
    
