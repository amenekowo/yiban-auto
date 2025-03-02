#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author: Rekord
# @Date: 2022-02-06

import getpass
import time
import datetime
import json
from yiban import Yiban
import requests

def main_handler(data=None, extend=None):
    # load json datas
    with open('config.json', encoding='utf-8') as f:
        json_datas = json.load(f)['Forms']
    # print(json_datas)

    total_msg = ""
    pushplus_token = ""
    pushplus_title = ""
    pushplus_msg = ""
    pushplus_url = "http://www.pushplus.plus/send?token="+pushplus_token+"&title="+pushplus_title+"&content="+pushplus_msg+"&template=html"
    
    for data in json_datas:
        success_flag = False
        max_run_count = 10 # 最大运行次数
        day_section_matrix = ['早','午','晚']
        while success_flag == False and max_run_count > 0:
            success_flag = True
            nickname = data['UserInfo']['NickName']
            # Time converted to UTC/GMT+08:00
            today = datetime.datetime.today() + datetime.timedelta(hours=8-int(time.strftime('%z')[0:3]))
            msg = f"%d-%02d-%02d %02d:%02d 用户：{nickname} | Yiban Punch：" % (today.year, today.month, today.day, today.hour, today.minute)
            form_info = data['FormInfo']
            try:
                for day_section in range (0,3):
                    # Force 2 digits month&day
                    task_title = f'%d-%02d-%02d学生健康监测情况（{day_section_matrix[day_section]}）' % (today.year, today.month, today.day)
                    yiban = Yiban(data['UserInfo']['Mobile'], data['UserInfo']['Password'], task_title, today)
                    yiban.submit_task(form_info)
                    msg = f'{msg}{day_section_matrix[day_section]}运行成功。 '
            # If an error occurs due to network problems, the program will continue to run
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                success_flag = False
                max_run_count -= 1
            except Exception as e:
                msg = f'{msg}{e}'
                pushplus_title = "易班自动填写故障"
                pushplus_msg = msg
                requests.get(pushplus_url)
            finally:
                if success_flag == True:                
                    print(msg)
                    total_msg = f'{total_msg}\n\n{msg}'
                time.sleep(1)
    # print(total_msg)
    # send pushplus
    pushplus_title = "易班自动填写运行日志"
    pushplus_msg = total_msg
    requests.get(pushplus_url)

def analyse_form():
    info = {}
    info['account'] = input("请输入手机号：")
    info['password'] =getpass.getpass("请输入密码：") 
    
    yiban = Yiban(info['account'], info['password'], datetime.datetime.today() + datetime.timedelta(hours=8-int(time.strftime('%z')[0:3])))
    # 根据自身情况考虑是否传参
    yiban.analyse()



if __name__ == '__main__':
    # if you want to analyse your own specific form.
    # please uncomment the following line.
    # analyse_form()

    main_handler()
