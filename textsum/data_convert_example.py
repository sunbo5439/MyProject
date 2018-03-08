# coding: utf-8
"""Example of Converting TextSum model data.
Usage:
python data_convert_example.py --command binary_to_text --in_file data/data --out_file data/text_data
python data_convert_example.py --command text_to_binary --in_file data/text_data --out_file data/binary_data
python data_convert_example.py --command binary_to_text --in_file data/binary_data --out_file data/text_data2
diff data/text_data2 data/text_data

python data_convert_example.py --command xml_to_binary --in_file data/PART_I.txt --out_file data/part1_bin
python data_convert_example.py --command binary_to_text --in_file data/part1_bin --out_file data/text_part1

python data_convert_example.py --command generate_vocab --in_file data/PART_I.txt --out_file data/vocab_cn

"""

import struct
import sys
import codecs
import jieba
import pickle
from collections import Counter

reload(sys)
sys.setdefaultencoding('utf-8')

import tensorflow as tf
from tensorflow.core.example import example_pb2

import xml.etree.ElementTree as ET
import re

FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_string('command', 'binary_to_text',
                           'Either binary_to_text or text_to_binary.'
                           'Specify FLAGS.in_file accordingly.')
tf.app.flags.DEFINE_string('in_file', '', 'path to file')
tf.app.flags.DEFINE_string('out_file', '', 'path to file')

SENTENCE_START = '<s>'
SENTENCE_END = '</s>'


def _binary_to_text():
    reader = open(FLAGS.in_file, 'rb')
    writer = open(FLAGS.out_file, 'w')
    while True:
        len_bytes = reader.read(8)
        if not len_bytes:
            sys.stderr.write('Done reading\n')
            return
        str_len = struct.unpack('q', len_bytes)[0]
        tf_example_str = struct.unpack('%ds' % str_len, reader.read(str_len))[0]
        tf_example = example_pb2.Example.FromString(tf_example_str)
        examples = []
        for key in tf_example.features.feature:
            examples.append(
                '%s=%s' % (key, tf_example.features.feature[key].bytes_list.value[0].decode('unicode-escape')))
        writer.write('%s\n' % '\t'.join(examples))
    reader.close()
    writer.close()


def _text_to_binary():
    inputs = open(FLAGS.in_file, 'r').readlines()
    writer = open(FLAGS.out_file, 'wb')
    for inp in inputs:
        tf_example = example_pb2.Example()
        for feature in inp.strip().split('\t'):
            (k, v) = feature.split('=')
            # print(k,v)
            tf_example.features.feature[k].bytes_list.value.extend([v])
        tf_example_str = tf_example.SerializeToString()
        str_len = len(tf_example_str)
        writer.write(struct.pack('q', str_len))
        writer.write(struct.pack('%ds' % str_len, tf_example_str))
    writer.close()


def _xml_to_binary():
    source_path = FLAGS.in_file
    writer = open(FLAGS.out_file, 'wb')
    f = codecs.open(source_path, 'r', 'utf-8')
    articles, summarys = [], []
    article_on, summary_on = False, False
    cur_article, cur_summary = '', ''
    for line in f:
        line = line.strip(u'\n\r\t ')
        if line.startswith('<summary>'):
            summary_on = True
        elif line.startswith('</summary>'):
            summary_on = False
            summarys.append(cur_summary)
            cur_summary = ''
        elif line.startswith('<short_text>'):
            article_on = True
        elif line.startswith('</short_text>'):
            article_on = False
            articles.append(cur_article)
            cur_article = ''
        elif article_on:
            cur_article += line
        elif summary_on:
            cur_summary += line
    assert len(summarys) == len(articles)
    for i in range(len(summarys)):
        article = ' '.join(jieba.cut(articles[i]))
        summary = ' '.join(jieba.cut(summarys[i]))
        article_lines = re.split(ur'[。？！；]', article)
        summary_lines = re.split(ur'[。？！；]', summary)
        article = ' '.join(["%s %s %s" % (SENTENCE_START, sent, SENTENCE_END) for sent in article_lines])
        summary = ' '.join(["%s %s %s" % (SENTENCE_START, sent, SENTENCE_END) for sent in summary_lines])
        tf_example = example_pb2.Example()
        tf_example.features.feature['article'].bytes_list.value.extend(
            [article.encode('unicode-escape').decode('string_escape')])
        tf_example.features.feature['abstract'].bytes_list.value.extend(
            [summary.encode('unicode-escape').decode('string_escape')])
        tf_example_str = tf_example.SerializeToString()
        str_len = len(tf_example_str)
        writer.write(struct.pack('q', str_len))
        writer.write(struct.pack('%ds' % str_len, tf_example_str))
    writer.close()


def _generation_vocab():
    source_path = FLAGS.in_file
    des_path = FLAGS.out_file
    c = Counter()
    sf = codecs.open(source_path, 'r', 'utf-8')
    df = codecs.open(des_path, 'w', 'utf-8')
    cur_count = 0
    for line in sf:
        if len(line) < 4:
            continue
        if line[-2] == '>':
            continue
        line = line.strip(u'\n\r\t ')
        for w in jieba.cut(line):
            c[w] += 1
        cur_count += 1
        if cur_count % 10000 == 0:
            print('process %s line' % cur_count)
    pickle.dump(c,open('c.pkl'))
    for k, v in c.most_common():
        df.writer(k + ' ' + v)
    sf.close()
    df.close()


def main(unused_argv):
    assert FLAGS.command and FLAGS.in_file and FLAGS.out_file
    if FLAGS.command == 'binary_to_text':
        _binary_to_text()
    elif FLAGS.command == 'text_to_binary':
        _text_to_binary()
    elif FLAGS.command == 'xml_to_binary':
        _xml_to_binary()
    elif FLAGS.command == 'generate_vocab':
        _generation_vocab()


if __name__ == '__main__':
    tf.app.run()
