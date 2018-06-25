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

# Non-standard Modules
from PIL import ImageTk

#Package Modules
from default_engines import ProductViewerEngine

class ProductViewer(tk.LabelFrame):
    def __init__(self,parent,controller=None,engine="default",config=None,dbvar=None):
        super().__init__(parent)
        self.parent = parent
        if not controller:
            self.controller = parent
        else:
            self.controller = controller
            
        if str(engine) == "default":
            self.engine = ProductViewerEngine()
        else:
            self.engine = engine         
            
        if config:
            self.engine.set_build_config(raw_config = config)  
            
        if dbvar:
            self.engine.set_dbvar(dbvar)
            
        self.product_detail_packs = []
        self.sku_detail_packs = []
#        Required to keep images in memory for tkinter to render
        self.current_images = [None,None]          
        
        self._build_search_frame()
        self._build_product_info_frame()
        self._build_sku_frame()
        
    def _build_search_frame(self):
        self.search_frame = ttk.LabelFrame(self,text="Search")
        self.search_frame.grid(row=0,column=0,sticky="ew",pady=15)
        
        self.search_pcode_stvar = tk.StringVar()        
        self.search_pcode_label = ttk.Label(self.search_frame,text="Search Product Code")
        self.search_pcode_label.grid(row=0,column=0)
        
        self.search_entry = ttk.Entry(
            self.search_frame, 
            width=15, 
            textvariable=self.search_pcode_stvar
        )
        self.search_entry.grid(row=0, column=1, padx=5,sticky="w")    
        
        self.search_button = ttk.Button(
            self.search_frame,
            text = "Search",
            command = self.search_product
        )
        self.search_button.grid(row=0,column=2,padx=5,sticky="w")
        
    def _build_product_info_frame(self):
        self.product_info_frame = ttk.LabelFrame(self,text="Product Information")
        self.product_info_frame.grid(row=1,column=0,sticky="ew")
        
        self.product_info_frame.columnconfigure(0,weight=0)
        self.product_info_frame.columnconfigure(1,weight=0)        
        self.product_info_frame.columnconfigure(2,weight=1)   

        required_details = ["product_code","vendor_name","vendor_code","vendor_price","category"]
        start_row = 0   
        for key in required_details:
            detail_var = tk.StringVar()
            detail_label = ttk.Label(self.product_info_frame,text = key)
            detail_label.grid(row=start_row,column=0,sticky="w")
            detail_value = ttk.Label(self.product_info_frame,textvariable = detail_var)
            detail_value.grid(row=start_row,column=1,sticky="w")
            start_row += 1
            self.product_detail_packs.append([key,detail_var,detail_value])

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
        
    def search_product(self,code=None):
        if code == None:
            code = self.search_pcode_stvar.get()        
        search_product_result = self.engine.search_product(code=code)
        if search_product_result == "no_results":
            self.popup = tk.Toplevel()
            self.popup.title("Load from Online or from Computer?")
            msg = tk.Message(
                self.popup,
                text="No results for this product code in database.")
            msg.pack()
            okbutton = ttk.Button(
                self.popup,
                text="OK",
                command=self.popup.destroy)
            okbutton.pack()
        elif search_product_result == "no_code_given":
            print("No Code Given")
        else:
            self.update_product_info(search_product_result)     
            
    def update_product_info(self,product_dict):
        self.clear_data()
        
#       UPDATE PRODUCT FRAME DETAILS      
        for stvar_tpl in self.product_detail_packs:
            key = stvar_tpl[0]
            detail_var = stvar_tpl[1]
            detail_var.set(product_dict["product_info"][key])

#       UPDATE MAIN IMAGE 
        p_url = product_dict["product_info"]["main_image_url"]
        self.update_label_image(self.main_image_url_label,p_url,0)            

#       UPDATE SKU FRAME
        row_c = 1
        for sku_tpl in product_dict["sku_list"]:
            
            barcode,color,size,url = sku_tpl
            
            barc_lbl = ttk.Label(self.sku_frame,text=barcode)
            barc_lbl.grid(row=row_c,column=0,sticky="w",padx=8) 
            
            colorbt = ttk.Button(self.sku_frame, text=color,
                command=lambda url = url: self.update_label_image(
                    self.sku_image_label,
                    url,1))
            colorbt.grid(row=row_c,column=1,sticky="w",padx=8)
            
            size_lbl = ttk.Label(self.sku_frame,text=size)     
            size_lbl.grid(row=row_c,column=2,sticky="w",padx=8)
            
            if row_c == 1:
                colorbt.invoke()
            row_c += 1
            
            sku_detail_pack = barc_lbl,colorbt,size_lbl
            self.sku_detail_packs.append(sku_detail_pack)
   
    def clear_data(self):
        self.main_image_url_label["image"] = ""
        self.sku_image_label["image"] = ""
        for tpl in self.product_detail_packs:
            tpl[1].set("")
            
        for tpl in self.sku_detail_packs:
            for x in tpl:
                x.grid_forget()
        self.sku_detail_packs = []       

    def update_label_image(self, labelobj,url,curr_img_index):
        im = self.engine.get_PIL_image(url)
        if im:
            im = im.resize((300, 300))
            image = ImageTk.PhotoImage(im)
            labelobj["image"] = image   
            self.current_images.append(image) 
        else:
            labelobj["image"] = ""
            image = None
        self.current_images[curr_img_index] = image
         
if __name__ == "__main__":
    dbfile =  open(r"databases/DH_DBS.pickle", "rb")
    dbs = pickle.load(dbfile)  
    app = tk.Tk()
    analysispage = ProductViewer(app,config=None,dbvar=dbs)
    analysispage.grid(padx=20)
    app.mainloop()            
         
        