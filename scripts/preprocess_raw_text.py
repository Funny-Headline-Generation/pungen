import argparse
import spacy
import re
from unidecode import unidecode
from tqdm import tqdm

nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])
sentencizer = nlp.create_pipe('sentencizer')
nlp.add_pipe(sentencizer, first=True)

print(nlp.pipe_names)
print(nlp.pipeline)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input')
    parser.add_argument('--output')
    parser.add_argument('--min-len', type=int, default=5, help='minimum sentence length')
    parser.add_argument('--max-len', type=int, default=30, help='maximum sentence length')
    args = parser.parse_args()
    return args

def sentence_iter(file_):
    with open(file_, 'r', errors='ignore') as fin:
        cache = []
        for line in fin:
            line = re.sub('\s+', ' ', unidecode(line.strip()))
            cache.append(line)
            if len(cache) == 200:
                docs = nlp.pipe(cache)
                for doc in docs:
                    for s in doc.sents:
                        yield s
                cache = []
        if cache:
            docs = nlp.pipe(cache)
            for doc in docs:
                for s in doc.sents:
                    yield s

def main(args):
    count = 0
    print ("hello")
    #lines = sum(1 for _ in sentence_iter(args.input))
    #print (lines)
    with open(args.output, 'w') as fout, open(args.input, 'r') as fin:
        for s in tqdm(sentence_iter(args.input), total=40274446):
            # s = line.strip().split()
            if len(s) >= args.min_len and len(s) <= args.max_len:
                l = ['{}|{}|{}'.format(token.text, token.lemma_, token.pos_) for token in s]
                fout.write(' '.join(l) + '\n')
                count += 1
    print (count)

if __name__ == '__main__':
    args = parse_args()
    main(args)