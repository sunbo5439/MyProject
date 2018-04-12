# coding: utf-8
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
import json, codecs
import httplib
import md5
import urllib
import random
import json
import codecs
import traceback

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
tf.flags.DEFINE_string("video_items_path", "",
                       "File pattern or comma-separated list of file patterns "
                       "of image files.")

tf.logging.set_verbosity(tf.logging.INFO)


class MyTranslator:
    appid_list = [
        ('20180108000113096', '6SoGftc65GEs3GcQSRi7'),  #
        ('20170226000039912', 'BwxN9UzG3yZbRQcJvc7d'),
        ('20180118000116684', 'J0Drvmy9UGcNwNMrDvYK'),
        ('20180118000116674', 'r1mbw_SKVsE5GLnntHXC'),
        ('20180117000115894', '8ebrPfFOUVtZFxQYcUGr'),
        ('20180116000115825', 'LGFk8C3pgW8GBvyG5MrS'),
        ('20180116000115792', '0UKEgR4FvUJdBXfs4XDi'),
        ('20180116000115768', 'PiJ0xQZgGN7nZSws0kmb'),
        ('20180116000115765', 'PP5PEGQx34y8wBuYlmvs'),
        ('20180116000115610', '_dSZB6V4NkvTzQPlAWKZ'),  # 有可能有问题
        ('20180110000113705', 'hOsZSKq1Ya2vPJwBK6wN'),
        ('20180109000113451', '25Yc0E58yOOxIQFONkcO'),  #
        ('20180108000113078', '1fPb7llXqa8EtwppFJMN'),  #
        ('20180108000113073', 'oujj9BU1yWEEsdSMwrei'),  #
        ('20180108000113068', 'SLFbMGFTx2AvGT9U1bM6'),  #
        ('20180108000113070', 'iUi9qyZcsoO10SjGKOE5'),

    ]
    appid_index = 0

    def geturl(self, sentence):
        q = sentence
        appid = self.appid_list[self.appid_index][0]
        secretKey = self.appid_list[self.appid_index][1]
        fromLang = 'en'
        toLang = 'zh'
        salt = random.randint(32768, 65536)
        myurl = '/api/trans/vip/translate'
        sign = appid + q + str(salt) + secretKey
        m1 = md5.new()
        m1.update(sign)
        sign = m1.hexdigest()
        myurl = myurl + '?appid=' + appid + '&q=' + urllib.quote(
            q) + '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(salt) + '&sign=' + sign
        return myurl

    def translate_sentence(self, sentence):
        rs = ''
        try:
            httpClient = httplib.HTTPConnection('api.fanyi.baidu.com')
            myurl = self.geturl(sentence)
            httpClient.request('GET', myurl)
            # response是HTTPResponse对象
            response = httpClient.getresponse()
            obj = json.loads(response.read(), encoding='utf-8')
            trans_rs = obj['trans_result']
            if len(trans_rs) == 1:
                rs = trans_rs[0]['dst']
            else:
                for e in trans_rs:
                    rs += e['dst'] + ' '
        except Exception, e:
            print
            e, sentence
            traceback.print_exc()
        finally:
            if httpClient:
                httpClient.close()
            return rs


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

    t = MyTranslator()

    with tf.Session(graph=g) as sess:
        # Load the model from checkpoint.
        restore_fn(sess)

        # Prepare the caption generator. Here we are implicitly using the default
        # beam search parameters. See caption_generator.py for a description of the
        # available beam search parameters.
        generator = caption_generator.CaptionGenerator(model, vocab)

        video_items_path = FLAGS.video_items_path
        video_items = json.load(codecs.open(video_items_path, 'r', 'utf-8'))
        for item in video_items:
            keyframes = item['keyframes']
            keyframe_desc_en = ''
            keyframe_desc_cn = ''
            for filename in keyframes:
                with tf.gfile.GFile(filename, "r") as f:
                    image = f.read()
                captions = generator.beam_search(sess, image)
                print("Captions for image %s:" % os.path.basename(filename))
                tmp_list_en = []
                tmp_list_cn = []
                for i, caption in enumerate(captions):
                    # Ignore begin and end words.
                    sentence = [vocab.id_to_word(w) for w in caption.sentence[1:-1]]
                    sentence = " ".join(sentence)
                    print("  %d) %s (p=%f)" % (i, sentence, math.exp(caption.logprob)))
                    tmp_list_en.append(sentence)
                if len(tmp_list_en) > 0:
                    keyframe_desc_en += tmp_list_en[0]
                    keyframe_desc_cn += t.translate_sentence(tmp_list_en[0])
            item['keyframe_desc_en'] = keyframe_desc_en
            item['keyframe_desc_en'] = keyframe_desc_cn
        json.dump(video_items, codecs.open(video_items_path, 'w', 'utf-8'), ensure_ascii=False, indent=4)


if __name__ == "__main__":
    tf.app.run()
