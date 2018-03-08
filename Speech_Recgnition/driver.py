# coding: utf-8
import tensorflow as tf
import neural_model
import sys
import numpy as np
import librosa
import data_preprocess

"""
train:  python driver.py
infer:  python driver.py --mode=infer --wav_file_path=D8_999.wav
"""

FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_string('log_root', 'log_root', 'Directory for model root.')
tf.app.flags.DEFINE_string('train_dir', 'log_root/train', 'Directory for train.')
tf.app.flags.DEFINE_string('wavs_list_path', 'model/wav_files.json', 'Directory for train.')
tf.app.flags.DEFINE_string('labels_vec_path', 'model/labels_id.json', 'Directory for train.')
tf.app.flags.DEFINE_string('mode', 'train', 'train , infer')
tf.app.flags.DEFINE_string('vocab_path', 'model/vocab.txt', 'train , infer')
tf.app.flags.DEFINE_string('wav_file_path', 'D8_999.wav', '')
tf.app.flags.DEFINE_integer('batch_size', 16, '')
tf.app.flags.DEFINE_float('lr', 0.01, '')
tf.app.flags.DEFINE_float('min_lr', 0.0005, '')
tf.app.flags.DEFINE_integer('label_max_len', 35, '')
tf.app.flags.DEFINE_integer('wav_max_len', 680, '')
tf.app.flags.DEFINE_integer('n_mfcc', 20, 'number of MFCCs to return,')
tf.app.flags.DEFINE_integer('max_run_steps', 1000000, '')


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
                                 global_step=model.global_step)
        sess = sv.prepare_or_wait_for_session(config=tf.ConfigProto(allow_soft_placement=True))
        running_avg_loss = 0
        step = 0
        while not sv.should_stop() and step < FLAGS.max_run_steps:
            x_batch, y_batch = data_batcher.get_next_batches()
            (_, batch_loss, train_step) = model.run_train_step(
                sess, x_batch, y_batch)
            batch_loss = tf.Summary()
            batch_loss.value.add(tag='batch_loss', simple_value=batch_loss)
            summary_writer.add_summary(batch_loss, train_step)
            sys.stdout.write('train_step:%d  , batch_loss: %f\n' % train_step % batch_loss)
            sys.stdout.write('step : %d' % step)
            step += 1
            if step % 100 == 0:
                summary_writer.flush()
        sv.Stop()


def _infer(model, wav_file_path, num_word_list):
    model.build_model()
    wav, sr = librosa.load(wav_file_path, mono=True)
    mfcc = np.transpose(np.expand_dims(librosa.feature.mfcc(wav, sr), axis=0), [0, 2, 1])
    saver = tf.train.Saver()
    sv = tf.train.Supervisor(logdir=FLAGS.log_root,
                             is_chief=True,
                             saver=saver,
                             global_step=model.global_step)
    sess = sv.prepare_or_wait_for_session(config=tf.ConfigProto(allow_soft_placement=True))
    predict = model.run_infer(sess=sess, mfcc=mfcc)
    to_word = lambda num: num_word_list[num]
    predict_word = [''.join(list(map(to_word, pd))) for pd in predict]
    for sentence in predict_word:
        print sentence


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
        mode=FLAGS.mode,
        lr=FLAGS.lr,
    )

    if hps.mode == 'train':
        model = neural_model.Model(hps=hps)
        batcher = neural_model.Batcher(hps)
        _train(model, batcher)
    elif hps.mode == 'infer':
        infer_hps = hps._replace(batch_size=1)
        model = neural_model.Model(hps=infer_hps)
        _infer(model, FLAGS.wav_file_path, num_word_list)


if __name__ == '__main__':
    tf.app.run()
