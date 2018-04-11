# coding: utf-8
import codecs
from collections import Counter
import jieba
import pickle
import os
import json

video_folder = ''


def extract_keyframe(video_items_path, keyframe_folder, number_keyframe):
    video_items = json.load(codecs.open(video_items_path, 'r', 'utf-8'))
    for item in video_items:
        video_path = item['video_path']
        video_name = os.path.basename(video_path).split('.')[0]
        keyframe_basename = os.path.join(keyframe_folder, video_name)
        extract_cmd = 'ffmpeg -i ' + video_path + ' -vf select="eq(pict_type\,PICT_TYPE_I)" -vsync 2 -f image2 -vframes ' + str(
            number_keyframe) + ' ' + keyframe_basename + '_thumbnail_%02d.jpg'
        print extract_cmd
        keyframes_list = [keyframe_basename + '_thumbnail_%02d.jpg' % i for i in range(1, number_keyframe+1)]
        item['keyframes'] = keyframes_list
    json.dump(video_items, codecs.open(video_items_path, 'w', 'utf-8'), ensure_ascii=False, indent=4)



extract_keyframe('VideoProcess/path_desc_voice.json', '/home/derc/sunbo/keyframes',20)
