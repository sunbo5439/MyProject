# coding: utf-8
import tensorflow as tf
import numpy as np
import os
from collections import Counter
import librosa
import codecs
import pickle
import json
import sys

reload(sys)
sys.setdefaultencoding('utf8')

import neural_model


def generation_vocab(label_vector_path, vocab_path):
    labels = json.load(codecs.open(label_vector_path, 'r', encoding='utf-8'))
    c = Counter()
    for sentence in labels:
        for tok in sentence:
            c[tok] += 1
    most_common_list = c.most_common()
    with codecs.open(vocab_path, 'w', encoding='utf-8') as f:
        for k, v in most_common_list:
            f.write(k + '\n')


def convert_textlabel_to_idlabel(text_label_path, id_label_path, word_num_dict):
    labels_text = json.load(codecs.open(text_label_path, 'r', encoding='utf-8'))
    labels_id = []
    for sentence in labels_text:
        sentence_ids = [word_num_dict.get(word, len(word_num_dict)) for word in sentence]
        labels_id.append(sentence_ids)
    json.dump(labels_id, codecs.open(id_label_path, 'w', encoding='utf-8'), ensure_ascii=False,indent=4)


def load_vocab(vocab_path):
    num_word_list = []
    with codecs.open(vocab_path, 'r', encoding='utf-8') as f:
        for line in f:
            num_word_list.append(line.strip('\n'))
    word_num_dict = dict(zip(num_word_list, range(len(num_word_list))))
    return word_num_dict, num_word_list, len(num_word_list)


def split_data():
    def doit(folder_path, wav_file_list_path, label_list_path):
        data_path = 'data_thchs30/data/'
        wav_file_list, label_list = [], []
        for e in os.listdir(folder_path):
            if e.endswith('wav'):
                f = codecs.open(os.path.join(data_path, e + '.trn'), 'r', 'utf-8')
                label_text = f.readline().strip('\n\r\t ').replace(' ', '')
                if len(label_text) < 2:
                    continue
                label_list.append(label_text)
                wav_file_list.append(os.path.join(data_path, e))
        json.dump(wav_file_list, codecs.open(wav_file_list_path, 'w', 'utf-8'), ensure_ascii=False, indent=4)
        json.dump(label_list, codecs.open(label_list_path, 'w', 'utf-8'), ensure_ascii=False, indent=4)

    merge_train_folder, test_folder = 'data_thchs30/merge_train', 'data_thchs30/test'
    doit(merge_train_folder,'model/wav_mergetrain_files.json','model/labels_mergetrain.json')
    doit(test_folder,'model/wav_test.json','model/labels_test.json')


if __name__ == '__main__':
    #split_data()
    #generation_vocab('model/labels.json', 'model/vocab.txt')
    word_num_dict, num_word_list, vocab_size = load_vocab('model/vocab.txt')
    convert_textlabel_to_idlabel('model/labels_mergetrain.json', 'model/labels_mergetrain_id.json', word_num_dict)

