# coding: utf-8
import tensorflow as tf
import numpy as np
import os
from collections import Counter
import librosa
import codecs
import pickle
import json

from joblib import Parallel, delayed

from collections import namedtuple

PAD = '<PAD>'
UNK = '<UNK>'
PAD_ID = 0

HParams = namedtuple('HParams',
                     ' batch_size,vocab_size,lr,min_lr,'
                     'wavs_list_path,labels_vec_path,'
                     'label_max_len,wav_max_len,n_mfcc,'
                     'mode,max_grad_norm'
                     )


class Model(object):
    def __init__(self, hps):
        self.aconv1d_index = 0
        self.conv1d_index = 0
        self.hps = hps
        self.logit = None
        self.loss = None

    def _build_neural_layer(self, n_dim=128, GRU_hidden_size=128):
        hp = self.hps

        #第一个卷积层
        kernal_1 = tf.get_variable('keranl_1', (3, hp.n_mfcc, n_dim), dtype=tf.float32,initializer=tf.random_uniform_initializer(minval=-0.15, maxval=0.15))
        b_1 = tf.get_variable('b_1', [n_dim], dtype=tf.float32, initializer=tf.constant_initializer(0.0))
        conv_1=tf.nn.conv1d(self.X,kernal_1,stride=1,padding='SAME')
        pre_activation_1 = tf.nn.bias_add(conv_1, b_1)
        cnn_1 = tf.nn.relu(pre_activation_1)

        #第二个卷积层
        kernal_2 = tf.get_variable('keranl_2', (5, n_dim, n_dim), dtype=tf.float32,
                                   initializer=tf.random_uniform_initializer(minval=-0.15, maxval=0.15))
        b_2 = tf.get_variable('b_2', [n_dim], dtype=tf.float32, initializer=tf.constant_initializer(0.0))
        conv_2 = tf.nn.conv1d(cnn_1, kernal_2, stride=1, padding='SAME')
        pre_activation_2 = tf.nn.bias_add(conv_2, b_2)
        cnn_2 = tf.nn.relu(pre_activation_2)

        #max_pooling
        out=cnn_2
        #三个GRU
        num_steps = cnn_2.shape.as_list()[-2]
        W = tf.Variable(tf.zeros([GRU_hidden_size, hp.vocab_size]))  # 构建一个变量，代表权重矩阵，初始化为0
        b = tf.Variable(tf.zeros([hp.vocab_size]))  # 构建一个变量，代表偏置，初始化为0
        def make_cell():
            return tf.contrib.rnn.GRUCell(GRU_hidden_size)
        cell = tf.contrib.rnn.MultiRNNCell(
            [make_cell() for _ in range(3)], state_is_tuple=True)

        self._initial_state = cell.zero_state(hp.batch_size, dtype=tf.float32)
        state = self._initial_state

        gru_outputs = []
        with tf.variable_scope("GRU"):
            for time_step in range(num_steps):
                if time_step > 0: tf.get_variable_scope().reuse_variables()
                (cell_output, state) = cell(cnn_2[:, time_step, :], state)
                #cell_output 做全连接 16，128--> 16,vocabsize 在做softmax(这儿没问题，
                # https://docs.scipy.org/doc/numpy-dev/reference/generated/numpy.matmul.html#numpy.matmul
                softmax = tf.nn.softmax(tf.matmul(cell_output, W) + b)
                gru_outputs.append(softmax)
        #output = tf.reshape(gru_outputs, [hp.batch_size, ,])
        #gru_outputs.shape=(wav_max_len,batch_size,n_dim) (680,16,128)
        # 最后卷积层输出是词汇表大小
        # 经过转置换后变成 (16,680,2882)
        self.logit=tf.transpose(gru_outputs, perm=[1, 0, 2])


    def _add_loss(self):
        hps = self.hps
        indices = tf.where(tf.not_equal(tf.cast(self.Y, tf.float32), 0.))
        target = tf.SparseTensor(indices=indices, values=tf.gather_nd(self.Y, indices) - 1,
                                 dense_shape=tf.cast(tf.shape(self.Y), tf.int64))
        self.sequence_len = tf.reduce_sum(
            tf.cast(tf.not_equal(tf.reduce_sum(self.X, reduction_indices=2), 0.), tf.int32),
            reduction_indices=1)
        self.loss = tf.nn.ctc_loss(target, self.logit, self.sequence_len, time_major=False)
        self.batch_loss = tf.reduce_mean(self.loss,name="batch_loss")

    def _add_placeholders(self):
        hps = self.hps
        self.X = tf.placeholder(dtype=tf.float32, shape=[hps.batch_size, hps.wav_max_len, hps.n_mfcc],
                                name='placeholder_x')
        self.Y = tf.placeholder(dtype=tf.int32, shape=[hps.batch_size, hps.label_max_len], name='placeholder_y')

    def _add_train_op(self):
        hps = self.hps
        self._lr_rate = tf.maximum(
            hps.min_lr,  # min_lr_rate.
            tf.train.exponential_decay(hps.lr, self.global_step, 3000, 0.98))
        optimizer = tf.train.GradientDescentOptimizer(self._lr_rate)
        tvars = tf.trainable_variables()
        grads, global_norm = tf.clip_by_global_norm(
            tf.gradients(self._loss, tvars), hps.max_grad_norm)
        # tf.summary.scalar('global_norm', global_norm)
        # tf.summary.scalar('learning rate', self._lr_rate)
        self._train_op = optimizer.apply_gradients(
            zip(grads, tvars), global_step=self.global_step, name='train_step')


    def _add_decode_op(self):
        decoded = tf.transpose(self.logit, perm=[1, 0, 2])
        decoded, _ = tf.nn.ctc_beam_search_decoder(decoded, self.sequence_len, merge_repeated=False)
        self.predict = tf.sparse_to_dense(decoded[0].indices, decoded[0].dense_shape, decoded[0].values) + 1
        #self.predict =  tf.sparse_to_dense(decoded[0].indices, decoded[0].shape, decoded[0].values) + 1

    def build_model(self):
        self.global_step = tf.Variable(0, name='global_step', trainable=False)
        self._add_placeholders()
        self._build_neural_layer()
        self._add_loss()
        if self.hps.mode == 'train':
            self._add_train_op()
        elif self.hps.mode == 'infer':
            self._add_decode_op()
        #self._summaries = tf.summary.merge_all()

    def run_train_step(self, sess, x_batch, y_batch):
        to_return = [self.optimizer_op,  self.batch_loss, self.global_step, self._lr_rate]
        return sess.run(to_return, feed_dict={self.X: x_batch, self.Y: y_batch})

    def run_infer(self, sess, mfcc):
        return sess.run([self.predict,self.global_step,self.sequence_len], feed_dict={self.X: mfcc})



class Batcher(object):
    def __init__(self, hps):
        self.wav_file_paths = json.load(codecs.open(hps.wavs_list_path, 'r', encoding='utf-8'))
        self.labels_id_vectors = json.load(codecs.open(hps.labels_vec_path, 'r', encoding='utf-8'))
        self.pointer = 0
        self.batch_size = hps.batch_size
        self.wav_max_len = hps.wav_max_len
        self.label_max_len = hps.label_max_len
        self.n_mfcc = hps.n_mfcc

    def get_next_batches(self):
        total_length = len(self.labels_id_vectors)
        batches_wavs, batches_labels = [], []
        for i in range(self.batch_size):
            wav, sr = librosa.load(self.wav_file_paths[self.pointer])
            mfcc = np.transpose(librosa.feature.mfcc(wav, sr, n_mfcc=self.n_mfcc), [1, 0])
            batches_wavs.append(mfcc.tolist())
            batches_labels.append(self.labels_id_vectors[self.pointer])
            self.pointer = (self.pointer + 1) % total_length
            # 取零补齐
        # label append 0 , 0 对应的字符
        # mfcc 默认的计算长度为20(n_mfcc of mfcc) 作为channel length
        for mfcc in batches_wavs:
            while len(mfcc) < self.wav_max_len:
                mfcc.append([PAD_ID] * self.n_mfcc)
            if(len(mfcc)>self.wav_max_len):
                mfcc=mfcc[:self.wav_max_len]
        for label in batches_labels:
            while len(label) < self.label_max_len:
                label.append(PAD_ID)
            if(len(label)>self.label_max_len):
                label=label[:self.label_max_len]
        rs_x = np.array(batches_wavs, dtype=np.float32)
        rs_y = np.array(batches_labels, dtype=np.int32)
        return rs_x, rs_y
