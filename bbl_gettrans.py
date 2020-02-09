from flask import request
from flask import Flask
from flask import jsonify

import requests
from selenium import webdriver
from bs4 import BeautifulSoup
from lxml import html, etree
import pandas as pd


bbl_driver = None

app = Flask(__name__)


def login_bbl_by_selenium(username, password):
    global bbl_driver

    # login bank
    driver = webdriver.Firefox()
    driver.get("https://ibanking.bangkokbank.com/SignOn.aspx")
    driver.implicitly_wait(5)
    driver.find_element_by_css_selector("#txtID").send_keys(username)
    driver.find_element_by_css_selector("#txtPwd").send_keys(password)
    driver.find_element_by_css_selector("#btnLogOn").click()
    driver.implicitly_wait(5)
    
    try:
        # 切換英文語系
        driver.find_element_by_css_selector("#ctl00_ctl00_C_CN_NavAcctSummary1_ucSwtLang_lnkEN").click()
    except:
        pass

    driver.find_element_by_css_selector("#ctl00_ctl00_C_CW_gvDepositAccts_ctl02_lnkDepositAccts").click()
    driver.implicitly_wait(5)
    soup = BeautifulSoup(driver.page_source, 'lxml')

    status = soup.find(id="ctl00_ctl00_C_CW_lblMainAccount").text
    bbl_driver = driver

    return True

def gettrans_bbl_by_selenium():
    global bbl_driver

    bbl_driver.find_element_by_css_selector("#ctl00_ctl00_C_CW_btnOK").click()    
    soup = BeautifulSoup(bbl_driver.page_source, 'lxml')

    html_string = str(soup.find(id="ctl00_ctl00_C_CW_UpdatePanel10"))
    dfs = pd.read_html(html_string) # read html table format
    df_ls = dfs[0].fillna("Na").values.tolist()

    trans = []
    for i in df_ls:
        Date = i[1]
        Description = i[2]
        Debit = i[3]
        Credit = i[4]
        Balance = i[5]
        Channel = i[6]
        
        if Date != "Na" and Date != "Date":
            trans_dict = {"date": Date, 
                        "desc": Description,
                        "bal": Balance,
                        "Channel": Channel}
            
            if Debit != "Na":
                trans_dict["debit"] = Debit
                
            elif Credit != "Na":
                trans_dict["credit"] = Credit
            
            trans += [trans_dict]
    
    return trans

@app.route('/banking/api/v1.1/login_bank/<username>/<password>', methods=['GET'])
def login_bank(username, password):
    status = login_bbl_by_selenium(username, password)
    return jsonify({'func': 'bank_transfer()', 'success': status})

@app.route('/banking/api/v1.1/get_transactions', methods=['GET'])
def get_transactions():
    trans = gettrans_bbl_by_selenium()
    print(trans)
    return jsonify({'func': 'bank_transfer()', 'success': True, 'result': trans})

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=False)