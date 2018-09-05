# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 12:57:01 2018

@author: Taken from github
"""

import master_calendar.ttkcalendar
import master_calendar.tkSimpleDialog

class CalendarDialog(master_calendar.tkSimpleDialog.Dialog):
    """Dialog box that displays a calendar and returns the selected date"""
    def body(self, master):
        self.calendar = master_calendar.ttkcalendar.Calendar(master)
        self.calendar.pack()

    def apply(self):
        self.result = self.calendar.selection
