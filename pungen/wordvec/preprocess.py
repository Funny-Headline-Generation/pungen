# -*- coding: utf-8 -*-

import os
import codecs
import pickle
import argparse
import numpy as np

from fairseq.data.dictionary import Dictionary


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=str, help="data directory path to save vocab and processed data")
    parser.add_argument('--vocab', type=str, help="corpus path for building vocab")
    parser.add_argument('--corpus', type=str, help="corpus path")
    parser.add_argument('--max-dist', type=int, default=5, help="maximum distance to the word")
    parser.add_argument('--max-vocab', type=int, default=-1, help="maximum number of vocab")
    parser.add_argument('--threshold', type=int, default=-1)
    parser.add_argument('--min-dist', type=int, default=0, help="minimum distance to the word")
    args = parser.parse_args()
    return args


class Preprocess(object):

    def __init__(self, max_dist=5, min_dist=0, data_dir='./data/'):
        self.max_dist = max_dist
        self.min_dist = min_dist
        self.data_dir = data_dir

    def skipgram(self, sentence, i):
        iword = sentence[i]
        left = sentence[max(i - self.max_dist, 0) : max(i - self.min_dist, 0)]
        right = sentence[i + 1 + self.min_dist : i + 1 + self.max_dist]
        n = self.max_dist - self.min_dist
        return iword, [self.unk for _ in range(n - len(left))] + left + right + [self.unk for _ in range(n - len(right))]

    def line_to_tokens(self, line):
        for x in line.split():
            ss = x.split('|')
            if len(ss) != 4 or ss[3] in ('PUNCT', 'SPACE'):
                continue
            yield ss[1]

    def build(self, filepath=None, vocab_path=None, threshold=-1, max_vocab=-1):
        if vocab_path and os.path.exists(vocab_path):
            print("loading vocab from {}".format(vocab_path))
            d = Dictionary.load(vocab_path)
            print('vocab size {}'.format(len(d)))
        else:
            print("building vocab...")
            d = Dictionary()
            with open(filepath, 'r') as fin:
                for step, line in enumerate(fin):
                    if not step % 1000:
                        print("working on {}kth line".format(step // 1000), end='\r')
                    tokens = self.line_to_tokens(line.strip())
                    for tok in tokens:
                        d.add_symbol(tok)
            d.finalize(threshold=threshold, nwords=max_vocab)
            print('build done. vocab size {}'.format(len(d)))
            d.save('{}/dict.txt'.format(self.data_dir))

        self.vocab = d
        self.unk = self.vocab.unk()

    def convert(self, filepath):
        print("converting corpus...")
        step = 0
        fout = open('{}/train.bin'.format(args.data_dir), 'wb')
        with codecs.open(filepath, 'r', encoding='utf-8') as file:
            for line in file:
                step += 1
                if not step % 1000:
                    print("working on {}kth line".format(step // 1000), end='\r')
                line = line.strip()
                if not line:
                    continue
                sent = [self.vocab.index(w) for w in self.line_to_tokens(line)]
                if len(sent) <= (self.max_dist - self.min_dist + 1):
                    continue
                for i in range(len(sent)):
                    iword, owords = self.skipgram(sent, i)
                    a = np.array([iword] + owords, dtype=np.uint16)
                    fout.write(a.tobytes())
        fout.close()
        print("conversion done")


if __name__ == '__main__':
    args = parse_args()
    preprocess = Preprocess(max_dist=args.max_dist, min_dist=args.min_dist, data_dir=args.data_dir)
    preprocess.build(vocab_path=args.vocab, filepath=args.corpus, threshold=args.threshold, max_vocab=args.max_vocab)
    preprocess.convert(args.corpus)