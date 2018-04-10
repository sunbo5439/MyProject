# coding: utf-8
import codecs
import json
import re
import os
import sys


def get_Path_Desc(json_path):
    data = json.load(codecs.open(json_path, 'r', 'utf-8'))['Metadata']
    path = data[u'VideoPath']
    program_des = data[u'Program'][u'Description'].get(u'DescriptionofContent', u'')
    scene_des = ' '.join([scene[u'Description'].get(u'DescriptionofContent', u'') for scene in data[u'Scene']])
    sequence_des = ' '.join([seq[u'Description'].get(u'DescriptionofContent', u'') for seq in data[u'Sequence']])
    shot_des = ' '.join([shot[u'Description'].get(u'DescriptionofContent', u'') for shot in data[u'Shot']])

    program_des = re.sub('[\r\n\t]', ' ', program_des)
    sequence_des = re.sub('[\r\n\t]', ' ', sequence_des)
    scene_des = re.sub('[\r\n\t]', ' ', scene_des)
    shot_des = re.sub('[\r\n\t]', ' ', shot_des)

    des = program_des + sequence_des + scene_des + shot_des
    return (path, des)


def process(json_folder):
    path_desc_list = []
    for file_name in os.listdir(json_folder):
        try:
            path_and_desc = get_Path_Desc(os.path.join(json_folder, file_name))
            if ' ' in path_and_desc[0] or u' ' in path_and_desc[0]:
                continue
            path_desc_list.append(path_and_desc)
            print(path_and_desc[0])
        except:
            continue
    print(len(path_desc_list))
    json.dump(path_desc_list, codecs.open('path_desc.json', 'w', 'utf-8'), ensure_ascii=False, indent=4)
    return path_desc_list

def rename():
    path_desc_list = json.load(codecs.open('path_desc.json', 'r', 'utf-8'))
    new_path_desc_list=[]
    for i in range(len(path_desc_list)):
        old_path,desc= path_desc_list[i]
        old_path='/home/derc/sunbo/video/'+old_path.split('/')[-1]
        if not os.path.exists(old_path):
            continue
        new_path='/home/derc/sunbo/video/'+str(i)+'.wmv'
        new_path_desc_list.append([new_path,desc])
        #os.rename(old_path,new_path)
    json.dump(new_path_desc_list, codecs.open('path_desc_new.json', 'w', 'utf-8'), ensure_ascii=False, indent=4)

def rename2():
    root_folder = '/home/derc/sunbo/video'
    for name in  os.listdir(root_folder):
        if not name.endswith('wav'):
            continue
        index=int(name.split('.')[0])
        new_name="%03d" %(index)+'.wmv'
        new_path=os.path.join(root_folder,new_name)
        os.rename(os.path.join(root_folder,name),new_path)

#process('data')
rename2()