# coding=utf-8
import os
import eyed3
import urllib2
import json
import base64
import codecs
import pickle


def getSubtitle(video_file_name, start_time, duration):
    """
    use the ffmpeg to extarct the subtitle from the video
    Parameters
    ----------
    video_file_name : str, the vedio file to process,and the resutlt will be saved in video_file_name+ '.srt'
    start_time : accept 60 or 00:00:60  both means extract from the  60 seconds
    duration : 60 or 00:00:60
    """
    input_file = video_file_name
    output_file = video_file_name[:video_file_name.rindex('.')] + '.srt'
    cmd = 'ffmpeg ' + ' -i ' + input_file + ' -ss ' + str(start_time) + ' -t ' + str(
        duration) + ' -loglevel error -map 0:s:0 ' + output_file
    print cmd
    os.system(cmd)


def video2text(video_file_name, text_file_name, start_time, duration):
    """
    use the baidu speech recognition api to translate the radio to text
    Parameters
    ----------
    video_file_name : str, the vedio file to process
    text_file_name  : the file to save the result of speech recognition
    """
    step_seconds = 50
    tempwav = '.temp.wav'
    input_file = video_file_name
    mp3_name = video_file_name[:video_file_name.rindex('.')] + '.mp3'
    wav_name = mp3_name[:-4] + '.wav'
    if os.path.exists(mp3_name):
        os.remove(mp3_name)
    if os.path.exists(wav_name):
        os.remove(wav_name)
    extracmp3_cmd = 'ffmpeg -ss ' + str(start_time) + ' -t ' + str(
        duration) + ' -i ' + input_file + ' -loglevel error -q:a 0 -map 0:a -ar 16000 -acodec mp3 ' + mp3_name
    convert2wav_cmd = 'ffmpeg -i ' + mp3_name + ' -loglevel error -ar 16000  -ac 1 -q:a 2 ' + wav_name
    cutcmd = 'ffmpeg -i %s -loglevel error -ss %s -t %s ' + tempwav
    os.system(extracmp3_cmd)
    os.system(convert2wav_cmd)
    duration = int(eyed3.load(mp3_name).info.time_secs)
    for start in xrange(0, duration, step_seconds):
        tempcmd = cutcmd % (wav_name, str(start), str(step_seconds + 5))
        print tempcmd
        if os.path.exists(tempwav):
            os.remove(tempwav)
        os.system(tempcmd)
        wav2text(tempwav, text_file_name)


def wav2text(wav_file, result_file, language='en'):
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
    #print(result)
    text_rs = ''
    if result['err_msg'] == 'success.':
        text_rs = result['result'][0].encode('utf-8')
        f = open(result_file, 'a')
        f.write(text_rs)
        f.close()
    else:
        print ("错误")
    return text_rs


# getSubtitle('a.mkv','0','60')
# video2text('a.mkv', 'da.txt', 0, 120)
# a=[]
# b= wav2text('data_thchs30/data/D31_906.wav', 'tmp.txt', language='zh')
# a.append(b)

test_wave_files_list = json.load(codecs.open('model/wav_test.json', 'r', 'utf-8'))
baidu_labels = []
for wav in test_wave_files_list:
    print(wav+'-------------------')
    label = wav2text(wav, '.tmp.txt', language='zh')
    print(label)
    baidu_labels.append(label)
pickle.dump(baidu_labels,open('baidu_labels_tmp.pkl'))
json.dump(baidu_labels, codecs.open('model/baidu_rs.json', 'w', 'utf-8'), encoding='utf-8',ensure_ascii=False, indent=4)
