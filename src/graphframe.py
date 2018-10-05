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
    
# STANDARD MODULES
from pprint import pprint as PRETTYPRINT

# Non-Standard Modules
import matplotlib
from matplotlib import font_manager
from matplotlib import ticker
from matplotlib.backends.backend_tkagg import FigureCanvas
from matplotlib.backend_tools import ToolBase, ToolToggleBase
from matplotlib.figure import Figure

#fontP = font_manager.FontProperties()
#fontP.set_family('Source Han')
#PRETTYPRINT(fontP.get_family())
#fontP.set_size(8)

font_path = r"C:\Windows\Fonts\malgun.ttf"
propF = font_manager.FontProperties(fname=font_path)
#matplotlib.font_manager.get_font("C:\\WINDOWS\\Fonts\\malgun.ttf", hinting_factor=None)

#PRETTYPRINT(matplotlib.font_manager.get_cachedir())

#matplotlib.font_manager._rebuild()
#matplotlib.rcParams['font.family'] = ['sans-serif']
#matplotlib.rcParams['font.sans-serif'] = ['Computer Modern Sans Serif']
#PRETTYPRINT(matplotlib.rcParams.keys())

from pprint import pprint as PRETTYPRINT
import logging
import datetime
import pandas as pd
import numpy as np

# Project Modules
from appwidget import AppWidget 

class GraphFrame(AppWidget):
    def __init__(self,parent,controller,config,dbvar=None, wd=14, ht=7.5):
        self.widget_name = "graphframe"
        
        self.lines_list = []
        self.bars_list = []
        self.event_polygon_list = []
        self.prime_graph_pack = None
        self.secondary_graph_pack = None
        
        super().__init__(parent,controller, config,dbvar=None)

        self.my_figure = Figure(figsize=(wd, ht), dpi=85)
        self.my_legend = self.my_figure.legend()

        self.axis_prime = self.my_figure.add_subplot(1, 1, 1)
#        self.axis_prime.set_title("No Query Selected")

        self.axis_secondary = self.my_figure.add_subplot(
            111, sharex=self.axis_prime, frameon=False)
        self.axis_secondary.xaxis.set_visible(False)
        self.axis_secondary.yaxis.set_label_position("right")   
        self.axis_secondary.yaxis.tick_right()

        self.canvas = FigureCanvas(self.my_figure, self)
        self.canvas.draw()
#        
#        self.canvas.manager.toolbar.add_tool('zoom', 'foo')
        
#        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self)
#        self.toolbar.update()
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

    def update_graph(self,gr_pk):
        
        """
        {'axis': 'left',
         'breakdown_colors': ['firebrick',
                              'dodgerblue',
                              'seagreen',
                              'darkorchid',
                              'gray',
                              'yellow',
                              'salmon',
                              'deeppink'],
         'color': '#a38bb6',
         'end': datetime.date(2018, 4, 1),
         'event_dates': [('04/29 Sale', '20180429', '20180429'),
                         ('05/01-05/06 Event', '20180501', '20180506'),
                         ('05/01-05/06 Event', '20180517', '20180520')],
         'force_y': (True, 0, 4),
         'gtype': 'date_series',
         'line_labels': ['PC', '모바일', 'm_PC', 'm_모바일'],
         'linestyles': '-',
         'met': 'Order Size',
         'start': datetime.date(2018, 3, 18),
         'str_x': 'Date (Average of 7-Day Periods)',
         'str_y': 'Order Size (Average)',
         'title': 'Average of Order Size (Exclude Cancelled Items) By Gen. Platform',
         'x_data': [datetime.date(2018, 3, 18),
                    datetime.date(2018, 3, 25),
                    datetime.date(2018, 4, 1)],
         'y_data': [[3.371877804372405, 3.330132851297275, 3.3963963963963963],
                    [2.5645786328057234, 2.5824528794692228, 2.647798742138365],
                    [3.6697965620085644, 3.371877804372405, 3.433628318584071],
                    [2.5361031401007033, 2.5645786328057234, 2.6683168316831685]]}
        """ 
        #       CLEAN UP AND RESET
        self.log("Update graph call.")
        
        self.clear_graph()

        # DETERMINE TARGET AXIS
        if gr_pk["axis"] == "left":
            target_axis = self.axis_prime
            
        elif gr_pk["axis"] == "right":
            target_axis = self.axis_secondary
            
        self.axis_prime.xaxis.set_visible(True)
        self.axis_prime.yaxis.set_visible(True)
        self.axis_prime.grid(b=True,which="major")

        self.prime_graph_pack = gr_pk
        other_pack = self.secondary_graph_pack
        self.log("target_axis: {} => self.axis_prime".format(gr_pk["axis"]))
            
#       TITLING
        if not other_pack:
            target_axis.set_title(gr_pk["title"])
            target_axis.xaxis.set_label_text(gr_pk["str_x"])
        elif other_pack:
            new_title = "{} vs. {}".format(self.prime_graph_pack["title"] ,
                                           self.secondary_graph_pack["title"]) 
            target_axis.set_title(new_title)
        
        target_axis.yaxis.set_label_text(gr_pk["str_y"])
     
#
##       GRAPH PRP
        gr_pk_colors = [gr_pk["color"]] +  gr_pk["breakdown_colors"]
#        PRETTYPRINT(gr_pk_colors)
        start = gr_pk["start"]
        end = gr_pk["end"]
        color_c = 0
        if gr_pk["gtype"] == "date_series":
            for x in range(0, len(gr_pk["y_data"])):
                try:
                    gr_pk_colors[x]
                except IndexError:
                    color_to_use = gr_pk_colors[x-10]
                else:
                    color_to_use= gr_pk_colors[x]
                    
                if "m_" in gr_pk["line_labels"][x]:
                    linewidth = 0.75
                else:
                    linewidth = 1.45
                self.lines_list.append(target_axis.plot_date(gr_pk["x_data"],
                                     gr_pk["y_data"][x],
                                     color=color_to_use,
                                     ls=gr_pk["linestyles"],
                                     lw=linewidth,
                                     label=gr_pk["line_labels"][x])[0])
#                print(self.line)
                color_c += 1

            target_axis.set_xlim(gr_pk["x_data"][0], gr_pk["x_data"][-1])

        elif gr_pk["gtype"] == "string-bar" or gr_pk["gtype"] == "bar":
            self.bars_list = target_axis.bar(gr_pk["x_data"],
                                gr_pk["y_data"][0],
                                color=gr_pk_colors[color_c]).patches
            color_c += 1   
        elif gr_pk["gtype"] == "pie":
            self.axis_prime.pie(gr_pk["y_data"][0],labels=gr_pk["x_data"])
#
#       POST PLOTTING FORMATTING
        if not gr_pk["gtype"] == "pie":
            # Y-AXIS FORMATTING            
            if gr_pk["force_y"][0]:
                target_axis.set_ylim(bottom=gr_pk["force_y"][1],top=gr_pk["force_y"][2])
            elif not gr_pk["force_y"][0]:
                if target_axis.get_ylim()[1] >= 1000:
                    target_axis.get_yaxis().set_major_formatter(
                    ticker.FuncFormatter(lambda x, p: format(int(x), ',')))    
                if target_axis.get_ylim()[0] <= 0:
                    target_axis.set_ylim(bottom=0)    
                    
            for tick in target_axis.get_xticklabels():
                tick.set_fontsize(8)
                tick.set_rotation(30)                       

    
            # EVENT HIGHLIGHTS
            if gr_pk["str_x"] == "Date":
#                event_colors = self.get_cfg_val("event_colors").split("-")
                invDisToAxFrac = self.axis_prime.transAxes.inverted()
                axis_left_lim = matplotlib.dates.num2date(self.axis_prime.get_xlim()[0]).date()   
                for e_index, event_tuple in enumerate(gr_pk["event_dates"]):
                    name_str = event_tuple[0]
                    start_str = event_tuple[1]
                    end_str = event_tuple[2]
                    
                    self.log("{}: {} -> {}".format(name_str,start_str,end_str))
                    start_date = datetime.date(int(start_str[0:4]),int(start_str[4:6]),int(start_str[6:8]))
                    end_date = datetime.date(int(end_str[0:4]),int(end_str[4:6]),int(end_str[6:8]))
                    axis_left_lim = matplotlib.dates.num2date(self.axis_prime.get_xlim()[0]).date()      
#                    if start_date < axis_left_lim:
#                        start_date = axis_left_lim
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
                    stagger_y = 0.95 - (0.10*e_index)                    
                    self.axis_prime.text(final_left_top[0]+ 0.01,stagger_y,
                        s=name_str,horizontalalignment="left",
                        transform=self.axis_prime.transAxes)
#
#    #       GENERAL FORMATTING

        self.my_legend = self.axis_prime.legend(
#                loc=0,
#                ncol=5,
                fontsize="x-small",
#                borderaxespad=-0.1,
                markerscale=0.6,
                framealpha=0.85,
                prop=propF)
#
        self.canvas.draw()
#        
        self.annot = self.axis_prime.annotate("", xy=(0,0), xytext=(-20,20),
                        textcoords="offset points", bbox=dict(boxstyle="round", 
                        fc="w"),arrowprops=dict(arrowstyle="->"),fontproperties=propF)
        self.annot.set_visible(False)
        self.canvas.mpl_connect("motion_notify_event", self.hover)        
        
        self.log("Completed Graphing.")
        
    def clear_graph(self,axis="both"):
        try:
            self.my_legend.remove()
        except BaseException:
            self.bug("My legend doesn't exist yet. Likely first time calling _update_plot()")

        self.lines_list = []
        self.bars_list = []
        self.event_polygon_list = []

        if axis == "both":
            self.axis_prime.cla()            
            self.axis_prime.yaxis.set_visible(False)
            self.axis_prime.grid(b=False)
                      
            self.axis_secondary.cla()

            self.axis_secondary.yaxis.set_visible(False)

            
