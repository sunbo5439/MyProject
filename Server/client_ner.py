# --*-- coding:utf-8 --*--
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


ner('我在位于北京的北京大学学习')
