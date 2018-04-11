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
        os.system(extract_cmd)
        keyframes_list = [keyframe_basename + '_thumbnail_%02d.jpg' % i for i in range(1, number_keyframe + 1)]
        item['keyframes'] = keyframes_list
    json.dump(video_items, codecs.open(video_items_path, 'w', 'utf-8'), ensure_ascii=False, indent=4)


def extract_mp3(video_items_path, mp3_folder):
    video_items = json.load(codecs.open(video_items_path, 'r', 'utf-8'))
    for item in video_items:
        video_path = item['video_path']
        mp3_name = os.path.basename(video_path).split('.')[0] + '.mp3'
        mp3_path = os.path.join(mp3_folder, mp3_name)
        extracmp3_cmd = 'ffmpeg -ss 120 ' + ' -i ' + video_path + ' -loglevel error -q:a 0 -map 0:a -ar 16000 -acodec mp3 ' + mp3_path
        if not os.path.exists(mp3_path):
            print(extracmp3_cmd)
            os.system(extracmp3_cmd)
        item['mp3_path'] = mp3_path
    json.dump(video_items, codecs.open(video_items_path, 'w', 'utf-8'), ensure_ascii=False, indent=4)


def convert_mp3_2_wav(video_items_path, wav_folder):
    video_items = json.load(codecs.open(video_items_path, 'r', 'utf-8'))
    for item in video_items:
        mp3_path = item['mp3_path']
        wav_name = os.path.basename(mp3_path).split('.')[0] + '.wav'
        wav_path = os.path.join(wav_folder, wav_name)
        cmd = 'ffmpeg -i ' + mp3_path + ' -loglevel error -ar 16000  -ac 1 -q:a 2 ' + wav_path
        print(cmd)
        item['wav_path'] = wav_path
    json.dump(video_items, codecs.open(video_items_path, 'w', 'utf-8'), ensure_ascii=False, indent=4)


extract_keyframe('VideoProcess/video_item.json', '/home/derc/sunbo/keyframe', 20)
extract_mp3('VideoProcess/video_item.json', '/home/derc/sunbo/mp3')
# convert_mp3_2_wav('VideoProcess/path_desc_voice.json','/home/derc/sunbo/wav')
