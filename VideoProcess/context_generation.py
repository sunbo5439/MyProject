# -*- encoding:utf-8 -*-
from __future__ import print_function

import sys

try:
    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass

import codecs,json
import os
import eyed3
import urllib2
import base64
from textrank4zh import TextRank4Keyword, TextRank4Sentence


class Summary_Gen(object):
    def __init__(self):
        self._tr4s = TextRank4Sentence()

    def get_summary(self, text, num_sum=30):
        self._tr4s.analyze(text=text, lower=True, source='all_filters')
        rs_list = []
        for item in self._tr4s.get_key_sentences(num=3):
            rs_list.append(item.sentence)
        return ''.join(rs_list)




def gen_sum(path_desc_voice_file,video_items_path_new):
    sg = Summary_Gen()
    path_desc_voice_list = json.load(codecs.open(path_desc_voice_file, 'r', 'utf-8'))
    for d in path_desc_voice_list:
        voice_text=d['voice_text']
        summary_voice=sg.get_summary(voice_text)
        d['summay_voice']=summary_voice
    json.dump(codecs.open(video_items_path_new, 'w', 'utf-8'), ensure_ascii=False, indent=4)


def wav2text(wav_file, language='zh'):
    baidu_server = "https://openapi.baidu.com/oauth/2.0/token?"
    grant_type = "client_credentials"
    client_id = "RMOy9Uw1TwND2WzrUeyDH66G"  # 填写API Key
    client_secret = "4f45bd174604a8dca81b8e733d2d935e"  # 填写Secret Key

    # 合成请求token的URL
    url = baidu_server + "grant_type=" + grant_type + "&client_id=" + client_id + "&client_secret=" + client_secret

    # 获取token
    res = urllib2.urlopen(url).read()
    data = json.loads(res)
    token = data["access_token"]
    # print token

    # 设置音频属性，根据百度的要求，采样率必须为8000，压缩格式支持pcm（不压缩）、wav、opus、speex、amr
    VOICE_RATE = 16000
    WAVE_FILE = wav_file  # 音频文件的路径
    USER_ID = "hail_hydra"  # 用于标识的ID，可以随意设置
    WAVE_TYPE = "wav"
    LANGUAGE = language

    # 打开音频文件，并进行编码
    f = open(WAVE_FILE, "r")
    speech = base64.b64encode(f.read())
    size = os.path.getsize(WAVE_FILE)
    update = json.dumps(
        {"format": WAVE_TYPE, "rate": VOICE_RATE, "lan": LANGUAGE, 'channel': 1, 'cuid': USER_ID, 'token': token,
         'speech': speech,
         'len': size})
    headers = {'Content-Type': 'application/json'}
    url = "http://vop.baidu.com/server_api"
    req = urllib2.Request(url, update, headers)

    t = urllib2.urlopen(req).read()
    result = json.loads(t)
    print(result)
    word = ''
    if result['err_msg'] == 'success.':
        word = result['result'][0].encode('utf-8')
    else:
        print ("错误")
    return word

video_items_path = 'VideoProcess/video_item_keyframe.json'
video_items_path_new = 'VideoProcess/video_item_keyframe.json'
gen_sum(video_items_path,video_items_path_new)