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
    json.dump(labels_id, codecs.open(id_label_path, 'w', encoding='utf-8'), ensure_ascii=False)


def load_vocab(vocab_path):
    num_word_list = []
    with codecs.open(vocab_path, 'r', encoding='utf-8') as f:
        for line in f:
            num_word_list.append(line.strip('\n'))
    word_num_dict = dict(zip(num_word_list, range(len(num_word_list))))
    return word_num_dict, num_word_list ,len(num_word_list)

if __name__ == '__main__':
    generation_vocab('model/labels.json','model/vocab.txt')
    word_num_dict, num_word_list,vocab_size = load_vocab('model/vocab.txt')
    convert_textlabel_to_idlabel('model/labels.json', 'model/labels_id.json', word_num_dict)
