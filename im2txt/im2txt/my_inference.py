# coding=utf8
# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
r"""Generate captions for images using default beam search parameters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math
import os
import socket
import time
import json

import tensorflow as tf

from im2txt import configuration
from im2txt import inference_wrapper
from im2txt.inference_utils import caption_generator
from im2txt.inference_utils import vocabulary

FLAGS = tf.flags.FLAGS

tf.flags.DEFINE_string("checkpoint_path", "",
                       "Model checkpoint file or directory containing a "
                       "model checkpoint file.")
tf.flags.DEFINE_string("vocab_file", "", "Text file containing the vocabulary.")
tf.flags.DEFINE_string("input_files", "",
                       "File pattern or comma-separated list of file patterns "
                       "of image files.")

tf.logging.set_verbosity(tf.logging.INFO)


def main(_):
    # Build the inference graph.
    g = tf.Graph()
    with g.as_default():
        model = inference_wrapper.InferenceWrapper()
        restore_fn = model.build_graph_from_config(configuration.ModelConfig(),
                                                   FLAGS.checkpoint_path)
    g.finalize()

    # Create the vocabulary.
    vocab = vocabulary.Vocabulary(FLAGS.vocab_file)

    with tf.Session(graph=g) as sess:
        # Load the model from checkpoint.
        restore_fn(sess)

        # Prepare the caption generator. Here we are implicitly using the default
        # beam search parameters. See caption_generator.py for a description of the
        # available beam search parameters.
        generator = caption_generator.CaptionGenerator(model, vocab)

        host = ''  # ''与‘0.0.0.0’表示所有机器都可以连接,'192.168.72.130'连接特定机器
        port = 7777  # 表示启用端口7777，不能使用双引号
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))  # 绑定主机与端口
        s.listen(2)  # 启用两个监听2进程

        while True:
            conn, addr = s.accept()  # 地址接收所有的连接
            print('Got connection from:%s', addr)  # 打印连接地址
            data = conn.recv(4096)  # 一次性可以连接4096字节
            print('get data %s', data)  # 打印客户端请求的数据
            if not data:  # 如果没有收到客户端数据就继续接收
                time.sleep(1.5)  # 每次暂停1.5秒
                continue
            filenames = []
            for file_pattern in data.split(","):
                filenames.extend(tf.gfile.Glob(file_pattern))
            tf.logging.info("Running caption generation on %d files matching %s",
                            len(filenames), FLAGS.input_files)
            rs_obj=[]
            for filename in filenames:
                with tf.gfile.GFile(filename, "r") as f:
                    image = f.read()

                captions = generator.beam_search(sess, image)
                sentence = [vocab.id_to_word(w) for w in captions[0].sentence[1:-1]]
                sentence = " ".join(sentence)
                rs_item = {}
                rs_item['image'] = filename
                rs_item['captions'] = sentence
                rs_obj.append(rs_item)


            conn.sendall(json.dumps(rs_obj,encoding='utf-8',ensure_ascii=False,indent=4))  # 如果有数据就全部回显,并且把回显的字母全部变成大写字母
        conn.close()  # 如果break话，就关闭会话


if __name__ == "__main__":
    tf.app.run()
