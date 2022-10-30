from yiban import Yiban
import json
import logging

if __name__ == '__main__':
    try:
        # read data from file.
        with open('config.json', encoding='utf-8') as f:
            json_datas = json.load(f)['address']

        yiban = Yiban(json_datas['mobile'], json_datas['password'], json_datas['task_title'])
        yiban.get_address()
        print("请求到的位置信息：" + str(yiban.get_picture("5221be63e32078bdf1bd9206a0f152ae", json_datas['task_title'])))
    except KeyError as e:
        print("配置文件填写有误，请检查。")
    except Exception as e:
        print(e)
