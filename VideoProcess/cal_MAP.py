# coding=utf-8
# https://en.wikipedia.org/wiki/Evaluation_measures_(information_retrieval)

def averageR(key, doc_list):
    total_count, hit_count = 0, 0
    for i in range(len(doc_list)):
        context = doc_list[i]['voice_text']
        ref = doc_list[i]['ref_text']

        if key in ref:
            total_count += 1
            if key in context:
                hit_count += 1
    return total_count, hit_count


def cal_AR(key_list, doc_list):
    total_count, hit_count = 0, 0
    for key in key_list:
        cur_total_count, cur_hit_count = averageR(key, doc_list)
        total_count += cur_total_count
        hit_count += cur_hit_count
    ar = hit_count * 1.0 / total_count


def averageP(key, doc_list):
    total_count, hit_count = 0, 0
    for i in range(len(doc_list)):
        context = doc_list[i]['voice_text']
        ref = doc_list[i]['ref_text']
        if key in context:
            total_count += 1
            if key in ref:
                hit_count += 1
    return total_count, hit_count


def cal_AP(key_list, doc_list):
    total_count, hit_count = 0, 0
    for key in key_list:
        cur_total_count, cur_hit_count = averageP(key, doc_list)
        total_count += cur_total_count
        hit_count += cur_hit_count
    ap = hit_count * 1.0 / total_count

def cal_Fscore(p,r):
    return 2*p*r/(p+r)

keys = [
    '北京', '北京大学',
]
