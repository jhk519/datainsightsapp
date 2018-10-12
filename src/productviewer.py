# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 19:42:58 2018

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
from pprint import pprint
import pickle
import datetime
import logging
from os import system
import webbrowser

# Non-standard Modules
import PIL
from PIL import ImageTk
import urllib

#Package Modules
from appwidget import AppWidget


class ProductViewer(AppWidget):
    def __init__(self,parent,controller,config,dbvar=None):
        self.widget_name = "productviewer"
        super().__init__(parent,controller,config,dbvar)     
        self.engine = ProductViewerEngine()              

        self.product_detail_packs = []
        self.sku_detail_packs = []
#        Required to keep images in memory for tkinter to render
        self.current_images = [None,None]          
        
        self._build_search_frame()
        self._build_product_info_frame()
        self._build_sku_frame()
        
#   UX EVENT HANDLERS AND HELPERS        
        
    def export_customers(self,code=None):
#        codetype = self.search_type_menu.get() 
        if code == None:
            code = self.product_detail_packs[0][1].get().strip().replace(" ", "").replace("\n", "")
        self.log("Exporting orders for product: {}".format(code))
        temp_odb = self.get_dbvar()["odb"]
        export_customer_result = self.engine.get_customers_list(temp_odb, code)
        try:
            self.export_to_csv(code,export_customer_result)
        except AttributeError:
            self.bug("export_customer_result is not a df, it is a {}".format(str(type(export_customer_result))))
            if export_customer_result == "no_results":
                self.bug("No Results for Export Customers Search for: {}".format(code))
                title = "No Results for this Product Code"
                text ="No results for {} in database.".format(code)
                self.create_popup(title,text)
                return
            elif export_customer_result == "no_code_given":
                self.bug("No code given for product search.")
                return "no_code_given"
        else:
            self.log("Completed Customer List export for: {}".format(code))
            
    def export_to_csv(self,code,dataframe):
        dbstr = "product_customers_{}".format(code)
        fullname = self.get_export_full_name(dbstr,ftype="excel")
        dataframe.to_excel(fullname, sheet_name=code)
        system('start excel.exe "%s"' % (fullname))
        
    def search_product(self,code=None):
        codetype = self.search_type_menu.get() 
        if code == None:
            code = self.search_pcode_stvar.get().strip().replace(" ", "").replace("\n", "")
        self.log("Searching for product: {} and type: {}".format(code,codetype))
        pdb = self.get_dbvar()["pdb"]
        search_product_result = self.engine.search_product(pdb,code,codetype)
        if search_product_result == "no_results":
            title = "No Results".format(codetype)
            text ="No Results for {} {} in database.".format(codetype, code)
            self.create_popup(title,text)            
            return
        elif search_product_result == "no_code_given":
            self.bug("No code given for product search.")
        else:
            self.update_product_info(search_product_result) 
            
    def search_cafe24(self):
        code = self.search_pcode_stvar.get().strip().replace(" ", "").replace("\n", "")
        webbrowser.open("https://chuu.co.kr/product/search.html?keyword={}".format(code))
            
    def update_product_info(self,product_dict):
        self._clear_data()
        
#       UPDATE PRODUCT FRAME DETAILS      
        for stvar_tpl in self.product_detail_packs:
            key = stvar_tpl[0]
            detail_var = stvar_tpl[1]
            detail_var.set(product_dict["product_info"][key])

#       UPDATE MAIN IMAGE 
        p_url = product_dict["product_info"]["main_image_url"]
        self.log("Updating Main Product Image")
        self._update_label_image(self.main_image_url_label,p_url,0) 

#       UPDATE SKU FRAME
        row_c = 1
        for sku_tpl in product_dict["sku_list"]:
            
            barcode,color,size,url = sku_tpl
            
            barc_lbl = ttk.Label(self.sku_frame,text=barcode)
            barc_lbl.grid(row=row_c,column=0,sticky="w",padx=8) 
            
            colorbt = ttk.Button(self.sku_frame, text=color,
                command=lambda url = url: self._update_label_image(
                    self.sku_image_label,
                    url,1))
            colorbt.grid(row=row_c,column=1,sticky="w",padx=8)
            
            size_lbl = ttk.Label(self.sku_frame,text=size)     
            size_lbl.grid(row=row_c,column=2,sticky="w",padx=8)
            row_c += 1

            self.sku_detail_packs.append((barc_lbl,colorbt,size_lbl))
        self.log("Invoking first SKU photo button.")
        self.sku_detail_packs[0][1].invoke()
   
    def _clear_data(self):
        self.main_image_url_label["image"] = ""
        self.sku_image_label["image"] = ""
        for tpl in self.product_detail_packs:
            tpl[1].set("")
            
        for tpl in self.sku_detail_packs:
            for x in tpl:
                x.grid_forget()
        self.sku_detail_packs = []       

    def _update_label_image(self, labelobj,url,curr_img_index):
        """ 
        Receives a label object (either main or SKU) and the curr_img_index
        from functions that update those photos. 
        The curr_img_index is used for the self.current_images array of 2 length
        that is just there to hold the images in memory.
        """
        TKim = self.engine.get_PIL_image(url)     
        if TKim:
            labelobj["image"] = TKim   
        elif TKim == None:
            labelobj["image"] = ""
        self.current_images[curr_img_index] = TKim
        
#   BUILD FUNCTIONS
    def _build_search_frame(self):
        self.search_frame = ttk.LabelFrame(self,text="Search")
        self.search_frame.grid(row=0,column=0,sticky="ew",pady=15)
        
        self.search_pcode_stvar = tk.StringVar()   
        self.search_pcode_stvar.set("P000BAZV")
        
        self.search_pcode_label = ttk.Label(self.search_frame,text="Search")
        self.search_pcode_label.grid(row=0,column=0)       
        
        self.search_type_var = tk.StringVar()
        
        self.search_type_menu = ttk.Combobox(self.search_frame, textvariable=self.search_type_var,
                                          width=17,values=["Product Code","Barcode"],state="readonly")
        self.search_type_menu.grid(row=0, column=1,columnspan=1,pady=(5,5), sticky="w",
                                padx=(5,5))

        self.search_type_menu.bind('<<ComboboxSelected>>',self.selclear)
        self.search_type_menu.current(0)
        self.search_type_menu.selection_clear()        

        self.search_entry = ttk.Entry(
            self.search_frame, 
            width=15, 
            textvariable=self.search_pcode_stvar
        )
        self.search_entry.grid(row=0, column=2, padx=5,sticky="w")    
        
        self.search_button = ttk.Button(
            self.search_frame,
            text = "Search",
            command = self.search_product
        )
        self.search_button.grid(row=0,column=3,padx=5,sticky="w")
        

        
    def selclear(self,e):
        self.search_type_menu.selection_clear()        
        
    def _build_product_info_frame(self):
        self.product_info_frame = ttk.LabelFrame(self,text="Product Information")
        self.product_info_frame.grid(row=1,column=0,sticky="ewn")
        
        self.product_info_frame.columnconfigure(0,weight=0)
        self.product_info_frame.columnconfigure(1,weight=0)        
        self.product_info_frame.columnconfigure(2,weight=1)   
        
        required_details = ["product_cafe24_code",
                            "category"]
        start_row = 1   
        for key in required_details:
            detail_var = tk.StringVar()
            detail_label = ttk.Label(self.product_info_frame,text = key)
            detail_label.grid(row=start_row,column=0,sticky="w")
            detail_value = ttk.Label(self.product_info_frame,textvariable = detail_var)
            detail_value.grid(row=start_row,column=1,sticky="w")
            start_row += 1
            self.product_detail_packs.append([key,detail_var,detail_value])
            
        self.export_customers_button = ttk.Button(
            self.product_info_frame,
            text = "Export Customers List",
            command = self.export_customers
        )
        self.export_customers_button.grid(row=start_row,column=0,padx=5,sticky="w")    

        self.search_cafe24_button = ttk.Button(
            self.product_info_frame,
            text = "Search Code in Cafe24",
            command = self.search_cafe24
        )
        self.search_cafe24_button.grid(row=start_row,column=1,padx=5,sticky="w")    
        start_row += 1

        self.main_image_url_label = ttk.Label(self.product_info_frame,text = "Image URL")        
        self.main_image_url_label.grid(row=0,column=3,rowspan=10,sticky="e",padx=15)
             

    def _build_sku_frame(self):
        self.sku_frame = ttk.LabelFrame(self,text="SKU Information")
        self.sku_frame.grid(row=1, column=1, sticky="wne",padx=15)
        
        self.sku_frame.columnconfigure(0,weight=0)
        self.sku_frame.columnconfigure(1,weight=0)        
        self.sku_frame.columnconfigure(2,weight=0)      
        self.sku_frame.columnconfigure(3,weight=1) 
        
        self.barcodes_col_label = ttk.Label(self.sku_frame,text="Barcode")
        self.barcodes_col_label.grid(row=0,column=0,sticky="w")
        
        self.color_col_label = ttk.Label(self.sku_frame,text="Color")
        self.color_col_label.grid(row=0,column=1,sticky="w")        
        
        self.size_col_label = ttk.Label(self.sku_frame,text="Size")
        self.size_col_label.grid(row=0,column=2,sticky="w")
        
        self.sku_image_label = ttk.Label(self.sku_frame,text="Default SKU URL")
        self.sku_image_label.grid(row=0,column=3,rowspan=10,sticky="e",padx=15)
        
class ProductViewerEngine():
    def __init__(self):    
        self.log = logging.getLogger(__name__).info
        self.log("Init.")
        self.bug = logging.getLogger(__name__).debug   
#        
#        self.bug("Post-Super Init for {} Engine".format(name))
        
#    def get_cdb_data(self):
#        cdb = self.get_dbvar()["cdb"]
#        return cdb
#    
#    def _get_orders_by_product(self,product_code):
#        temp_odb = self.get_dbvar()["odb"]
#        locced = temp_odb.loc[temp_odb["product_cafe24_code"] == product_code]
#        self.log(".get_orders_by_product locced df length: {}".format(locced.shape[0]))
#        return locced
        
    def get_pdb_product_data(self,pdb, code,codetype):
        self.log("Getting pdb data for {}, search_type: {}, objecttype: {}".format(code,codetype,str(type(code))))
        
        self.log("Orig. pdb length: {}".format(pdb.shape[0]))
        if codetype == "Product Code":
            returndf = pdb.loc[pdb['product_cafe24_code'] == code]  
        elif codetype == "Barcode":
            returndf = pdb.loc[pdb['sku_code'] == int(code)]
        self.log("Locced pdb length: {}".format(returndf.shape[0]))
        return returndf
    
    def get_customers_list(self,temp_odb,code):
        self.log("Called with code: {}".format(code))
        if not code is None and not code == "":
            filtered_odb = temp_odb.loc[temp_odb["product_cafe24_code"] == code]            
            if filtered_odb.shape[0] < 1:
                self.bug("No orders for this product code: {}".format(code))
                return "no_results"
            else:
#                dropped = filtered_odb.drop_duplicates(subset="customer_phone_number")
                return filtered_odb
        else:
            self.bug("No Code Given")
            return "no_code_given"
        
    def search_product(self,pdb, code,codetype):
        self.log("Code Search: {}".format(code))
        if not code is None and not code == "":
            
            filtered_pdb = self.get_pdb_product_data(pdb,code, codetype)
        else:
            return "no_code_given"
            
        if filtered_pdb.shape[0] < 1:
            self.bug("Search yielded a DF less than 1 length.")
            return "no_results"
        else:
            self.log("Search yielded DF of {} length.".format(filtered_pdb.shape[0]))
             
        plist = filtered_pdb.to_dict(orient='records')
        
        final_dict = {
            "product_info": {
                "product_code": "DEFAULT PRODUCT CODE",
#                "vendor_name": "DEFAULT VENDOR NAME",
#                "vendor_code": "DEFAULT VENDOR CODE",
#                "vendor_price": "DEFAULT VENDOR PRICE",
                "main_image_url": "DEFAULT URL",
                "category": "DEFAULT  CATEGORY"
            },
            "sku_list": []
        }
            
        for sku_dict in plist:
            final_dict["product_info"]["product_cafe24_code"] = sku_dict["product_cafe24_code"]
#            final_dict["product_info"]["vendor_name"] = sku_dict["vendor_name"]
#            final_dict["product_info"]["vendor_code"] = sku_dict["vendor_code"]
#            final_dict["product_info"]["vendor_price"] = sku_dict["vendor_price"]
#            final_dict["product_info"]["main_image_url"] = sku_dict["main_image_url"]
            final_dict["product_info"]["category"] = sku_dict["category"]
            
            sku_full_options_text_split = sku_dict["option_text"].split(",")
            sku_color = sku_full_options_text_split[0]
            sku_size = sku_full_options_text_split[1]
            
            final_dict["sku_list"].append(
                (sku_dict["sku_code"],sku_color,sku_size, sku_dict["sku_image_url"])   
            )
        return final_dict
            
    def get_PIL_image(self,url):
        if url == "DEFAULT URL":
            self.bug("Received url of default value. Skipping download attempt.")
            return None
        try:        
            self.log("Trying PIL Image from {}...".format(url))
            raw_data = urllib.request.urlopen(url).read()
            self.log("urllib.request.urlopen(ABOVE URL).read() successfully called.")   
        except ValueError:
            self.bug("THIS IMAGE AT {} IS NOT WORKING!".format(url))
            return None
        except AttributeError:
            self.bug("CANNOT READ URLOPEN FOR ", url)
            return None
        else: 
            PILim = PIL.Image.open(io.BytesIO(raw_data)).resize((300, 300))
            TKim = PIL.ImageTk.PhotoImage(image=PILim)         
            return TKim           
        

if __name__ == "__main__":
    logname = "debug-{}.log".format(datetime.datetime.now().strftime("%y%m%d"))
    ver = "v0.2.10.7 - 2018/07/22"
    
    logging.basicConfig(filename=r"debuglogs\\{}".format(logname),
        level=logging.DEBUG, 
        format="%(asctime)s %(name)s:%(lineno)s - %(funcName)s() %(levelname)s || %(message)s",
        datefmt='%H:%M:%S')
    logging.info("-------------------------------------------------------------")
    logging.info("DEBUGLOG @ {}".format(datetime.datetime.now().strftime("%y%m%d-%H%M")))
    logging.info("VERSION: {}".format(ver))
    logging.info("AUTHOR:{}".format("Justin H Kim"))
    logging.info("-------------------------------------------------------------")

    
    import config2
    dbfile =  open(r"databases/DH_DBS.pickle", "rb")
    dbs = pickle.load(dbfile)  
#    dbs = None
    app = tk.Tk()
    productviewer = ProductViewer(app,app,config2.backend_settings,dbvar=dbs)
    productviewer.grid(padx=20)
    app.mainloop()            
         
        