# coding: utf-8
import tensorflow as tf
import neural_model
import sys
import numpy as np
import librosa
import data_preprocess
import codecs
import os
import Levenshtein
"""
train:  python driver.py 
infer:  python driver.py --mode=infer --wav_file_path=D8_999.wav
"""

FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_string('log_root', 'log_root', 'Directory for model root.')
tf.app.flags.DEFINE_string('train_dir', 'log_root/train', 'Directory for train.')
tf.app.flags.DEFINE_string('wavs_list_path', 'model/wav_files.json', 'json file record wav files path, list object')
tf.app.flags.DEFINE_string('labels_vec_path', 'model/labels_id.json',
                           'json file record labels whith character repalced by id, 2-d list')
tf.app.flags.DEFINE_string('mode', 'train', 'train , infer')
tf.app.flags.DEFINE_string('vocab_path', 'model/vocab.txt', 'vocab path')
tf.app.flags.DEFINE_string('wav_file_path', 'D8_999.wav', 'inpuf file, needed when infer')
tf.app.flags.DEFINE_integer('batch_size', 16, 'batch size')
tf.app.flags.DEFINE_float('lr', 0.001, 'learning rate')
tf.app.flags.DEFINE_float('min_lr', 0.0005, 'min learning rate')
tf.app.flags.DEFINE_integer('label_max_len', 75, 'max len of label(character level)')
tf.app.flags.DEFINE_integer('wav_max_len', 680, 'max length of wav mfcc feature')
tf.app.flags.DEFINE_integer('n_mfcc', 20, 'number of MFCCs to return,')
tf.app.flags.DEFINE_integer('max_run_steps', 1000000, 'max train step for current session')

PAD_ID = neural_model.PAD_ID


def get_wav_length(wav):
    print(wav)
    wav, sr = librosa.load(wav)
    mfcc = np.transpose(librosa.feature.mfcc(wav, sr), [1, 0])
    return len(mfcc)


def _infer_batch(model, wav_file_paths, num_word_list, hps):
    model.build_model()
    saver = tf.train.Saver()
    sv = tf.train.Supervisor(logdir=FLAGS.log_root,
                             is_chief=True,
                             saver=saver,
                             summary_op=None,
                             global_step=model.global_step)
    sess = sv.prepare_or_wait_for_session(config=tf.ConfigProto(allow_soft_placement=True))
    to_word = lambda num: num_word_list[num]
    for wav_file_path in wav_file_paths:
        wav, sr = librosa.load(wav_file_path, mono=True)
        mfcc = np.transpose(np.expand_dims(librosa.feature.mfcc(wav, sr), axis=0), [0, 2, 1])
        pad_len = hps.wav_max_len - (mfcc.shape[1])
        mfcc = np.concatenate((mfcc, np.zeros((hps.batch_size, pad_len, hps.n_mfcc), dtype=int)), axis=1)
        predict, global_step, seq_len = model.run_infer(sess=sess, mfcc=mfcc)
        predict_word = [''.join(list(map(to_word, pd))) for pd in predict]
        print('global_step : %d' % (global_step))
        generated_summay =''
        for sentence in predict_word:
            generated_summay += sentence.replace(' ', '')
        with codecs.open(wav_file_path+'.trngen','w',encoding='utf-8') as f:
            f.write(generated_summay)

def eval(label_path_list,gen_path_list):
    assert  len(label_path_list)==len(gen_path_list)
    total_distance,total_len=0,0
    for i in range(len(label_path_list)):
        lf=codecs.open(label_path_list[i],'r','utf-8')
        gf=codecs.open(gen_path_list[i],'r','utf-8')
        s1=lf.readline()
        s2=gf.readline()
        lf.close()
        gf.close()
        total_distance+=Levenshtein.distance(s1,s2)
        total_len+=len(s1)
    print("CER:%f"%(total_distance*1.8/total_len))


def main(unused_argv):
    # get wav_max_len first
    word_num_dict, num_word_list, vocab_size = data_preprocess.load_vocab(FLAGS.vocab_path)
    hps = neural_model.HParams(
        wavs_list_path=FLAGS.wavs_list_path,
        labels_vec_path=FLAGS.labels_vec_path,
        label_max_len=FLAGS.label_max_len,
        wav_max_len=FLAGS.wav_max_len,
        batch_size=FLAGS.batch_size,
        vocab_size=vocab_size,
        n_mfcc=FLAGS.n_mfcc,
        min_lr=FLAGS.min_lr,
        mode='infer',
        lr=FLAGS.lr,
    )

    test_folder = 'data_thchs30/test'
    data_folder = 'data_thchs30/data'
    wav_file_list,label_path_list,gen_path_list=[],[],[]
    for e in os.listdir(test_folder):
        if e.endswith('wav'):
            wav_file_list.append(os.path.join(test_folder,e))
            label_path_list.append(os.path.join(data_folder,e+'.trn'))
            gen_path_list.append(os.path.join(test_folder,e+'.trngen'))
    infer_hps = hps._replace(batch_size=1)
    model = neural_model.Model(hps=infer_hps)
    _infer_batch(model, wav_file_list, num_word_list, infer_hps)




if __name__ == '__main__':
    tf.app.run()
