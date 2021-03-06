# coding: utf-8
import tensorflow as tf
import neural_model
import sys
import numpy as np
import librosa
import data_preprocess
import codecs, json

"""
train:  python driver.py
infer:  python driver.py --mode=infer --wav_file_path=D8_999.wav
"""

FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_string('log_root', 'log_root', 'Directory for model root.')
tf.app.flags.DEFINE_string('train_dir', 'log_root/train', 'Directory for train.')
tf.app.flags.DEFINE_string('wavs_list_path', 'model/wav_mergetrain_files.json',
                           'json file record wav files path, list object')
tf.app.flags.DEFINE_string('labels_vec_path', 'model/labels_mergetrain_id.json',
                           'json file record labels whith character repalced by id, 2-d list')
tf.app.flags.DEFINE_string('mode', 'train', 'train , infer,batch_inder')
tf.app.flags.DEFINE_string('vocab_path', 'model/vocab.txt', 'vocab path')
tf.app.flags.DEFINE_string('wav_file_path', 'D8_999.wav', 'inpuf file, needed when infer')
tf.app.flags.DEFINE_string('wav_test_paths', 'model/wav_test.json', '')
tf.app.flags.DEFINE_integer('batch_size', 16, 'batch size')
tf.app.flags.DEFINE_float('lr', 0.001, 'learning rate')
tf.app.flags.DEFINE_float('min_lr', 0.0005, 'min learning rate')
tf.app.flags.DEFINE_integer('label_max_len', 75, 'max len of label(character level)')
tf.app.flags.DEFINE_integer('wav_max_len', 720, 'max length of wav mfcc feature')
tf.app.flags.DEFINE_integer('n_mfcc', 20, 'number of MFCCs to return,')
tf.app.flags.DEFINE_integer('max_run_steps', 1000000, 'max train step for current session')

PAD_ID = neural_model.PAD_ID


def get_wav_length(wav):
    print(wav)
    wav, sr = librosa.load(wav)
    mfcc = np.transpose(librosa.feature.mfcc(wav, sr), [1, 0])
    return len(mfcc)


def _train(model, data_batcher):
    with tf.Graph().as_default():
        """Runs model training."""
        model.build_model()
        saver = tf.train.Saver()
        # Train dir is different from log_root to avoid summary directory
        # conflict with Supervisor.
        summary_writer = tf.summary.FileWriter(FLAGS.train_dir, tf.get_default_graph())
        sv = tf.train.Supervisor(logdir=FLAGS.log_root,
                                 is_chief=True,
                                 saver=saver,
                                 summary_op=None,
                                 global_step=model.global_step)
        sess = sv.prepare_or_wait_for_session(config=tf.ConfigProto(allow_soft_placement=True))
        running_avg_loss = 0
        step = 0
        while not sv.should_stop() and step < FLAGS.max_run_steps:
            x_batch, y_batch = data_batcher.get_next_batches()
            (_, batch_loss, train_step, lr) = model.run_train_step(
                sess, x_batch, y_batch)
            loss_summary = tf.Summary()
            loss_summary.value.add(tag='batch_loss', simple_value=batch_loss)
            loss_summary.value.add(tag='learning_rate', simple_value=lr)
            summary_writer.add_summary(loss_summary, train_step)
            sys.stdout.write('train_step:%d  ------ cur_step:%d ---- batch_loss: %f\n' % (train_step, step, batch_loss))
            sys.stdout.flush()
            step += 1
            if step % 100 == 0:
                summary_writer.flush()
        sv.Stop()


def _infer(model, wav_file_path, num_word_list, hps):
    model.build_model()
    wav, sr = librosa.load(wav_file_path, mono=True)
    mfcc = np.transpose(np.expand_dims(librosa.feature.mfcc(wav, sr), axis=0), [0, 2, 1])
    pad_len = hps.wav_max_len - (mfcc.shape[1])
    if pad_len > 0:
        mfcc = np.concatenate((mfcc, np.zeros((hps.batch_size, pad_len, hps.n_mfcc), dtype=int)), axis=1)
    else:
        mfcc = mfcc[:, 0:hps.wav_max_len, :]
    saver = tf.train.Saver()
    sv = tf.train.Supervisor(logdir=FLAGS.log_root,
                             is_chief=True,
                             saver=saver,
                             summary_op=None,
                             global_step=model.global_step)
    sess = sv.prepare_or_wait_for_session(config=tf.ConfigProto(allow_soft_placement=True))
    predict, global_step, seq_len = model.run_infer(sess=sess, mfcc=mfcc)
    print('predict shape:', predict.shape)
    print('seq_len.shape', seq_len.shape)
    print(seq_len)
    to_word = lambda num: num_word_list[num]
    predict_word = [''.join(list(map(to_word, pd))) for pd in predict]
    print('global_step : %d' % (global_step))
    for sentence in predict_word:
        print sentence.replace(' ', '_')


def _infer_batch(model, wav_file_paths, num_word_list, result_path, hps):
    model.build_model()
    saver = tf.train.Saver()
    sv = tf.train.Supervisor(logdir=FLAGS.log_root,
                             is_chief=True,
                             saver=saver,
                             summary_op=None,
                             global_step=model.global_step)
    sess = sv.prepare_or_wait_for_session(config=tf.ConfigProto(allow_soft_placement=True))
    to_word = lambda num: num_word_list[num]
    generated_summay_list = []
    for wav_file_path in wav_file_paths:
        print(wav_file_path)
        wav, sr = librosa.load(wav_file_path, mono=True)
        mfcc = np.transpose(np.expand_dims(librosa.feature.mfcc(wav, sr), axis=0), [0, 2, 1])
        pad_len = hps.wav_max_len - (mfcc.shape[1])
        if pad_len > 0:
            mfcc = np.concatenate((mfcc, np.zeros((hps.batch_size, pad_len, hps.n_mfcc), dtype=int)), axis=1)
        else:
            mfcc = mfcc[:, 0:hps.wav_max_len, :]
        predict, global_step, seq_len = model.run_infer(sess=sess, mfcc=mfcc)
        predict_word = [''.join(list(map(to_word, pd))) for pd in predict]
        generated_summay = ''
        for sentence in predict_word:
            generated_summay += sentence.replace(' ', '')
        generated_summay_list.append(generated_summay)
        json.dump(generated_summay_list, codecs.open(result_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=4)


def main(unused_argv):
    # get wav_max_len first
    word_num_dict, num_word_list, vocab_size = data_preprocess.load_vocab(FLAGS.vocab_path)
    mode = FLAGS.mode
    if mode == 'batch_infer':
        mode = 'infer'
    hps = neural_model.HParams(
        wavs_list_path=FLAGS.wavs_list_path,
        labels_vec_path=FLAGS.labels_vec_path,
        label_max_len=FLAGS.label_max_len,
        wav_max_len=FLAGS.wav_max_len,
        batch_size=FLAGS.batch_size,
        vocab_size=vocab_size,
        n_mfcc=FLAGS.n_mfcc,
        min_lr=FLAGS.min_lr,
        lr=FLAGS.lr,
        mode=mode,
        max_grad_norm=2,
    )

    if FLAGS.mode == 'train':
        model = neural_model.Model(hps=hps)
        batcher = neural_model.Batcher(hps)
        _train(model, batcher)
    elif FLAGS.mode == 'infer':
        infer_hps = hps._replace(batch_size=1)
        model = neural_model.Model(hps=infer_hps)
        _infer(model, FLAGS.wav_file_path, num_word_list, infer_hps)
    elif FLAGS.mode == 'batch_infer':
        infer_hps = hps._replace(batch_size=1)
        model = neural_model.Model(hps=infer_hps)
        wav_file_paths = json.load(codecs.open(FLAGS.wav_test_paths, 'r', 'utf-8'))
        _infer_batch(wav_file_paths, num_word_list, 'model/my_test_label.json', infer_hps)


if __name__ == '__main__':
    tf.app.run()
