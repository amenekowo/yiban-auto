#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author: Rekord
# @Date: 2022-02-01

#


import re
import time
import json
import requests
import datetime
from crypter import rsa_encrypt, aes_encrypt, aes_decrypt
import os
import random

os.environ['NO_PROXY']="www.yiban.cn" # cancel proxy

class Yiban():
    AES_KEY = '2knV5VGRTScU7pOq'
    AES_IV = 'UmNWaNtM0PUdtFCs'
    RSA_KEY = '''-----BEGIN PUBLIC KEY-----
            MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA6aTDM8BhCS8O0wlx2KzA
            Ajffez4G4A/QSnn1ZDuvLRbKBHm0vVBtBhD03QUnnHXvqigsOOwr4onUeNljegIC
            XC9h5exLFidQVB58MBjItMA81YVlZKBY9zth1neHeRTWlFTCx+WasvbS0HuYpF8+
            KPl7LJPjtI4XAAOLBntQGnPwCX2Ff/LgwqkZbOrHHkN444iLmViCXxNUDUMUR9bP
            A9/I5kwfyZ/mM5m8+IPhSXZ0f2uw1WLov1P4aeKkaaKCf5eL3n7/2vgq7kw2qSmR
            AGBZzW45PsjOEvygXFOy2n7AXL9nHogDiMdbe4aY2VT70sl0ccc4uvVOvVBMinOp
            d2rEpX0/8YE0dRXxukrM7i+r6lWy1lSKbP+0tQxQHNa/Cjg5W3uU+W9YmNUFc1w/
            7QT4SZrnRBEo++Xf9D3YNaOCFZXhy63IpY4eTQCJFQcXdnRbTXEdC3CtWNd7SV/h
            mfJYekb3GEV+10xLOvpe/+tCTeCDpFDJP6UuzLXBBADL2oV3D56hYlOlscjBokNU
            AYYlWgfwA91NjDsWW9mwapm/eLs4FNyH0JcMFTWH9dnl8B7PCUra/Lg/IVv6HkFE
            uCL7hVXGMbw2BZuCIC2VG1ZQ6QD64X8g5zL+HDsusQDbEJV2ZtojalTIjpxMksbR
            ZRsH+P3+NNOZOEwUdjJUAx8CAwEAAQ==
            -----END PUBLIC KEY-----
            '''
    CSRF = '123456' # Any
    COOKIES = {"csrf_token": CSRF}  # 固定cookie 无需更改
    HEADERS = {"Origin": "https://c.uyiban.com", "User-Agent": "Yiban", "AppVersion": "5.0"}  # 固定头 无需更改    
              
    def __init__(self, mobile, password, task_title, today=datetime.datetime.today() + datetime.timedelta(hours=8-int(time.strftime('%z')[0:3]))):
        self.session = requests.session()
        self.mobile = mobile
        self.password = password
        self.task_title = task_title
        self.today = today
        self.login()

    
    def req(self, url, method='get', cookies={}, headers={}, timeout=5, allow_redirects=True, **kwargs):
        time.sleep(1) # 增加请求延时，避免请求过快 Error104
        data = kwargs.get("data")
        params = kwargs.get("params")
        cookies.update(self.COOKIES)
        headers.update(self.HEADERS)
        if method == 'get':
            resp = self.session.get(
                url     = url, 
                data    = data,
                params  = params,
                headers = headers, 
                cookies = cookies, 
                timeout = timeout,
                allow_redirects = allow_redirects
            )
        elif method == 'post':
            resp = self.session.post(
                url     = url, 
                data    = data,
                params  = params,
                headers = headers, 
                cookies = cookies, 
                timeout = timeout,
                allow_redirects = allow_redirects
            )
        else:
            self.session.close()    # close session
            raise Exception('请求方法错误。')
        return resp


    def login(self):
        resp = self.req(
            method = 'post',
            url = 'https://www.yiban.cn/login/doLoginAjax',
            data = {
                'account':self.mobile,
                'password':self.password,
            }
        )
        if resp.json()['code'] == 200:
            # get yiban_user_token
            print (f'以 {self.mobile} 身份登录...')
            self.access_token = requests.utils.dict_from_cookiejar(resp.cookies)['yiban_user_token']
        else:
            self.session.close()    # close session
            raise Exception(f'登录失败，可能是用户名或密码有误。')
    

    def submit_task(self, form_info):
        # 校本化认证
        self.auth()

        # # 获取未完成任务列表
            #print("----未完成任务列表: ", self.getUncompletedList()['data'])
            #print('\n')
        # # 获取已完成任务列表
            #print("----已完成任务列表: ", self.getCompletedList())
            #print('\n')
        self.auto_fill_form(self.getUncompletedList(), form_info)


    def auth(self):
        # 校本化认证
        resp = self.req(
            url='http://f.yiban.cn/iframe/index', 
            params={'act': 'iapp7463'},
            cookies={'yiban_user_token': self.access_token},
            allow_redirects=False
        )
        verify = re.findall(r"verify_request=(.*?)&", resp.headers.get("Location"))[0]
        self.req(
            url='https://api.uyiban.com/base/c/auth/yiban', 
            params={'verifyRequest': verify, 'CSRF': self.CSRF},
        )


    def re_auth(self):
        self.req(
            url='https://oauth.yiban.cn/code/html',
            params={'client_id': '95626fa3080300ea', 'redirect_uri': 'https://f.yiban.cn/iapp7463'},
        )
        self.req(
            method='post',
            url='https://oauth.yiban.cn/code/usersure', 
            data={'client_id': '95626fa3080300ea', 'redirect_uri': 'https://f.yiban.cn/iapp7463'}
        )
        

    def getCompletedList(self):
        resp = self.req(
            url='https://api.uyiban.com/officeTask/client/index/completedList', 
            params={
                'StartTime': (self.today+datetime.timedelta(days=-14)).strftime('%Y-%m-%d'),
                'EndTime': "%d-%02d-%02d 23:59" % (self.today.year, self.today.month, self.today.day),
                'CSRF': self.CSRF
            }
        ).json()
        # auth again
        if resp['data'] is None:
            self.re_auth()
            self.session.close()    # close session
            raise requests.exceptions.ConnectionError("登录过期，请重试。")
        
        return resp
        

    def getUncompletedList(self):
        resp = self.req(
            url='https://api.uyiban.com/officeTask/client/index/uncompletedList', 
            params={
                'StartTime': (self.today+datetime.timedelta(days=-14)).strftime('%Y-%m-%d'),
                'EndTime': "%d-%02d-%02d 23:59" % (self.today.year, self.today.month, self.today.day),
                'CSRF': self.CSRF
            }
        ).json()
        # auth again
        if resp['data'] is None:
            self.re_auth()
            self.session.close()    # close session
            raise requests.exceptions.ConnectionError("登录过期，请重试。")

        return resp


    def auto_fill_form(self, resp, form_info):
        today = datetime.datetime.today()
        # traverse task list
        for i in resp['data']:
            if i['Title'] == self.task_title:
                print(f'填充表格 {i["Title"]} 中...')
                task_detail = self.req(
                    url='https://api.uyiban.com/officeTask/client/index/detail', 
                    params={'TaskId': i['TaskId'], 'CSRF': self.CSRF}
                ).json()['data']

                # self.view_completed(task_detail['InitiateId'])
                #print(task_detail)

                extend = {
                    "TaskId":  task_detail["Id"],
                    "title": "学生每日健康监测情况",
                    "content": [
                        {"label": "任务名称", "value": task_detail["Title"]},
                        {"label": "发布机构", "value": task_detail["PubOrgName"]},
                        #{"label": "发布人", "value": task_detail["PubPersonName"]}
                    ]
                }

                data_form = {
                    # 22.10.30 学生类别
                    "903b07c4d51b8ebcf14d9ed9398db569": '本科生',
                    # 22.10.30 当前位置
                    "5221be63e32078bdf1bd9206a0f152ae": {
                        "time": f'{today.year}-{today.month}-{today.day} {today.hour}:{"{:02d}".format(today.minute)}',
                        "longitude": self.get_value_from_key(self.get_value_from_key(form_info, "AddressInfo2"), "longitude"),
                        "latitude": self.get_value_from_key(self.get_value_from_key(form_info, "AddressInfo2"), "latitude"),
                        "address": self.get_value_from_key(self.get_value_from_key(form_info, "AddressInfo2"), "address")
                    },
                    # 22.10.30 体温
                    "f23866960d58448a55c70fbef7f104f9": '35.90 ℃',
                    # 22.10.30 是否有新冠肺炎相关症状
                    "cbee0f084906800e80fc0a4304de97f9": '否',
                    # 22.10.30 10天内是否有中、高、低风险地区旅居史
                    "1afa3233899be3f371fbc6957465bd8b": '否',
                    # 22.10.30 10天内是否曾接触过新冠病毒感染者或其密切接触者
                    "b9087618b21106381cf08f021f5433fd": '否',
                    # 22.10.30 你所在居住位置属于以下哪类区域
                    "695fed783d1c83ee7d5126bffe7cdd38": '常态化地区',
                    # 22.10.30 你现在属于以下哪种情况
                    "859883030b77447963d8f06a93091da7": '校园内静态管理',
                    # 22.10.30 是否校内人员
                    "e944ebb08f9126111d1adb55d41c7140": '是，我在学校',
                    # 22.10.30 今天是否做了核酸检测
                    "7acc9b10550ca12649281fc77817b710": '是',
                    # 22.10.30 本人确认上述情况属实
                    "376ea41464235daa916087016af43975": '是'
                    # 22.8.31 截图 保留
                    #"id": self.get_picture("id")
                }

                submit_data = {}
                submit_data['WFId'] = task_detail['WFId']
                submit_data['Extend'] = json.dumps(extend, ensure_ascii=False)
                submit_data['Data'] = json.dumps(data_form, ensure_ascii=False)
                postData = json.dumps(submit_data, ensure_ascii=False)  # transfer to json

                resp = self.req(
                    method='post',
                    url=f'https://api.uyiban.com/workFlow/c/my/apply',
                    params={'CSRF': self.CSRF},
                    data={'Str': aes_encrypt(self.AES_KEY, self.AES_IV, postData)}
                ).json()

                # Failed
                if resp['code'] != 0:
                    if resp['msg'] != "任务已结束，不能反馈!":
                        self.session.close()    # close session
                        raise Exception(f"提交时提交失败，错误信息：" + str(resp))
                    else:
                        print (f"任务" + i["Title"] + "已结束，不能反馈，已跳过。")
                break
                
    def view_completed(self, InitiateId):
        return self.req(
            url=f'https://api.uyiban.com/workFlow/c/work/show/view/{InitiateId}',
            params={'CSRF': self.CSRF}
        ).json()['data']['Initiate']

    
    def get_address(self):
        # 校本化认证
        self.auth()
        # traverse task list
        for i in self.getCompletedList()['data']:
            if i['Title'] == self.task_title:
                InitiateId = self.req(
                    url='https://api.uyiban.com/officeTask/client/index/detail', 
                    params={'TaskId': i['TaskId'], 'CSRF': self.CSRF}
                ).json()['data']['InitiateId']
                #print ("请求到的JSON: "+str(self.req(
                    #url=f'https://api.uyiban.com/workFlow/c/work/show/view/{InitiateId}',
                    #params={'CSRF': self.CSRF}
                #).json()['data']['Initiate']['FormDataJson']))
                break


    def get_value_from_key(self, dict, key):
        try:
            return dict[key]
        except KeyError:
            return None            


    # get the pricture of assigned date, default yesterday
    def get_picture(self, id, task_title,
        day = datetime.datetime.today() + datetime.timedelta(hours=8-int(time.strftime('%z')[0:3])) - datetime.timedelta(days=1)):
        # if task_title is blank regenerate task title
        if (len(task_title)==0):
            task_title = f'%d-%02d-%02d学生健康监测情况（早）' % (day.year, day.month, day.day)
        print ("任务标题:" + task_title)
        try: 
            resp = self.getCompletedList()
            # traverse task list
            for i in resp['data']:
                if i['Title'] == task_title:
                    task_detail = self.req(
                        url='https://api.uyiban.com/officeTask/client/index/detail', 
                        params={'TaskId': i['TaskId'], 'CSRF': self.CSRF}
                    ).json()['data']

                    form_data_json = self.view_completed(task_detail['InitiateId'])['FormDataJson']
                    for item in form_data_json:
                        if item['id'] == id:
                            return item['value']
        except Exception:
            return None


    # 分析自定义表单，默认时间为“今天”，默认任务标题为“{today.year}-{today.month}-{today.day}学生健康监测情况（早）”
    def analyse(self, day = datetime.datetime.today() + datetime.timedelta(hours=8-int(time.strftime('%z')[0:3]))):
        # 校本化认证
        self.auth()

        task_title = f'%d-%02d-%02d学生健康监测情况（早）' % (day.year, day.month, day.day)
        resp = self.getCompletedList()
        # traverse task list
        for i in resp['data']:
            if i['Title'] == task_title:
                task_detail = self.req(
                    url='https://api.uyiban.com/officeTask/client/index/detail', 
                    params={'TaskId': i['TaskId'], 'CSRF': self.CSRF}
                ).json()['data']

                print("task_detail:")
                print(task_detail)
                print("data:")
                print(self.view_completed(task_detail['InitiateId']))
                print(self.view_completed(task_detail['InitiateId'])['FormDataJson'])
