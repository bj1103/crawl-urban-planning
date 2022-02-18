import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import os
import json
import time
from arcgis2geojson import arcgis2geojson
from tqdm import tqdm

SLEEP_TIME=4

r = requests.get('https://luz.tcd.gov.tw/WEB/')
session_id =  r.headers['Set-Cookie'].split(';')[0].split('=')[-1]
soup = BeautifulSoup(r.text, "html.parser")
js_element = soup.findAll('script')
token = js_element[-2].text.split('M_CONFIG = {"Token":"')[1].split('"')[0]

session = requests.session()
county_url = "https://luz.tcd.gov.tw:443/WEB/ws_form.ashx?CMD=GETFORM&FUNC=%230101"

# get 縣市 code (return type: html)

county_cookies = {"ASP.NET_SessionId": session_id}
county_headers = {"Sec-Ch-Ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"96\"", "Accept": "*/*", "X-Requested-With": "XMLHttpRequest", "Sec-Ch-Ua-Mobile": "?0", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36", "Sec-Ch-Ua-Platform": "\"Linux\"", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://luz.tcd.gov.tw/WEB/default.aspx", "Accept-Encoding": "gzip, deflate", "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"}
html_page = session.get(county_url, headers=county_headers, cookies=county_cookies)
soup = BeautifulSoup(html_page.text, "html.parser")
element = soup.find("select", {"id": "COUNTY_0101"}).findAll('option')

county2id = {}
for e in element:
    county2id[e.getText()] = e['value']

class TK_Window():
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('Crawl for Urban plan')
        self.window.geometry('400x300')

        self.county_id = ''
        self.plan2id = {}
        self.plan_id = ''
        self.plans2id = {}
        self.plans_id = ''
        self.path = os.getcwd()

        #select path
        self.labelOpen = tk.Label(self.window, text='選擇下載路徑')
        self.labelOpen.grid(column=0, row=0)
        self.path_label = tk.Label(self.window, text=self.path, borderwidth=2, relief="ridge", width=20)
        self.path_label.grid(column=0, row=1)
        self.open_button = ttk.Button(
            self.window,
            text='瀏覽',
            command=self.select_file
        )
        self.open_button.grid(column=1, row=1)
        
        #select county
        self.labelCounty = tk.Label(self.window, text='選擇縣市')
        self.labelCounty.grid(column=0, row=2)
        self.countyCombobox = ttk.Combobox(
            self.window, 
            values=list(county2id.keys())
        )
        self.countyCombobox.grid(column=0, row=3)
        self.countyCombobox.bind('<<ComboboxSelected>>', self.select_county)

        #select plan
        self.labelPlan = tk.Label(self.window, text='選擇都市計畫區')
        self.labelPlan.grid(column=0, row=4)
        self.urbanPlanCombobox = ttk.Combobox(
            self.window, 
            values=[],
            postcommand=self.post_for_urbanPlan
        )
        self.urbanPlanCombobox.grid(column=0, row=5)
        self.urbanPlanCombobox.bind('<<ComboboxSelected>>', self.select_urbanPlan)

        #download plan
        self.download_plan_button = ttk.Button(
            self.window,
            text='下載',
            command=self.save_plan
        )
        self.download_plan_button.grid(column=1, row=5)

        #select plans
        self.labelPlans = tk.Label(self.window, text='選擇都市計畫使用分區')
        self.labelPlans.grid(column=0, row=6)
        self.urbanPlansCombobox = ttk.Combobox(
            self.window, 
            values=[],
            postcommand=self.post_for_urbanPlans
        )
        self.urbanPlansCombobox.grid(column=0, row=7)

        #download plans
        self.download_plans_button = ttk.Button(
            self.window,
            text='下載',
            command=self.save_plans
        )
        self.download_plans_button.grid(column=1, row=7)

        # download progress bar
        self.labelProgressBar = tk.Label(self.window, text='下載進度')
        self.labelProgressBar.grid(column=0, row=8)
        self.progressBar = ttk.Progressbar(self.window, orient='horizontal', length=200, mode='determinate')
        self.progressBar.grid(column=0, row=9)
        self.labelProgress = tk.Label(self.window, text='0.00%')
        self.labelProgress.grid(column=1, row=9)



    def main(self):
        self.window.mainloop()
    
    def select_county(self, event):
        self.county_id = county2id[self.countyCombobox.get()]
        plan_url = "https://luz.tcd.gov.tw:443/WEB/ws_data.ashx?CMD=GETDATA&OBJ=URBANPLAN"
        plan_cookies = {"ASP.NET_SessionId": session_id}
        plan_headers = {"Sec-Ch-Ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"96\"", "Accept": "*/*", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest", "Sec-Ch-Ua-Mobile": "?0", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36", "Sec-Ch-Ua-Platform": "\"Linux\"", "Origin": "https://luz.tcd.gov.tw", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://luz.tcd.gov.tw/WEB/default.aspx", "Accept-Encoding": "gzip, deflate", "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"}
        plan_data = {"FUNC": "0101", "COUNTY": self.county_id}
        res = session.post(plan_url, headers=plan_headers, cookies=plan_cookies, data=plan_data).json()
        self.plan2id = {}
        for plan in res:
            self.plan2id[plan['計畫區名稱']] = plan['計畫區代碼']

    def post_for_urbanPlan(self):
        self.urbanPlanCombobox['values'] = ['ALL'] + list(self.plan2id.keys())
    
    def select_urbanPlan(self, event):
        if self.urbanPlanCombobox.get() != 'ALL':
            self.plan_id = self.plan2id[self.urbanPlanCombobox.get()]
            plans_url = "https://luz.tcd.gov.tw:443/WEB/ws_data.ashx?CMD=GETDATA&OBJ=URBANPLANS"
            plans_cookies = {"ASP.NET_SessionId": session_id}
            plans_headers = {"Sec-Ch-Ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"96\"", "Accept": "*/*", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest", "Sec-Ch-Ua-Mobile": "?0", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36", "Sec-Ch-Ua-Platform": "\"Linux\"", "Origin": "https://luz.tcd.gov.tw", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://luz.tcd.gov.tw/WEB/default.aspx", "Accept-Encoding": "gzip, deflate", "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"}
            plan_data = {"FUNC": "0101", "VAL1": self.plan_id}
            res = session.post(plans_url, headers=plans_headers, cookies=plans_cookies, data=plan_data).json()
            self.plans2id = {}
            for plan in res:
                self.plans2id[plan['分區次類別']] = plan['分區代碼']

    def post_for_urbanPlans(self):
        if self.urbanPlanCombobox.get() != 'ALL':
            self.urbanPlansCombobox['values'] = ['ALL'] + list(self.plans2id.keys())
        else:
            self.urbanPlansCombobox['values'] = []

    def select_file(self):
        self.path = fd.askdirectory(
            title='Open a directory',
            initialdir=self.path,
        )
        self.path_label["text"] = self.path

    def save_plan(self):
        self.progressBar['value'] = 0
        self.labelProgress['text'] = "0.00%"
        self.window.update()
        geometry_url = f"https://luz.tcd.gov.tw:443/WEB/ws_data.ashx?CMD=SEARCHURBANRANGE&TOKEN={token}"
        geometry_cookies = {"ASP.NET_SessionId": session_id}
        geometry_headers = {"Sec-Ch-Ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"96\"", "Accept": "*/*", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest", "Sec-Ch-Ua-Mobile": "?0", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36", "Sec-Ch-Ua-Platform": "\"Linux\"", "Origin": "https://luz.tcd.gov.tw", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://luz.tcd.gov.tw/WEB/default.aspx", "Accept-Encoding": "gzip, deflate", "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"}
        if self.urbanPlanCombobox.get() != 'ALL':
            geometry_data = {"VAL1": self.plan_id}
            res = session.post(geometry_url, headers=geometry_headers, cookies=geometry_cookies, data=geometry_data).json()
            del res['spatialReference']
            json.dump(arcgis2geojson(res), open(os.path.join(self.path, f'{self.urbanPlanCombobox.get()}.json'), "w")) 
            self.progressBar['value'] = self.progressBar["maximum"]
            self.labelProgress['text'] = '100.00%'
        else:
            combine_json = {
                "type" : "FeatureCollection",
                "features" : []
            }
            interval = self.progressBar["maximum"] / len(self.plan2id.items())
            for i, (plan_name, plan_id) in tqdm(enumerate(self.plan2id.items())):
                geometry_data = {"VAL1": plan_id}
                res = session.post(geometry_url, headers=geometry_headers, cookies=geometry_cookies, data=geometry_data).json()
                del res['spatialReference']
                res = arcgis2geojson(res)
                combine_json["features"] += res["features"]
                self.progressBar['value'] = i * interval
                self.labelProgress['text'] = f"{self.progressBar['value']:5.2f}%"
                self.window.update()
                time.sleep(SLEEP_TIME)
            self.progressBar['value'] = self.progressBar["maximum"]
            self.labelProgress['text'] = '100.00%'
            self.window.update()
            json.dump(combine_json, open(os.path.join(self.path, f'{self.countyCombobox.get()}_ALL.json'), "w")) 
            
    
    def save_plans(self):
        self.progressBar['value'] = 0
        self.labelProgress['text'] = "0.00%"
        self.window.update()
        geometry_url = f"https://luz.tcd.gov.tw:443/WEB/ws_data.ashx?CMD=SEARCHURBANLANDUSE&TOKEN={token}"
        geometry_cookies = {"ASP.NET_SessionId": session_id}
        geometry_headers = {"Sec-Ch-Ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"96\"", "Accept": "*/*", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest", "Sec-Ch-Ua-Mobile": "?0", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36", "Sec-Ch-Ua-Platform": "\"Linux\"", "Origin": "https://luz.tcd.gov.tw", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://luz.tcd.gov.tw/WEB/default.aspx", "Accept-Encoding": "gzip, deflate", "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"}
        if self.urbanPlansCombobox.get() != 'ALL':
            self.plans_id = self.plans2id[self.urbanPlansCombobox.get()]
            geometry_data = {"VAL1": self.plan_id, "VAL2" : self.plans_id}
            res = session.post(geometry_url, headers=geometry_headers, cookies=geometry_cookies, data=geometry_data).json()
            del res['spatialReference']
            json.dump(arcgis2geojson(res), open(os.path.join(self.path, f'{self.urbanPlansCombobox.get()}.json'), "w")) 
            self.progressBar['value'] = self.progressBar["maximum"]
            self.labelProgress['text'] = '100.00%'
        else:
            interval = self.progressBar["maximum"] / len(self.plans2id.items())
            for i, (plans_name, plans_id) in tqdm(enumerate(self.plans2id.items())):
                geometry_data = {"VAL1": self.plan_id, "VAL2" : plans_id}
                res = session.post(geometry_url, headers=geometry_headers, cookies=geometry_cookies, data=geometry_data).json()
                del res['spatialReference']
                json.dump(arcgis2geojson(res), open(os.path.join(self.path, f'{plans_name}.json'), "w")) 
                self.progressBar['value'] = i * interval
                self.labelProgress['text'] = f"{self.progressBar['value']:5.2f}%"
                self.window.update()
                time.sleep(SLEEP_TIME)
        self.progressBar['value'] = self.progressBar["maximum"]
        self.labelProgress['text'] = '100.00%'
        self.window.update()
tk_window = TK_Window()
tk_window.main()

