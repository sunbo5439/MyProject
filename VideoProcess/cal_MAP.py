# coding=utf-8
# https://en.wikipedia.org/wiki/Evaluation_measures_(information_retrieval)

import json, codecs


def averageR(key, doc_list, types=['voice_text']):
    total_count, hit_count = 0, 0
    for i in range(len(doc_list)):
        context = ''
        for type in types:
            context += doc_list[i][type]
        ref = doc_list[i]['ref_text']
        if key in ref:
            total_count += 1
            if key in context:
                hit_count += 1
    return total_count, hit_count


def cal_AR(key_list, doc_list, types=['voice_text']):
    total_count, hit_count = 0, 0
    for key in key_list:
        cur_total_count, cur_hit_count = averageR(key, doc_list, types)
        total_count += cur_total_count
        hit_count += cur_hit_count
    ar = hit_count * 1.0 / total_count
    return ar


def averageP(key, doc_list, types=['voice_text']):
    total_count, hit_count = 0, 0
    for i in range(len(doc_list)):
        context = ''
        for type in types:
            context += doc_list[i][type]
        ref = doc_list[i]['ref_text']
        if key in context:
            total_count += 1
            if key in ref:
                hit_count += 1
    return total_count, hit_count


def cal_AP(key_list, doc_list, types=['voice_text']):
    total_count, hit_count = 0, 0
    for key in key_list:
        cur_total_count, cur_hit_count = averageP(key, doc_list)
        total_count += cur_total_count
        hit_count += cur_hit_count
    ap = hit_count * 1.0 / total_count
    return ap


def cal_Fscore(p, r):
    return 2 * p * r / (p + r)


f = codecs.open('keys.txt', 'r', 'utf-8')
line = f.readline()
keys = line.split()
print('length of keys' + str(len(keys)))
video_items_path = 'video_item_keyframe.json'
video_items = json.load(codecs.open(video_items_path, 'r', 'utf-8'))

print('语音')
ar = cal_AR(keys, video_items, ['voice_text'])
ap = cal_AP(keys, video_items, ['voice_text'])
f = cal_Fscore(ap, ar)
print('ar:' + str(ar))
print('ap:' + str(ap))
print('f :' + str(ar))

print('图片描述')
ar = cal_AR(keys, video_items, ['keyframe_desc_en'])
ap = cal_AP(keys, video_items, ['keyframe_desc_en'])
f = cal_Fscore(ap, ar)
print('ar:' + str(ar))
print('ap:' + str(ap))
print('f :' + str(ar))

print('语音摘要')
ar = cal_AR(keys, video_items, ['summay_voice'])
ap = cal_AP(keys, video_items, ['summay_voice'])
f = cal_Fscore(ap, ar)
print('ar:' + str(ar))
print('ap:' + str(ap))
print('f :' + str(ar))

print('语音+关键帧')
ar = cal_AR(keys, video_items, ['keyframe_desc_en', 'voice_text'])
ap = cal_AP(keys, video_items, ['keyframe_desc_en', 'voice_text'])
f = cal_Fscore(ap, ar)
print('ar:' + str(ar))
print('ap:' + str(ap))
print('f :' + str(ar))

print('语音摘要+关键帧')
ar = cal_AR(keys, video_items, ['keyframe_desc_en', 'summay_voice'])
ap = cal_AP(keys, video_items, ['keyframe_desc_en', 'summay_voice'])
f = cal_Fscore(ap, ar)
print('ar:' + str(ar))
print('ap:' + str(ap))
print('f :' + str(ar))

print('done')
