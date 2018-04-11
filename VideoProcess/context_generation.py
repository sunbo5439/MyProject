# -*- encoding:utf-8 -*-
from __future__ import print_function

import sys

try:
    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass

import codecs,json
from textrank4zh import TextRank4Keyword, TextRank4Sentence


class Summary_Gen(object):
    def __init__(self):
        self._tr4s = TextRank4Sentence()

    def get_summary(self, text, num_sum=10):
        self._tr4s.analyze(text=text, lower=True, source='all_filters')
        rs_list = []
        for item in self._tr4s.get_key_sentences(num=3):
            rs_list.append(item.sentence)
        return ''.join(rs_list)




def gen_sum():
    sg = Summary_Gen()
    path_desc_voice_file = 'path_desc_voice.json'
    path_desc_voice_list = json.load(codecs.open(path_desc_voice_file, 'r', 'utf-8'))
    for d in path_desc_voice_list:
        voice_text=d['voice_text']
        summary_voice=sg.get_summary(voice_text)
        d['summay_voice']=summary_voice
    json.dump(codecs.open(path_desc_voice_file, 'w', 'utf-8'), ensure_ascii=False, indent=4)
