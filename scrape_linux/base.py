from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
# import pandas as pd
from bs4 import BeautifulSoup
import re
import os
import sys
import glob
from datetime import datetime
from smtplib import SMTP
from email.mime.text import MIMEText
# import mod_log



# Seleniumをあらゆる環境で起動させるChromeオプション
options = Options()
options.add_argument('--disable-gpu')
options.add_argument('--disable-extensions')
options.add_argument('--proxy-server="direct://"')
options.add_argument('--proxy-bypass-list=*')
options.add_argument('--start-maximized')
options.add_argument('--headless') # ※ヘッドレスモードを使用する場合、コメントアウトを外す

DRIVER_PATH = './chromedriver'
# DRIVER_PATH = '/Users/Kenta/Desktop/Selenium/chromedriver' # ローカル
# DRIVER_PATH = '/app/.chromedriver/bin/chromedriver'        # heroku


try:
    # ブラウザの起動
    driver = webdriver.Chrome(executable_path=DRIVER_PATH, options=options)


    # Webページにアクセスする
    url = 'https://www.to-kousya.or.jp/chintai/rent/index.html'
    driver.get(url)
    driver.implicitly_wait(3)
    driver.find_element_by_id('kensaku1').click()


    # 検索ページへ切り替え
    driver.switch_to.window(driver.window_handles[1])


    # 区のチェック
    driver.implicitly_wait(3)
    # element = driver.find_element_by_xpath("//label[contains(text(), '板橋区')]")
    # element.find_element_by_xpath('..//input').click()
    # element = driver.find_element_by_xpath("//label[contains(text(), '北区')]")
    # element.find_element_by_xpath('..//input').click()
    # element = driver.find_element_by_xpath("//label[contains(text(), '杉並区')]")
    # element.find_element_by_xpath('..//input').click()
    # element = driver.find_element_by_xpath("//label[contains(text(), '中野区')]")
    # element.find_element_by_xpath('..//input').click()
    # element = driver.find_element_by_xpath("//label[contains(text(), '練馬区')]")
    # element.find_element_by_xpath('..//input').click()

    for city in ['板橋区', '北区', '杉並区', '中野区', '練馬区', '豊島区', '江東区']:
        xpath_arg = "//label[contains(text(), '%s')]" % city
        element = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, xpath_arg)))
        # element = driver.find_element_by_xpath(arg)
        element.find_element_by_xpath('..//input').click()



    # 検索
    # element = driver.find_elements_by_xpath("//img[@alt='検索する']")
    # xpath_arg = "//img[@alt='検索する']"
    element = WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.XPATH, "//img[@alt='検索する']")))
    # element[0].find_element_by_xpath('..').click()
    element.find_element_by_xpath('..').click()
    # print(driver.current_url)
    # print(element)


    # 表示数を50に変更
    # show_element = driver.find_element_by_name('akiyaRefRM.showCount')
    show_element = WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.NAME, 'akiyaRefRM.showCount')))
    show_select_element = Select(show_element)
    show_select_element.select_by_value('50')
    driver.implicitly_wait(3)


    # スクレイピング
    # 物件データ
    html = driver.page_source.encode('utf-8')
    soup = BeautifulSoup(html, "lxml")

    # tds = soup.find_all('td', class_=re.compile('^ListTXT'))
    trs = soup.select('tr[class^=ListTXT]')
    # print(trs)

    info_list = []
    for tr in trs:
        # print(tr.select('td')[1].string.strip())
        one_info = []
        for td in tr.select('td'):
            if td.string:
                one_info.append(td.string.strip())
                # print(td.string.strip())

        info_list.append(one_info)

    # print(info_list)


    # 項目データ
    tds = soup.select('td[class=cell99CC99]')

    item_name_list = []
    for td in tds:
        if td.text:
            item_name_list.append(td.text.strip())

    # print(item_name_list)
    item_name_list.pop(0)


    # 前回結果の読み込み
    file_list = glob.glob('./log/*')
    src_estimate_list = []
    if file_list:
        latest_file = max(file_list, key=os.path.getctime)
        # print(latest_file)

        with open(latest_file) as f:
            src_estimate_list = [s.strip().split(', ') for s in f.readlines()]
        # print(src_list)


    # 前回結果と比較
    src_list = [', '.join(l) for l in src_estimate_list]
    dst_list = [', '.join(l) for l in info_list]
    # print(del_list)
    # print(add_list)
    del_list = list(set(src_list) - set(dst_list))
    add_list = list(set(dst_list) - set(src_list))
    # print(add_list)

    if del_list or add_list:
        # output_list = [', '.join(l) for l in add_list]
        output_str = '\n'.join(dst_list)

        os.makedirs('./log', exist_ok=True)
        file_path = './log/result_%s.log' \
                    % str(datetime.now().strftime('%Y-%m-%dT%H%M%S'))

        with open(file_path, 'w') as f:
            f.write(output_str)


    # 結果ファイル出力
    if not add_list:
        # print('物件　新着なし')
        driver.quit()
        sys.exit(0)


    # メール送信
    target_list = []
    for estimate_name in ['コーシャハイム向原ガーデンコート', 'コーシャハイム加賀',
                          'コーシャハイム田端テラス', 'コーシャハイム中野フロント', '南砂']:
        tmp_list = [estimate for estimate in add_list if estimate_name in estimate]
        target_list += tmp_list
    # print(target_list)
    send_target_list = [target.split(', ') for target in target_list]
    # print(send_target_list)

    if not send_target_list:
        # print('希望物件　新着なし')
        driver.quit()
        sys.exit(0)

    body_text = '★新着★\n'
    n =1
    for t in send_target_list:
        body_text += '--------------------------------------------\n'
        body_text += '%d件目\n' % n
        for item, val in zip(item_name_list, t):
            body_text += '%s: %s\n' % (item, val)
        n += 1
    # print(body_text)

    gmail_account = 'socskmbn10yz@gmail.com'
    gmail_password = 'xmjqaxwenlptkmkr'
    mail_to = 'bizbnskmyz14-tojkk@yahoo.co.jp'
    subject = '新着　希望物件'
    body = body_text
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["To"] = mail_to
    msg["From"] = gmail_account

    gmail=SMTP("smtp.gmail.com", 587)
    gmail.starttls()
    gmail.login(gmail_account, gmail_password)
    gmail.send_message(msg)

    driver.quit()

except Exception as e:
    # print('Error: %s', e)
    os.makedirs('./errors', exist_ok=True)
    file_path = './errors/error.log'
    output_str = '%s Error occurred : %s' % \
                 (datetime.now().strftime('%Y-%m-%dT%H%M%S'), e)
    with open(file_path, 'a') as f:
        f.write(output_str)

    driver.quit()
    sys.exit(1)



