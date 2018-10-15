# -*- coding: utf-8 -*-
"""
Created on Thu Oct 11 09:03:41 2018

@author: Justin H Kim
"""
# Tkinter Modules
try:
    import Tkinter as tk
    import tkFont
    import ttk
except ImportError:  # Python 3
    import tkinter as tk
    import tkinter.font as tkFont
    import tkinter.ttk as ttk
    import tkinter.filedialog
    
# Standard Modules
import datetime
import base64
import os
import logging
from pprint import pprint as PRETTYPRINT
import pandas as pd
import time
import numpy as np

# Non-Standard Modules
import cryptography.fernet as fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Project Modules
import cafe24_queries
import master_calendar.calendardialog as cal_dialog
from appwidget import AppWidget

class Cafe24Manager(AppWidget):
    def __init__(self,parent,controller,config,dbvar=None,user="normal"):
        self.widget_name = "cafe24manager"
        self.user = user
        super().__init__(parent,controller,config,dbvar)     
        
        
        # TOKEN VARS
        self.token_doc_name = r"settings/tokens.txt"
        self.salt = b"\x97\xa1\x8dU\xe8\xad\xd6\x85\xa9\xc0\x7f\xd2+t\x9e\xfa"
        self.pass_var = tk.StringVar()
        self.last_update_var = tk.StringVar()
        self.last_update_var.set("NONE")
        self.expire_date_var = tk.StringVar()
        self.expire_date_var.set("NONE")        
        self.access_token_var = tk.StringVar()
        self.access_token_var.set("NONE")
        self.refresh_token_var = tk.StringVar()
        self.refresh_token_var.set("NONE")
        
        
        # FUNCTION VARS
        
        # ORDERS
        self.use_insights_headers = tk.BooleanVar()
        self.use_insights_headers.set(True)
        
        self.order_start_datetime = datetime.date(2018, 8, 1)
        self.order_end_datetime = datetime.date(2018, 8, 1)
        
        self.order_start_date_button_var = tk.StringVar()
        self.order_start_date_button_var.set(str(self.order_start_datetime))
        
        self.order_end_date_button_var = tk.StringVar()
        self.order_end_date_button_var.set(str(self.order_end_datetime)) 
        
        self.order_id_var = tk.StringVar()
        self.order_id_var.set("ORDER_ID,ORDER_ID,etc...")
        
        self.sales_volume_code = tk.StringVar()
        self.sales_volume_code.set("PRODUCT_CAFE24_CODE")
    
        self.tokens = {
            "last_update":"",
            "password":"",
            "access_token":"UkMxNaTfRSoEJuRb6HFhKB",
            "refresh_token":"LtGVwa0KO1zqUBrRr4SPpC",
            "auth_code":"",
            "expire_date":"",
        }
        
        self.tokens_frame = tk.LabelFrame(self,text="Authorization Tokens")
        self.tokens_frame.grid(row=0,column=0,sticky="nw",padx=(20,10),pady=(20,0))
        self.build_tokens_frame(self.tokens_frame)
        
        self.functions_frame = tk.LabelFrame(self,text="Functions")
        self.functions_frame.grid(row=1,column=0,sticky="new",padx=(20,10),pady=(10,20))
        self.build_functions_frame(self.functions_frame)
        
        self.toggle_functions_buttons(False)
        
    def get_order_id(self,string):
        return string.rsplit("-",1)[0]
            
    def ux_get_orders_full(self,gen_excel=True):
        self.log("Get Orders Items FULL Called.")
        failed_x_pages = []
        count_kwargs = {"start_date":self.order_start_date_button_var.get(),
                        "end_date":self.order_end_date_button_var.get()}
        
        total_count = cafe24_queries.main("get_order_count",self.tokens["access_token"],count_kwargs)
        self.log("Total orders: {}".format(total_count))
        
        req_pages = (total_count // 500) + 1
        if req_pages > 16:
            self.bug("CANNOT CALL MORE THAN 16 PAGES!")
            self.bug("Currently need {} pages for {} orders.".format(req_pages,total_count))
            return
        self.log("Required pages: {}".format(req_pages))

        order_kwargs = {"start_date":self.order_start_date_button_var.get(),
                        "end_date":self.order_end_date_button_var.get()}
        curr_orders_df = pd.DataFrame()
        order_items_dict_list = []
        
        for x in range(0,req_pages):
            self.log("Getting page: {} of {}...".format(x+1,req_pages))
            order_kwargs["offset"] = 500 * x
            orders_json = cafe24_queries.main("get_orders",self.tokens["access_token"],order_kwargs)
            for order_dict in orders_json:
                order_items_dict_list += order_dict["items"]
                order_dict.pop("items")
            append_df = pd.DataFrame(orders_json)
            curr_orders_df = pd.concat([curr_orders_df, append_df], axis=0, 
                                        ignore_index = True, join = "outer")          
        curr_order_items_df = pd.DataFrame(order_items_dict_list)
        
        curr_order_items_df['order_id'] = curr_order_items_df["order_item_code"].apply(self.get_order_id)      
        merged = pd.merge(curr_order_items_df, curr_orders_df, 
                          on="order_id", right_index=False,
                          how='left', sort=False)    
        
        
        
        if self.use_insights_headers.get():
            merged = self.get_translated_and_dropped_df(merged,self.get_cfg_val("header_reference"))
            merged = self.convert_all_date_columns(merged)
            
        merged = merged.loc[merged['date_payment'] != ""]
            
        self.__gen_df_excel(merged)
        
    def ux_get_orders(self,gen_excel=True):
        self.log("Get Orders Called.")
        failed_x_pages = []
        count_kwargs = {"start_date":self.order_start_date_button_var.get(),
                        "end_date":self.order_end_date_button_var.get()}
        total_count = cafe24_queries.main("get_order_count",self.tokens["access_token"],count_kwargs)
        self.log("Total orders: {}".format(total_count))
        req_pages = (total_count // 500) + 1
        if req_pages > 16:
            self.bug("CANNOT CALL MORE THAN 16 PAGES!")
            return
        self.log("Required pages: {}".format(req_pages))

        order_kwargs = {"start_date":self.order_start_date_button_var.get(),
                        "end_date":self.order_end_date_button_var.get()}
        
        curr_df = pd.DataFrame()
        for x in range(0,req_pages):
            self.log("Getting page: {} of {}...".format(x+1,req_pages))
            order_kwargs["offset"] = 500 * x
            orders_json = cafe24_queries.main("get_orders",self.tokens["access_token"],order_kwargs)
            append_df = pd.DataFrame(orders_json)
            curr_df = pd.concat([curr_df, append_df], axis=0, 
                                 ignore_index = True, join = "outer")
            
        self.log("Compiling all pages...")
        self.bug(failed_x_pages)
        cols = list(curr_df.columns.values) #Make a list of all of the columns in the df
        cols.pop(cols.index("order_id")) #Remove b from list
        curr_df = curr_df[["order_id"] + cols]  
        if gen_excel:           
            self.__gen_df_excel(curr_df)   
        else:
            return curr_df
        
    def ux_get_order_items_use_excel(self):
        pathstr = tk.filedialog.askopenfilename()
        init_df = pd.read_excel(pathstr, 0)
        if "order_id" in init_df.columns:
            col_series = init_df["order_id"]
        else:
            col_series = init_df.iloc[:,0]
        self.ux_get_order_items(set(col_series))
        
    def ux_get_order_items(self,order_ids=None,gen_excel=True):
        self.log("Get Order Items Called")
        failed_requests = []
        if order_ids is None:
            clean_entry = self.order_id_var.get().strip().replace(" ", "").replace("\n", "")
            ids_set = set(clean_entry.split(","))
        else:
            ids_set = order_ids
            
        curr_df = pd.DataFrame()
        for index,order_id in enumerate(ids_set):
            self.log("Getting order_items for id: {}, {} out of {}".format(order_id,index,len(ids_set)))
            if len(failed_requests) > 10:
                self.bug("Too many failed requests, stopping.")
                break
            response = cafe24_queries.main("get_order_items",self.tokens["access_token"],
                                              {"order_id":order_id })
            handled = self.response_handler(response,curr_df)
            
            if type(handled) is str:
                if handled == "try_again":
                    response_again = cafe24_queries.main("get_order_items",self.tokens["access_token"],
                                              {"order_id":order_id })
                    handled_again = self.response_handler(response_again,curr_df)
                    if type(handled_again) is str:
                        failed_requests.append(order_id)
                    elif type(handled_again) is pd.DataFrame:
                        curr_df = handled_again
                elif handled == "error":
                    failed_requests.append(order_id)
            elif type(handled) == pd.DataFrame:
                curr_df = handled
                
        self.bug("\n".join(failed_requests))
        cols = list(curr_df.columns.values) #Make a list of all of the columns in the df
        cols.pop(cols.index("order_item_code")) #Remove b from list
        curr_df = curr_df[["order_item_code"] + cols]                
    
        if gen_excel:
            if curr_df.shape[0] > 10:
                self.__gen_df_excel(curr_df,transpose=False)
            else:
                self.__gen_df_excel(curr_df,transpose=True)
        else:
            return curr_df
            
    def ux_get_sales_volume(self):
        pcode = self.sales_volume_code.get()
        response = cafe24_queries.main("get_product",self.tokens["access_token"],
                                              {"product_code":pcode })
        product_nom = response[0]["product_no"]
        sales_volume_kwargs = {"start_date":self.order_start_date_button_var.get(),
                               "end_date":self.order_end_date_button_var.get(),
                               "product_no":product_nom}
        response_sales = cafe24_queries.main("get_sales_volume",self.tokens["access_token"],
                                             sales_volume_kwargs)
#        print(response_sales)
        handled = self.response_handler(response_sales,pd.DataFrame())
        self.__gen_df_excel(handled)
        
     
        
    def ux_apply_password(self):
        self.set_new_encrytion_suite()
                
        if self._open_tokens_doc():
            self.refresh_tokens_statuses(True)
            self.toggle_functions_buttons(True)
        else:
           self.refresh_tokens_statuses(False) 
           self.toggle_functions_buttons(False)
           
    def ux_refresh_access_token(self):
        response_json = cafe24_queries.main("new_refresh",self.tokens["refresh_token"],{})
        PRETTYPRINT(response_json)
        self.tokens["access_token"] = response_json["access_token"]
        self.tokens["refresh_token"] = response_json["refresh_token"]
        self.tokens["expire_date"] = response_json["expires_at"].replace("T"," ").replace(":","-")
#        self.set_new_encrytion_suite()
        self.rewrite_tokens_doc()
        self._open_tokens_doc()
        self.refresh_tokens_statuses(True)
        
    def _ux_open_order_cal(self,which_cal):
        self.log("Getting new cal date")
        if which_cal == "start":
            the_datetime = self.order_start_datetime
            the_date_var = self.order_start_date_button_var
        else:
            the_datetime = self.order_end_datetime
            the_date_var = self.order_end_date_button_var
        get_calendar = cal_dialog.CalendarDialog(self, year=the_datetime.year,
                                                 month=the_datetime.month)
        try:
            the_datetime = get_calendar.result.date()
        except AttributeError:
            self.log("Start date probably set to None.")
        else:
            if which_cal == "start":
                self.order_start_datetime = the_datetime
            else:
                self.order_end_datetime = the_datetime            
            the_date_var.set(str(the_datetime))           
        
        
    # INTERNAL FUNCTIONS 
    
    def response_handler(self,response,curr_df):
        if type(response) is str:
            self.bug(response)
            if "Call limit" in response:
                self.bug("Sleeping 25 seconds.")
                time.sleep(25)
                
                return "try_again"
            elif "404" in response:
                time.sleep(15)
                return "error"
            else:
                return "error"
        else:
            order_items_df = pd.DataFrame(response) 
            curr_df = pd.concat([curr_df, order_items_df], axis=0, 
                                 ignore_index = True, join = "outer")
            return curr_df             

    def get_translated_and_dropped_df(self,init_df,header_ref):
        init_df.rename(
            columns=lambda x: x.strip().replace(" ", "").replace("\n", ""), inplace=True)
        for header in list(init_df):
            if header not in header_ref and header not in header_ref.values():
                init_df = init_df.drop(labels=header, axis=1)
            else:
                continue
        init_df.rename(columns=header_ref, inplace=True)
        
        return init_df        
    
    def convert_all_date_columns(self,curr_df):
        curr_df = curr_df.fillna(0)
        for column_name in curr_df.columns:
            if "date" in column_name:
#                print(column_name)
                curr_df[column_name] = curr_df[column_name].apply(lambda x: self.convert_to_date(x))
            elif column_name == "cancel_status":
                curr_df[column_name] = curr_df[column_name].apply(lambda x: self.convert_cancel_date_to_cancel_status(x))
        return curr_df
    
    def convert_to_date(self,string):
        if string == 0:
            return ""
        else:
            a_str = string[0:10]
            datetime_obj = datetime.datetime.strptime(a_str, "%Y-%m-%d")
            return datetime_obj
    
    def convert_cancel_date_to_cancel_status(self,cancel_date):
#        self.bug(cancel_date)
        if cancel_date == 0:
            return "취소안함"
        else:
            return "부분취소"
    
    def __gen_df_excel(self,df,transpose=False,open_excel=True):
#        time_str = datetime.datetime.now().strftime("%y%m%d-%H%M%S")    
        if self.get_cfg_val("automatic_db_export"):
            fullname = self.get_export_full_name("cafe24result")
#            self.log(".export_db_csb auto-fullname: {}".format(fullname))
        else:
            dir_loc = tk.filedialog.asksaveasfilename() 
            fullname = dir_loc + ".xlsx"
            self.bug("_export_db_csv manual fullname: {}".format(fullname))        

        if transpose:
            df = df.transpose()
        df.to_excel(fullname)
        self.log("Completed Excel Export...")
        if open_excel:
            self.log("Opening Excel...")
            os.system('start excel.exe "%s"' % (fullname)) 
            
    def set_new_encrytion_suite(self):
        self.tokens["password"] = self.pass_var.get()
        byte_pw = self.tokens["password"].encode()
        self.kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=self.salt,iterations=100000,
                         backend=default_backend())         
        self.fernetter = fernet.Fernet(base64.urlsafe_b64encode(self.kdf.derive(byte_pw)))        
           
    def refresh_tokens_statuses(self,open_file_ok):
        if open_file_ok:
            self.last_update_var.set(self.tokens["last_update"])
            self.expire_date_var.set(self.tokens["expire_date"])
            self.access_token_var.set("OK")
            self.refresh_token_var.set("OK")
        else:
            self.last_update_var.set("ERROR - Likely Invalid Password or Corrupted Encryptions")
            self.expire_date_var.set("ERROR - Likely Invalid Password or Corrupted Encryptions")
            self.access_token_var.set("ERROR - Likely Invalid Password or Corrupted Encryptions") 
            self.refresh_token_var.set("ERROR - Likely Invalid Password or Corrupted Encryptions")          
            
    def _open_tokens_doc(self):
        print("---")
        fin = open(self.token_doc_name,"rb")
        gen = (line for line in fin)
        
        for line in gen:
            plaintext = ""
            try:
                plaintext = self.fernetter.decrypt(line).decode()
            except fernet.InvalidToken:
                print("error line: {}".format(line.decode()))
                return False
            for string in plaintext.split("$$%%"):
                clean_tuple = string.split(":")
                if clean_tuple[0] == "ACCESS_TOKEN":
                    self.tokens["access_token"] = clean_tuple[1]
                elif clean_tuple[0] == "REFRESH_TOKEN":
                    self.tokens["refresh_token"] = clean_tuple[1] 
                elif clean_tuple[0] == "DATE":
                    self.tokens["last_update"] = clean_tuple[1]
                elif clean_tuple[0] == "EXPIRE_DATE":
                    self.tokens["expire_date"] = clean_tuple[1]
                print("{}:{}".format(clean_tuple[0],clean_tuple[1]))
        print("---")                
        return True
        
    def rewrite_tokens_doc(self,acc="",ref=""):
        if acc == "" and ref == "":
            acc = self.tokens["access_token"]
            ref = self.tokens["refresh_token"]
            exp = self.tokens["expire_date"].replace("T"," ")
            
        self.set_new_encrytion_suite()         
        
        with open(self.token_doc_name, 'wb') as the_file:
            time_str = datetime.datetime.now().strftime("%Y-%B-%d %H-%M-%S")
            join_list = ["DATE:"+time_str,"EXPIRE_DATE:"+exp,"ACCESS_TOKEN:"+acc,"REFRESH_TOKEN:"+ref]
            byte_seq = self.fernetter.encrypt("$$%%".join(join_list).encode())
            the_file.write(byte_seq)     
            
#        with open("tokens.txt", 'wb') as the_file:
#            time_str = datetime.datetime.now().strftime("%Y-%B-%d %H-%M-%S")
#            join_list = ["DATE:"+time_str,"EXPIRE_DATE:"+exp,"ACCESS_TOKEN:"+acc,"REFRESH_TOKEN:"+ref]
#            byte_seq = self.fernetter.encrypt("$$%%".join(join_list).encode())
#            the_file.write(byte_seq)              
    
#    def str_to_enc_bytes(self,left_str,str_data):
#        access_tokenized = self.fernetter.encrypt(left_str.encode() + str_data.encode())
#        return access_tokenized   
    
    def toggle_functions_buttons(self,toggle):
        for child in self.functions_frame.winfo_children():
            if type(child) == tk.Button:
                if "ADMIN" in child["text"] and self.user == "normal":
                    child["state"] = "disabled"
                    continue
                if toggle:
                    child["state"] = "active"
                else:
                    child["state"] = "disabled"
            if type(child) == tk.Entry:
                if toggle:
                    child["state"] = "normal"
                else:
                    child["state"] = "disabled"     
                    
#    def clean_cafe24_date(self,date_str):
#        tpl = date_str.split("T")
#        date = tpl[0]
#        time = tpl[1]
                    
    # BUILD FUNCTIONS
    
    def build_tokens_frame(self,targ_frame):
        rown=0
        tk.Label(targ_frame,text="Enter Encryption Password:").grid(
                row=rown,column=0)
        password_entry = tk.Entry(targ_frame,textvariable=self.pass_var,show="*")
        password_entry.grid(row=rown,column=1,sticky="w")
        
        tk.Button(targ_frame,text="Apply",command=self.ux_apply_password).grid(
                row=rown,column=2,padx=(8,5),sticky="w")
        rown += 1
        
        tk.Label(targ_frame,text="Last Refresh Date and Time: ").grid(
                row=rown,column=0,sticky="w",padx=(8,5))
        tk.Label(targ_frame,textvariable=self.last_update_var).grid(
                row=rown,column=1,columnspan=2,sticky="w")
        rown += 1
        
        tk.Label(targ_frame,text="Access Token Expire Date: ").grid(
                row=rown,column=0,sticky="w",padx=(8,5))
        tk.Label(targ_frame,textvariable=self.expire_date_var).grid(
                row=rown,column=1,columnspan=2,sticky="w")
        rown += 1        
        
        tk.Label(targ_frame,text="Access-Token Decryption:").grid(
                row=rown,column=0,sticky="w",padx=(8,5))
        tk.Label(targ_frame,textvariable=self.access_token_var).grid(
                row=rown,column=1,columnspan=2,sticky="w")
        rown += 1
        
        tk.Label(targ_frame,text="Refresh-Token Decryption:").grid(
                row=rown,column=0,sticky="w",padx=(8,5))
        tk.Label(targ_frame,textvariable=self.refresh_token_var).grid(
                row=rown,column=1,columnspan=2,sticky="w")
        rown += 1
         

        rewrite_button = tk.Button(targ_frame,text="Rewrite Token Encryption File\nADMIN ONLY!",
                            command=self.rewrite_tokens_doc)
        rewrite_button.grid(row=rown,column=0,sticky="w",padx=(10,5),pady=(8,5))
        if self.user == "normal":
            rewrite_button["state"] = "disabled"
        else:
            rewrite_button["state"] = "active"
            
        rown += 1             
        
    def build_functions_frame(self,targ_frame):
        rown = 0

        
        tk.Button(targ_frame,text="Refresh Access-Token - ADMIN ONLY",command=self.ux_refresh_access_token).grid(
                  row=rown,column=0,columnspan=2,sticky="w",padx=(10,0),pady=(8,5))
        rown += 1


        tk.Label(targ_frame,text="Dates (Orders & Sales Volume):").grid(
                row=rown,column=0,sticky="w",padx=(8,5))           
        tk.Button(targ_frame,command=lambda: self._ux_open_order_cal("start"), 
                  textvariable=self.order_start_date_button_var).grid(
    			row=rown, column=1,columnspan=1, padx=(0,5),pady=(8,5),sticky="w")   
        
        tk.Button(targ_frame,command=lambda: self._ux_open_order_cal("end"),
                  textvariable=self.order_end_date_button_var).grid(
    			row=rown, column=2,columnspan=1, padx=(0,10),pady=(8,5),sticky="w") 
        rown += 1        
        
        tk.Button(targ_frame,text="Get Orders",command=self.ux_get_orders).grid(
                row=rown,column=0,sticky="w",padx=(10,0),pady=(8,5))
        rown += 1
        
        tk.Button(targ_frame,text="Get Order Items FULL",command=self.ux_get_orders_full).grid(
                row=rown,column=0,sticky="w",padx=(10,0),pady=(8,5))

        ttk.Checkbutton(targ_frame, text="Convert to Insights Headers", variable=self.use_insights_headers,
                onvalue=True,offvalue=False).grid(row=rown, column=1,columnspan=2, sticky="w",padx=(8,0))
        rown += 1
        
        tk.Entry(targ_frame,textvariable=self.sales_volume_code,width=30).grid(
                row=rown,column=0, columnspan=1,sticky="w",padx=(10,5),pady=(8,5))
        tk.Button(targ_frame,text="<- Get Sales Volume",command=self.ux_get_sales_volume).grid(
            row=rown,column=1,columnspan=2,sticky="w",padx=(0,5),pady=(8,5))     
        rown += 1     
        
        tk.Entry(targ_frame,textvariable=self.order_id_var,width=30).grid(
                row=rown,column=0, columnspan=1,sticky="w",padx=(10,5),pady=(8,5))
        tk.Button(targ_frame,text="<- Get Order Items",command=self.ux_get_order_items).grid(
            row=rown,column=1,columnspan=2,sticky="w",padx=(0,5),pady=(8,5))     
        rown += 1
        
        tk.Button(targ_frame,text="Get Order Items By Excel",command=self.ux_get_order_items_use_excel).grid(
            row=rown,column=0,columnspan=2,sticky="w",padx=(10,5),pady=(8,5))        
        rown += 1        
        
        targ_frame.columnconfigure(0,weight=0)
        targ_frame.columnconfigure(1,weight=0)
        targ_frame.columnconfigure(2,weight=1)  
        targ_frame.columnconfigure(3,weight=1)  
        targ_frame.columnconfigure(4,weight=0)  
        targ_frame.columnconfigure(5,weight=0)  
        
if __name__ == "__main__":
    
    logname = "debug-{}.log".format(datetime.datetime.now().strftime("%y%m%d"))
    ver = "v0.0.1 - 2018/10/11"
    if not os.path.exists(r"debug\\"):
        os.mkdir(r"debug\\")
    logging.basicConfig(filename=r"debug\\{}".format(logname),
        level=logging.DEBUG, 
        format="%(asctime)s %(name)s:%(lineno)s - %(funcName)s() %(levelname)s || %(message)s",
        datefmt='%H:%M:%S')
    logging.info("-------------------------------------------------------------")
    logging.info("DEBUGLOG @ {}".format(datetime.datetime.now().strftime("%y%m%d-%H%M")))
    logging.info("VERSION: {}".format(ver))
    logging.info("AUTHOR:{}".format("Justin H Kim"))
    logging.info("-------------------------------------------------------------")
    logging.info("PPBCafe24App module initialized...")
    
    app = Cafe24Manager("Admin")
    logging.info("App Initialized...")
    
#    app.state("zoomed")
    app.title("PPB Cafe24 API App - {}".format(ver))
    app.mainloop()
    logging.info("app.mainloop() terminated.")
    


