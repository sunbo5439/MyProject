# coding: utf-8
import codecs
from collections import Counter
import jieba
import pickle
import os
import json
import eyed3
import os
import eyed3
import urllib2
import json
import base64

video_folder = ''


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
    # print(result)
    word = ''
    if result['err_msg'] == 'success.':
        word = result['result'][0].encode('utf-8')
    else:
        print ("错误")
    return word


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


def convert_mp3_2_shortwav(video_items_path, shortwav_folder):
    step_seconds = 50
    video_items = json.load(codecs.open(video_items_path, 'r', 'utf-8'))
    cut_cmd = 'ffmpeg -i %s  -loglevel error -ss %s -t %s -ar 16000  -ac 1 -q:a 2 %s'
    for item in video_items:
        mp3_path = item['mp3_path']
        wav_basename = os.path.basename(mp3_path).split('.')[0]
        duration = int(eyed3.load(mp3_path).info.time_secs)
        short_wav_list = []
        for start in xrange(0, duration, step_seconds):
            wav_path = os.path.join(shortwav_folder, wav_basename + '_%04d.wav' % (start / step_seconds))
            short_wav_list.append(wav_path)
            tmp_cmd = cut_cmd % (mp3_path, str(start), str(step_seconds + 1), wav_path)
            print(tmp_cmd)
            os.system(tmp_cmd)
        item['shortwav_path'] = short_wav_list
    json.dump(video_items, codecs.open(video_items_path, 'w', 'utf-8'), ensure_ascii=False, indent=4)


def speech_recognition_baidu(video_items_path, shortwav_folder):
    video_items = json.load(codecs.open(video_items_path, 'r', 'utf-8'))
    video_items = video_items[:1]
    for item in video_items:
        speech_text = ''
        shortwav_path = item['shortwav_path']
        shortwav_path = shortwav_path[:4]
        for wav_path in shortwav_path:
            try:
                speech_text += wav2text(wav_path)
            except:
                continue
        item['voice_text'] = speech_text
    json.dump(video_items, codecs.open(video_items_path, 'w', 'utf-8'), encoding='utf-8', ensure_ascii=False, indent=4)


# extract_keyframe('VideoProcess/video_item.json', '/home/derc/sunbo/keyframe', 20)
# extract_mp3('VideoProcess/video_item.json', '/home/derc/sunbo/mp3')
# convert_mp3_2_wav('VideoProcess/path_desc_voice.json','/home/derc/sunbo/wav')
# convert_mp3_2_shortwav('VideoProcess/video_item2.json', '/home/derc/sunbo/shortwav')
speech_recognition_baidu('VideoProcess/video_item2.json', '/home/derc/sunbo/shortwav')
