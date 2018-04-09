# coding: utf-8
import codecs
import xml.etree.ElementTree as ET
import re
from collections import Counter
import jieba
import pickle


def fn(source_path, des_path):
    f = codecs.open(source_path, 'r', encoding='utf-8')
    df = codecs.open(des_path, 'w', encoding='utf-8')
    for line in f:
        if line.startswith('<doc id'):
            df.write('<doc>\n')
        else:
            df.write(line)
    f.close()
    df.close()


# fn('PART_I.txt', 'PART_I.xml')
# fn('PART_II.txt', 'PART_II.xml')
# fn('PART_III.txt', 'PART_III.xml')

SENTENCE_START = '<s>'
SENTENCE_END = '</s>'


def parse_xml(source_path):
    f = codecs.open(source_path, 'r', 'utf-8')
    articles, summarys = [], []
    article_on, summary_on = False, False
    cur_article, cur_summary = '', ''
    for line in f:
        line = line.strip(u'\n\r\t ')
        if line.startswith('<summary>'):
            summary_on = True
        elif line.startswith('</summary>'):
            summary_on = False
            summarys.append(cur_summary)
            cur_summary = ''
        elif line.startswith('<short_text>'):
            article_on = True
        elif line.startswith('</short_text>'):
            article_on = False
            articles.append(cur_article)
            cur_article = ''
        elif article_on:
            cur_article += line
        elif summary_on:
            cur_summary += line
    assert len(summarys) == len(articles)

    for i in range(len(summarys)):
        article = articles[i]
        summary = summarys[i]
        article_lines = re.split(ur'[。？！；]', article)
        summary_lines = re.split(ur'[。？！；]', summary)
        article = ' '.join(["%s %s %s" % (SENTENCE_START, sent, SENTENCE_END) for sent in article_lines])
        summary = ' '.join(["%s %s %s" % (SENTENCE_START, sent, SENTENCE_END) for sent in summary_lines])
        print article
        print '----------------------------------------------------------------------------------'
        print summary
        print '----------------------------------------------------------------------------------'


# parse_xml('PART_III.xml')


import json, urllib2, urllib

port = 9001


def ner(sentence):
    if len(sentence) == 0:
        return
    properties = {"annotators": "ner", "outputFormat": "json"}
    url = 'http://localhost:' + str(port) + '/?properties=' + urllib.urlencode(properties)
    req = urllib2.Request(url)
    response = urllib2.urlopen(req, sentence)
    rs = response.read()
    obj = json.loads(rs)
    entities = set()
    for sent in obj['sentences']:
        for e in sent['entitymentions']:
            entities.add(e['text'])
    return entities


# entity = ner('北京大学坐落在北京海淀区。中国的现任国家主席是习近平')
# for e in entity:
#     print e

def _generation_vocab():
    source_path = 'PART_III.xml'
    des_path = 'tt'
    c = Counter()
    sf = codecs.open(source_path, 'r', 'utf-8')
    df = codecs.open(des_path, 'w', 'utf-8')
    # for line in sf:
    #     if len(line) < 4:
    #         continue
    #     if line[-2] == '>':
    #         continue
    #     line = line.strip(u'\n\r\t ')
    #     for w in jieba.cut(line):
    #         c[w] += 1
    # pickle.dump(c, open('c.pkl'))
    c = pickle.load(open('c.pkl', 'r'))
    for k, v in c.most_common():
        df.write(k + ' ' + str(v) + '\n')
    sf.close()
    df.close()

#_generation_vocab()

s='\\u672c\\u6587'
print s.decode('unicode_escape')

