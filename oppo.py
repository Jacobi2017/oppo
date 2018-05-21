#! /usr/bin env python
# coding:utf-8
import requests
import re
from lxml import etree
import  pymysql
import csv
import time
import pytesseract
from PIL import Image
import json
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import datetime
import logging
import configue
class Oppo_spider:
    #.......##################
    def __init__(self):

        self.s = requests.session()
        self.starttime = datetime.datetime.now()
        print("爬虫进行抓取的时间为")

        print self.starttime
        self.connection =  pymysql.connect(host=configue.DB.get('host'),port=configue.DB.get('port'),user=configue.DB.get('user'), passwd=configue.DB.get('passwd'), db=configue.DB.get('db'), charset=configue.DB.get('charset'))
        self.cursor = self.connection.cursor();

    def captcha(self,data):
        with open('captcha.jpg', 'wb') as fp:
            fp.write(data)
        time.sleep(1)
        image = Image.open("captcha.jpg")
        text = pytesseract.image_to_string(image)
        print "机器学习识别后的验证码为：" + text
        return text
    def login_in(self):
        login_token_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36'
        }

        login_token_url = "https://e.oppomobile.com/login_token"
        self.s.get(login_token_url, headers=login_token_headers)
        login_token_headers['Referer'] = login_token_url
        log_url = 'https://e.oppomobile.com/login'
        loginCaptcha_url = 'https://e.oppomobile.com/loginCaptcha'
        response=self.s.get(loginCaptcha_url)

        Form_data = {'name': '1000002573', 'passwd': 'pairuioppo8', 'captcha': self.captcha(response.content)}
        manage_page_response = self.s.post(log_url, data=Form_data, headers=login_token_headers).text
        if (manage_page_response.encode("utf-8").find("广告主ID") == -1):
            print("sign in is failing , now restart sign in ,please hold on a few minutes")
            self.login_in()
        else:
            pattern = re.compile(r'<div class="account_area"><a href="/agency/passwd">.*?(\d+).*?(\d+).*?')
            ad_owner_id = pattern.search(manage_page_response).group(1).encode("utf-8")
            user_id = pattern.search(manage_page_response).group(2).encode("utf-8")
            if (ad_owner_id == "1000002573" and user_id == "800002573"):
                print("sign in is sucessful 你的广告主ID为:%s 用户ID为:%s") % (ad_owner_id, user_id)
                self.Promotion_manage(manage_page_response.encode("utf-8"),login_token_headers)

    #


    def Promotion_manage(self, manage_page,login_token_headers):
        index_url = "https://e.oppomobile.com/agency/index"
        self.s.get(url=index_url,headers=login_token_headers)
        ifrma_list=[]
        manage_page_data = etree.HTML(manage_page).xpath('//tr[contains(@class,"tolist")]//td/text()')
        manage_page_ifrma = etree.HTML(manage_page).xpath(
            '//tr[contains(@class,"tolist")]//td/a[contains(@href,"javascript:;")]/@onclick')

        '''
        csvfile = open('data.csv', 'wb')  # 打开方式还可以使用file对象
        writer = csv.writer(csvfile)
        writer.writerow(['客户名称', '客户ID'])
        '''

        print("推广管理数据输出中:\r\n")
        for i in range(len(manage_page_data)):

            if (i % 10 == 2):
                manage_page_data[i] = manage_page_data[i].strip()
            if (i % 10 == 3):
                manage_page_data[i] = manage_page_data[i].strip()
            # print (manage_page_data[i])
            if (i % 10 == 9):
                pass

        for i in range(len(manage_page_ifrma)):
            ifrma_list.append("https://e.oppomobile.com" + manage_page_ifrma[i].split("('", 1)[1].split("')", 1)[0])

        for i ,v in enumerate(ifrma_list):
            manage_page_data.insert(i*11+10,v)
        for i in range(len(manage_page_data)):

            if(i%11)==10:

                account_list = "select id from account where media_id=4 and account_id_from_media='%s';" % (
                manage_page_data[i - 10 + 1])
                self.cursor.execute(account_list)
                account_result= self.cursor.fetchone()

                usable_status = 2 if manage_page_data[i - 10 + 1 + 1] == "审核通过" else 3
                if (account_result == None):
                    sql_account = "insert into account (account_fullname,user, account_id_from_media,funds,agency_id, media_id,usable_status,usable_log)values('%s','%s','%s','%s',8,4,%d,'%s');" % (
                        manage_page_data[i - 10], manage_page_data[i - 10], manage_page_data[i - 10 + 1],
                        manage_page_data[i - 10 + 4], usable_status, 1)

                    self.cursor.execute(sql_account)
                    try:
                        self.connection.commit()
                    except Exception as e:
                        self.connection.rollback()

                else:
                    sql_account = "update account set account_fullname='%s',user='%s', account_id_from_media='%s',funds='%s',agency_id=8, media_id=4,usable_status=%d where media_id=4 and account_id_from_media='%s';" % (
                        manage_page_data[i - 10], manage_page_data[i - 10], manage_page_data[i - 10 + 1],
                        manage_page_data[i - 10 + 4], usable_status, manage_page_data[i - 10 + 1])

                    self.cursor.execute(sql_account)
                    try:
                        self.connection.commit()
                    except Exception as e:
                        self.connection.rollback()
                if manage_page_data[i-10+2]=="审核通过":
                    print(' 抓取客户名称信息是%s')%(manage_page_data[i-10])
                    login_token_headers['Referer'] = index_url
                    apply_page=self.s.get(manage_page_data[i], headers=login_token_headers).text
                    # self.s.get('https://e.oppomobile.com/agency/ownerLogin/1000002684',headers=apply_headers)
                    list_url = "https://e.oppomobile.com/bid/list"
                    self.s.get(url=list_url,headers=login_token_headers)

                    #2获取账户下的应用分发列表信息
                    if "暂无查询结果" in apply_page:
                        print('应用分发没数据')
                        pass
                    else:

                        print "应用分发"+manage_page_data[i]
                        account_id =(int)(manage_page_data[i-10+2-1])
                        print account_id
                        campaign_id =etree.HTML(apply_page).xpath('//span[contains(@class,"oper_on")]/@id')[0]
                        campaign_id=(int)(re.search('(\d+)',campaign_id).group(1))

                        campaign_name =etree.HTML(apply_page).xpath('//a[@class="campaignLink"]/text()')[0]

                        day_download=etree.HTML(apply_page).xpath('//td[contains(@class,"col_validclickcount")]/text()')[1].strip()

                        day_cost=etree.HTML(apply_page).xpath('//td[contains(@class,"col_xiaoh")]/text()')[1].strip()

                        day_budget=etree.HTML(apply_page).xpath('//span[@class="daybudget"]/text()')[0]

                        json_campaign={"download":day_download,"cost":day_cost,"budget":day_budget}
                        data_json = json.dumps(json_campaign)

                        id2="insert into oppo_cpd_stat_total_list (account_id,campaign_id,campaign_name, json_campaign)values(%d,%d,'%s','%s');"%(account_id,campaign_id,campaign_name,data_json)
                        self.cursor.execute(id2)
                        try:
                            self.connection.commit()
                        except Exception as e:
                               self.connection.rollback()

                    login_token_headers['Referer'] =list_url
                    feeds_list_url="https://e.oppomobile.com/feeds/list"
                    self.s.get(feeds_list_url, headers=login_token_headers)
                    login_token_headers['Referer']=feeds_list_url
                    feedsplan_url="https://e.oppomobile.com/feedsPlan/list"
                    feeds_plan_page_data = self.s.get(feedsplan_url,headers=login_token_headers).text
                    if "暂无查询结果" in feeds_plan_page_data:
                        print('feedsplan 没数据')
                        pass
                    else:
                        print manage_page_data[i]
                        feeds_plan_hide_total_page=re.search('id="hid_totalPage"\s*value="\s*(\d+)"',feeds_plan_page_data).group(1)
                        print "total page ="+feeds_plan_hide_total_page
                        for j in range(1, (int)(feeds_plan_hide_total_page) + 1):
                            if (j == 1):
                                print manage_page_data[i]
                                feeds_plan_campaign_id = re.findall('''.*?"plan_edit\('(\d+)'\);"''',feeds_plan_page_data,re.S)
                                feeds_plan_budget = etree.HTML(feeds_plan_page_data).xpath('//tbody//tr/td[4]/text()')
                                feeds_plan_campaign_name = etree.HTML(feeds_plan_page_data).xpath('//tbody//tr/td[1]/text()')
                                for k in range(len(feeds_plan_campaign_name)):
                                    if '\r\n' in feeds_plan_campaign_name[k]:
                                        pass
                                    else:
                                      feeds_plan_campaign_id[k] = re.search('(\d+)', feeds_plan_campaign_id[k]).group(1)
                                      json_campaign = {"cost": "0", "budget": (str)(feeds_plan_budget[k].strip())}
                                      json_campaign=json.dumps(json_campaign)
                                      sql_feeds_stat="insert into oppo_feeds_stat_total_list ( account_id,campaign_id,campaign_name,json_campaign)values(%d,%d,'%s','%s');"%((int)(manage_page_data[i-10+2-1]),(int)(feeds_plan_campaign_id[k]),feeds_plan_campaign_name[k],json_campaign)
                                      self.cursor.execute(sql_feeds_stat)
                                      try:
                                          self.connection.commit()
                                      except Exception as e:
                                          self.connection.rollback()

                            else:
                                    print('进入多页循环 这是第%d页数据')%(j)
                                    feedsPlan_headers = {
                                                         "Referer": list_url,
                                                         "tk": self.s.cookies.get('tk'),
                                                         "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36" , "X-Requested-With": "XMLHttpRequest"}
                                    feeds_plan_recy__page_data=self.s.post("https://e.oppomobile.com/feedsPlan/list",data={"tk": self.s.cookies.get('tk'), "name":"","page": j,"rows": "5","totalPage":feeds_plan_hide_total_page,"sortString":""},headers=feedsPlan_headers).text
                                    feeds_plan_campaign_id = re.findall('''.*?"plan_edit\('(\d+)'\);"''',feeds_plan_recy__page_data, re.S)
                                    feeds_plan_budget = etree.HTML(feeds_plan_recy__page_data).xpath('//tbody//tr/td[4]/text()')

                                    feeds_plan_campaign_name=etree.HTML(feeds_plan_recy__page_data).xpath("//tbody//tr/td[1]/text()")
                                    for k in range(len(feeds_plan_campaign_name)):

                                        if '\r\n' in feeds_plan_campaign_name[k]:
                                            pass
                                        else:
                                            feeds_plan_campaign_id[k] = re.search('(\d+)',feeds_plan_campaign_id[k]).group(1)
                                            json_campaign = {"cost": "0", "budget": (str)(feeds_plan_budget[k].strip())}
                                            json_campaign = json.dumps(json_campaign)
                                            sql_feeds = "insert into oppo_feeds_stat_total_list ( account_id,campaign_id,campaign_name,json_campaign)values(%d,%d,'%s','%s');"%(
                                                (int)(manage_page_data[i - 10 + 2 - 1]),
                                                (int)(feeds_plan_campaign_id[k]), feeds_plan_campaign_name[k],
                                                json_campaign)
                                            self.cursor.execute(sql_feeds)
                                            try:
                                                self.connection.commit()
                                            except Exception as e:
                                                   self.connection.rollback()


                    # # #<<<<<<<<<<<<<<<<<< 4.获取账户下的搜索推广计划列表信息>>>>>>>>>>>

                    searchBid_url="https://e.oppomobile.com/searchBid/list"
                    login_token_headers['Referer'] = feedsplan_url
                    search_page_data=self.s.get(searchBid_url,headers=login_token_headers).text

                    if "暂无查询结果" in search_page_data:
                        print('进入搜索结果 没数据')
                    else:
                        print('进入搜索结果 启动数据')
                        print manage_page_data[i]
                        account_id=(int)(manage_page_data[i-10+2-1])

                        campaign_search_id =(etree.HTML(search_page_data).xpath('//span[contains(@class,"oper_on")]/@id')[0])
                        campaign_search_id = (int)(re.search('(\d+)', campaign_search_id).group(1))

                        campaign_search_name =etree.HTML(search_page_data).xpath('//a[@class="campaignLink"]/text()')[0]

                        budget_search =etree.HTML(search_page_data).xpath('//span[@class="daybudget"]/text()')[0]

                        cost_search =etree.HTML(search_page_data).xpath('//td[@class="col_xiaoh"]/text()')[1].strip()

                        download=(int)(etree.HTML(search_page_data).xpath('//td[@class="col_validclickcount"]/text()')[1].replace(",",""))

                        json_campagin={"download":download,"cost":cost_search,"budget":budget_search}
                        json_campagin=json.dumps(json_campagin)

                        sql_search="insert into  oppo_search_stat_total_list (account_id,campaign_id,campaign_name,json_campaign)values(%d,%d,'%s','%s');"%(account_id,campaign_search_id,campaign_search_name,json_campagin)
                        self.cursor.execute(sql_search)
                        try:
                            self.connection.commit()
                        except Exception as e:
                               self.connection.rollback()

                    login_token_headers['Referer'] = searchBid_url
                    self.report_list(manage_page_data[i], manage_page_data[i - 10 + 2 - 1],login_token_headers)


        self.cursor.close()
        self.connection.close()
        print('程序结束')
        print('花费的总时间为')
        endtime = datetime.datetime.now()
        print (endtime - self.starttime).seconds

    #报表
    def report_list(self,url,client_id,login_token_headers):
        print url
        print("进入报表")
        if (len(sys.argv)<2):
            interval_day = datetime.date.today() - datetime.timedelta(days=1)
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            self.report_list1(interval_day, yesterday, url, client_id, login_token_headers)
        elif datetime.date.today() - datetime.timedelta(days=365) <= (
        datetime.date(*map(int, sys.argv[1].split('-')))) <= datetime.date.today() - datetime.timedelta(days=1):
            interval_day = datetime.date(*map(int, sys.argv[1].split('-')))
            yesterday = datetime.date(*map(int, sys.argv[1].split('-')))
            self.report_list1(interval_day, yesterday, url, client_id, login_token_headers)


    def report_list1(self,interval_day,yesterday,url,client_id,login_token_headers):
        account_id = (int)(client_id)
        cpdStat_url = "https://e.oppomobile.com/cpdStat/index"
        self.s.get(cpdStat_url, headers=login_token_headers)
        # 5.获取账户类型为应用分发类型的报表
        trend_url = "https://e.oppomobile.com/cpdStat/trend"
        Form_data = {"dateRange": "{}~{}".format(interval_day, yesterday), "appId": "", "moduleId": "", "type": "1"}
        tread_headers = {"Referer": cpdStat_url, "tk": self.s.cookies.get('tk'),
                         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"}
        tread_list_data = self.s.post(trend_url,
                                      data={"dateRange": "{}~{}".format(interval_day, yesterday), "appId": "",
                                            "moduleId": "", "type": "1"}, headers=tread_headers).text

        if len(json.loads(tread_list_data)['data']) == 0:
            pass
        else:
            print "应用分发数据" + tread_list_data
            tread_json_data = json.loads(tread_list_data)


            report_date = (str)(tread_json_data['data'][len(tread_json_data['data']) - 1]['dt'])

            json_data = tread_json_data['data'][len(tread_json_data['data']) - 1]
            json_data = json.dumps(json_data)

            id3 = "select id from oppo_cpd_stat_total_report where account_id =%d and report_date='%s';" % (
            account_id, report_date)
            self.cursor.execute(id3)
            report_result = self.cursor.fetchone()

            if (report_result == None):
                sql_cpd = "insert into  oppo_cpd_stat_total_report (account_id,report_date,json_data)values(%d,'%s','%s');" % (
                account_id, report_date, json_data)
                self.cursor.execute(sql_cpd)
                try:
                    self.connection.commit()
                except Exception as e:
                    self.connection.rollback()
            else:
                sql_cpd = "update oppo_cpd_stat_total_report set account_id=%d,report_date='%s',json_data='%s' where account_id=%d and report_date='%s' ;" % (
                account_id, report_date, json_data,account_id,report_date)
                self.cursor.execute(sql_cpd)
                try:
                    self.connection.commit()
                except Exception as e:
                    self.connection.rollback()
            # dateRange:2018-02-06~2018-02-12

        # 6.获取账户类型为信息流类型的报表

        cpd_list_url = 'https://e.oppomobile.com/cpdStat/list'
        cpd_list_headers = {
            'Referer': cpdStat_url,
            'tk': self.s.cookies.get('tk'),
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36',
        }
        Form_data = {
            'dateRange': "{}~{}".format(interval_day, yesterday),
            'appId': '',
            'moduleId': '',
            'page': '1',
            'type': '1',
        }
        cpd_list_text = self.s.post(url=cpd_list_url, headers=cpd_list_headers, data=Form_data)
        feedreport_url = "https://e.oppomobile.com/feedsStat/report"
        feedreport_headers = {
            'Referer': 'https://e.oppomobile.com/cpdStat/index',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36',
        }
        feed_text = self.s.get(url=feedreport_url, headers=feedreport_headers).text
        start_date = interval_day.strftime('%Y%m%d')
        end_date = yesterday.strftime('%Y%m%d')

        feed_total_url = "https://e.oppomobile.com/feedsStat/total"
        feed_total_headers = {
            'Referer': 'https://e.oppomobile.com/feedsStat/report',
            'tk': self.s.cookies.get('tk'),
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36',
        }
        Form_data = {
            'startDate': start_date,
            'endDate': end_date,
        }
        feed_total_data = self.s.post(url=feed_total_url, headers=feed_total_headers, data=Form_data).text

        if len(json.loads(feed_total_data)['data']) == 0:
            print('信息流类报表数据为空')

        else:
            print('进入信息流类报表')
            feeds_list_data = json.loads(feed_total_data)


            report_date = feeds_list_data['data'][len(feeds_list_data['data']) - 1]['time']

            json_data = feeds_list_data['data'][len(feeds_list_data['data']) - 1]
            json_data = json.dumps(json_data)

            sql_report_id = "select id from oppo_feeds_stat_total_report where account_id =%d and report_date='%s';" % (
            account_id, report_date)
            self.cursor.execute(sql_report_id)
            feeds_stat_result = self.cursor.fetchone()

            if (feeds_stat_result == None):
                sql_report = "insert into  oppo_feeds_stat_total_report (account_id,report_date,json_data)values(%d,'%s','%s');" % (
                account_id, report_date, json_data)
                self.cursor.execute(sql_report)
                try:
                    self.connection.commit()
                except Exception as e:
                    self.connection.rollback()

            else:
                sql_report = "update oppo_feeds_stat_total_report set account_id=%d,report_date='%s',json_data='%s'where account_id=%d and report_date='%s';" % (
                account_id, report_date, json_data,account_id,report_date)
                self.cursor.execute(sql_report)
                try:
                    self.connection.commit()
                except Exception as e:
                    self.connection.rollback()

        # #<<<<<<<<<<<<<<<<<<<<<<<<8.获取创意的报表>>>>>>>>>>>>>>>>>>>>>>>>>>>

        feedsStat_totalpage_url = 'https://e.oppomobile.com/feedsStat/totalPage'
        feed_totalpage_headers = {
            'Referer': 'https://e.oppomobile.com/feedsStat/report',
            'tk': self.s.cookies.get('tk'),
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36',
        }
        data = {
            'startDate': start_date,
            'endDate': end_date,
            'page': '1',
        }
        a = self.s.post(url=feedsStat_totalpage_url, headers=feed_totalpage_headers, data=data)
        ad_url = "https://e.oppomobile.com/feedsStat/ad"
        ad_headers = {
            'Referer': 'https://e.oppomobile.com/feedsStat/report',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36',
        }
        feedsStat_ad_data = self.s.get(url=ad_url, headers=ad_headers).text


        if "推广名称" not in feedsStat_ad_data:

            print('广告报表没有数据')
            pass
        else:
            print('enter广告报表')
            print  start_date
            print  end_date
            ad_total_page = re.search('" id="hid_totalPage" value="\s*(\d+)"\s*/>', feedsStat_ad_data).group(1)
            print "ad_total page is"+ad_total_page
            print url
            print "ad_totaol_page" + ad_total_page
            for j in range(1, (int)(ad_total_page) + 1):
               if(j==1):
                    ymd = end_date
                    print "time is"
                    print ymd
                    print('这是广告报表第%d页数据') % (j)
                    print url

                    ad_id = etree.HTML(feedsStat_ad_data).xpath('//tbody//tr/td[8]/p[1]/a/@href')
                    ad_name = etree.HTML(feedsStat_ad_data).xpath(
                        '//div[@style="float: left;width: 150px;text-align: left;padding: 0 10px;"]/p[2]/text()')
                    ad_img_url = etree.HTML(feedsStat_ad_data).xpath(
                        '//div[@class="img_box"]/img[contains(@class,"img_preview")]/@src')
                    ad_cost = etree.HTML(feedsStat_ad_data).xpath('//tbody//tr/td[5]/text()')

                    ad_click = etree.HTML(feedsStat_ad_data).xpath('//tbody//tr/td[3]/text()')

                    ad_view = etree.HTML(feedsStat_ad_data).xpath('//tbody//tr/td[2]/text()')

                    for k in range(len(ad_name)):
                        ad_name[k] = ad_name[k].replace('推广名称:', '')

                        ad_cost[k] = ad_cost[k].strip()

                        ad_click[k] = ad_click[k].strip()

                        ad_view[k] = ad_view[k].strip()

                        ad_id[k] = ad_id[k].replace('/feedsStat/adDetail/', '')

                        # <<<<<<<oppo_feeds_stat_ad_vcc_report>>>>>>>>>>
                        sql_vcc_id = "select id from oppo_feeds_stat_ad_vcc_report where ad_id =%d and ymd='%s';" % (
                        (int)(ad_id[k]),ymd)
                        print sql_vcc_id
                        self.cursor.execute(sql_vcc_id)
                        vcc_result = self.cursor.fetchall()
                        print vcc_result
                        if (vcc_result == None):

                            sql_vcc = "insert into  oppo_feeds_stat_ad_vcc_report (ad_id,ymd,cost,click,view) values (%d,'%s','%s','%s','%s');" % (
                            (int)(ad_id[k]), ymd, ad_cost[k], ad_click[k], ad_view[k])
                            print sql_vcc
                            self.cursor.execute(sql_vcc)
                            try:
                                self.connection.commit()
                            except Exception as e:
                                self.connection.rollback()


                        else:
                            sql_vcc = "update oppo_feeds_stat_ad_vcc_report set ad_id=%d,ymd='%s',cost='%s',click='%s',view='%s' where ad_id=%d and ymd='%s';" % (
                            (int)(ad_id[k]), ymd, ad_cost[k], ad_click[k], ad_view[k],(int)(ad_id[k]),ymd)

                            print sql_vcc

                            self.cursor.execute(sql_vcc)
                            try:
                                self.connection.commit()
                            except Exception as e:
                                self.connection.rollback()
                        # <<<<<<<oppo_feeds_stat_ad_img_report>>>>>>>>>>

                        sql_ad_img_id = "select id from oppo_feeds_stat_ad_img_report where account_id =%d and ad_id=%d;" % (
                        (int)(account_id), (int)(ad_id[k]))
                        print sql_ad_img_id

                        self.cursor.execute(sql_ad_img_id)
                        ad_img_result = self.cursor.fetchone()

                        if (ad_img_result == None):

                            sql1 = "insert into oppo_feeds_stat_ad_img_report (account_id,ad_id,ad_name,img_url)values(%d,%d,'%s','%s');" % (
                                (int)(account_id), (int)(ad_id[k]), ad_name[k], ad_img_url[k])
                            print sql1

                            self.cursor.execute(sql1)
                            try:
                                self.connection.commit()
                            except Exception as e:
                                self.connection.rollback()


                        else:
                                sql_ad_img = "update oppo_feeds_stat_ad_img_report set account_id=%d,ad_id=%d,ad_name='%s',img_url='%s' where account_id=%d and ad_id=%d;" % (
                                    (int)(account_id), (int)(ad_id[k]), ad_name[k], ad_img_url[k],account_id,(int)(ad_id[k]))
                                self.cursor.execute(sql_ad_img)
                                try:
                                    self.connection.commit()
                                except Exception as e:
                                    self.connection.rollback()



               else:
                    ymd = end_date
                    print('这是广告报表第%d页数据') % (j)
                    feedStat_ad_headers = {
                        'Referer': 'https://e.oppomobile.com/feedsStat/report',
                        'tk': self.s.cookies.get('tk'),
                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36',
                    }
                    Form_date = {"tk": self.s.cookies.get('tk'), "adId": "", "adName": "", "startDate": start_date,
                                 "endDate": end_date, "page": j, "totalPage": ad_total_page, "sortString": "",
                                 "rows": "10"}
                    feedsStat_ad_data = self.s.post(ad_url, headers=ad_headers, data=feedStat_ad_headers).text
                    ad_id = etree.HTML(feedsStat_ad_data).xpath('//tbody//tr/td[8]/p[1]/a/@href')
                    ad_name = etree.HTML(feedsStat_ad_data).xpath(
                        '//div[@style="float: left;width: 150px;text-align: left;padding: 0 10px;"]/p[2]/text()')
                    ad_img_url = etree.HTML(feedsStat_ad_data).xpath(
                        '//div[@class="img_box"]/img[contains(@class,"img_preview")]/@src')
                    ad_cost = etree.HTML(feedsStat_ad_data).xpath('//tbody//tr/td[5]/text()')

                    ad_click = etree.HTML(feedsStat_ad_data).xpath('//tbody//tr/td[3]/text()')

                    ad_view = etree.HTML(feedsStat_ad_data).xpath('//tbody//tr/td[2]/text()')

                    for k in range(len(ad_name)):
                        ad_name[k] = ad_name[k].replace('推广名称:', '')

                        ad_cost[k] = ad_cost[k].strip()

                        ad_click[k] = ad_click[k].strip()

                        ad_view[k] = ad_view[k].strip()

                        ad_id[k] = ad_id[k].replace('/feedsStat/adDetail/', '')

                        # <<<<<<<oppo_feeds_stat_ad_vcc_report>>>>>>>>>>
                        ad_vcc_id = "select id from oppo_feeds_stat_ad_vcc_report where ad_id =%d and ymd='%s';" % (
                            (int)(ad_id[k]), ymd)
                        print ad_vcc_id

                        self.cursor.execute(ad_vcc_id)
                        ad_vcc_result = self.cursor.fetchone()
                        print ad_vcc_result

                        if (ad_vcc_result == None):
                            sql1 = "insert into  oppo_feeds_stat_ad_vcc_report (ad_id,ymd,cost,click,view)values(%d,'%s','%s','%s','%s');" % (
                                (int)(ad_id[k]), ymd, ad_cost[k], ad_click[k], ad_view[k])
                            self.cursor.execute(sql1)
                            try:
                                self.connection.commit()
                            except Exception as e:
                                self.connection.rollback()


                        else:
                            sql_ad= "update oppo_feeds_stat_ad_vcc_report set ad_id=%d,ymd='%s',cost='%s',click='%s',view='%s' where ad_id=%d and ymd='%s';" % (
                                (int)(ad_id[k]), ymd, ad_cost[k], ad_click[k], ad_view[k],(int)(ad_id[k]),ymd)

                            print sql_ad
                            self.cursor.execute(sql_ad)
                            try:
                                self.connection.commit()
                            except Exception as e:
                                self.connection.rollback()
                        # <<<<<<<oppo_feeds_stat_ad_img_report>>>>>>>>>>

                        ad_img_id = "select id from oppo_feeds_stat_ad_img_report where account_id =%d and ad_id=%d;" % (
                        (int)(account_id), (int)(ad_id[k]))
                        self.cursor.execute(ad_img_id)
                        ad_img_result = self.cursor.fetchone()
                        if (ad_img_result == None):
                            sql1 = "insert into oppo_feeds_stat_ad_img_report (account_id,ad_id,ad_name,img_url)values(%d,%d,'%s','%s');" % (
                                (int)(account_id), (int)(ad_id[k]), ad_name[k], ad_img_url[k])

                            self.cursor.execute(sql1)
                            try:
                                self.connection.commit()
                            except Exception as e:
                                self.connection.rollback()

                        else:
                            sql_img = "update oppo_feeds_stat_ad_img_report set account_id=%d,ad_id=%d,ad_name='%s',img_url='%s'where account_id=%d and ad_id=%d;" % (
                                (int)(account_id), (int)(ad_id[k]), ad_name[k], ad_img_url[k],account_id,(int)(ad_id[k]))
                            self.cursor.execute(sql_img)
                            try:
                                self.connection.commit()
                            except Exception as e:
                                self.connection.rollback()

        # # # <<<<<<<<<<<<<<<<<<<<<<<<<7.获取账户类型为搜索类型的报表>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        print('enter搜索类型的报表')
        print interval_day
        print yesterday

        search_index_url = 'https://e.oppomobile.com/searchStat/index'
        search_index_text = self.s.get(url=search_index_url, headers=ad_headers)
        sea_tr_url = 'https://e.oppomobile.com/searchStat/trend'
        data = {
            'daterange': '{}~{}'.format(interval_day, yesterday),
            'appId': '',
            'keyWord': '',
            'type': '1'
        }
        search_headers = {
            'Referer': 'https://e.oppomobile.com/searchStat/index',
            'tk': self.s.cookies.get('tk'),
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36',
        }
        searchStat_index_data = self.s.post(url=sea_tr_url, headers=search_headers, data=data).text

        if len(json.loads(searchStat_index_data)['data']) == 0:
            print('搜索报表没有数据')



        else:
            print('进入搜索报表数据')
            search_index_json_data = json.loads(searchStat_index_data)

            report_date = (str)(search_index_json_data['data'][len(search_index_json_data['data']) - 1]['dt'])
            print "report_date is "+report_date

            json_data = search_index_json_data['data'][len(search_index_json_data['data']) - 1]
            json_data = json.dumps(json_data)

            search_stat_id= "select id from oppo_search_stat_total_report where account_id =%d and report_date='%s';" % (
            (int)(account_id), report_date)
            print search_stat_id

            self.cursor.execute(search_stat_id)
            search_result = self.cursor.fetchone()

            if (search_result == None):
                search_sql = "insert into oppo_search_stat_total_report (account_id,report_date,json_data)values(%d,'%s','%s');" % (
                (int)(account_id), report_date, json_data)
                print search_sql
                self.cursor.execute(search_sql)
                try:
                    self.connection.commit()
                except Exception as e:
                    self.connection.rollback()


            else:
                sql_search_report = "update oppo_search_stat_total_report set account_id=%d,report_date='%s',json_data='%s' where account_id=%d and report_date='%s';" % (
                (int)(account_id), report_date, json_data,account_id,report_date)

                self.cursor.execute(sql_search_report)
                try:
                    self.connection.commit()
                except Exception as e:
                    self.connection.rollback()


if __name__ == "__main__":
    oppo = Oppo_spider()
    oppo.login_in()















































