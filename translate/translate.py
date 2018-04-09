# /usr/bin/env python
# coding=utf8

import httplib
import md5
import urllib
import random
import json
import codecs
import traceback


class MyTranslator:
    appid_list = [
        ('20180108000113096', '6SoGftc65GEs3GcQSRi7'),  #
        ('20170226000039912', 'BwxN9UzG3yZbRQcJvc7d'),
        ('20180118000116684', 'J0Drvmy9UGcNwNMrDvYK'),
        ('20180118000116674', 'r1mbw_SKVsE5GLnntHXC'),
        ('20180117000115894', '8ebrPfFOUVtZFxQYcUGr'),
        ('20180116000115825', 'LGFk8C3pgW8GBvyG5MrS'),
        ('20180116000115792', '0UKEgR4FvUJdBXfs4XDi'),
        ('20180116000115768', 'PiJ0xQZgGN7nZSws0kmb'),
        ('20180116000115765', 'PP5PEGQx34y8wBuYlmvs'),
        ('20180116000115610', '_dSZB6V4NkvTzQPlAWKZ'),   # 有可能有问题
        ('20180110000113705', 'hOsZSKq1Ya2vPJwBK6wN'),
        ('20180109000113451', '25Yc0E58yOOxIQFONkcO'),  #
        ('20180108000113078', '1fPb7llXqa8EtwppFJMN'),  #
        ('20180108000113073', 'oujj9BU1yWEEsdSMwrei'),  #
        ('20180108000113068', 'SLFbMGFTx2AvGT9U1bM6'),  #
        ('20180108000113070', 'iUi9qyZcsoO10SjGKOE5'),

    ]
    appid_index = 0

    def geturl(self, sentence):
        q = sentence
        appid = self.appid_list[self.appid_index][0]
        secretKey = self.appid_list[self.appid_index][1]
        fromLang = 'en'
        toLang = 'zh'
        salt = random.randint(32768, 65536)
        myurl = '/api/trans/vip/translate'
        sign = appid + q + str(salt) + secretKey
        m1 = md5.new()
        m1.update(sign)
        sign = m1.hexdigest()
        myurl = myurl + '?appid=' + appid + '&q=' + urllib.quote(
            q) + '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(salt) + '&sign=' + sign
        return myurl

    def translate_sentence(self, sentence):
        rs = ''
        try:
            httpClient = httplib.HTTPConnection('api.fanyi.baidu.com')
            myurl = self.geturl(sentence)
            httpClient.request('GET', myurl)
            # response是HTTPResponse对象
            response = httpClient.getresponse()
            obj = json.loads(response.read(), encoding='utf-8')
            trans_rs = obj['trans_result']
            if len(trans_rs) == 1:
                rs = trans_rs[0]['dst']
            else:
                for e in trans_rs:
                    rs += e['dst'] + ' '
        except Exception, e:
            print e, sentence
            traceback.print_exc()
        finally:
            if httpClient:
                httpClient.close()
            return rs


t = MyTranslator()
ss=[
    'a bird is perched on a tree branch',
    'an elephant standing in the middle of a field'
]
for s in ss:
    rs = t.translate_sentence(s)  #一个人骑在上面冲浪板波
    print(rs)
print('\nend\n')
