#!/usr/bin/env python3
"""Convert geoloc model to JSON format"""
import re
import sys
import logging
import argparse
import gzip
import os
import json
import platform
from enum import Enum, auto


class Mode(Enum):
    NONE = auto()
    TWEETMATRIX = auto()
    CENTROIDS = auto()
    WORD = auto()
    MATRIX = auto()
    NEXTWORD = auto()
    WORDMATRIX = auto()


parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
parser.add_argument('--coords', action='store_true', help='Add coords to output files')
parser.add_argument('--weight', action='store_true', help='Add weight to output files')
parser.add_argument('--word_id', action='store_true', help='Add word id to output files')
parser.add_argument('model_file', help='Geoloc model file')
parser.add_argument('output_dir', help='Model output dir')
args = parser.parse_args()

logging.basicConfig(format='%(asctime)s %(levelname)-s: %(message)s', level=logging.INFO)


def log_unknown_line(l: str):
    logging.error('Unknown line: {}'.format(l))


def word_is_saveable(word: str) -> bool:
    if '*' in word or '?' in word or '\\' in word or '/' in word:
        return False
    if platform.system() == 'Windows' and word in {'con', 'aux', 'prn', 'nul', 'com1', 'com2', 'com3', 'com4', 'com5',
                                                   'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4',
                                                   'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'}:
        return False
    len_word = len(word)
    if len_word > 32 or len_word < 1:
        return False
    return True


with gzip.open(args.model_file, 'rt', encoding='utf-8') as model:
    mode = Mode.NONE
    index = 0
    model_properties = {'wordtypes': 0}
    word_properties = {}

    def save_word(word: str, properties: dict):
        if word_is_saveable(word):
            word_file_name = os.path.join(args.output_dir, 'words', '{word}.json'.format(word=word))
            with open(word_file_name, 'w', encoding='utf-8') as word_file:
                json.dump(properties, word_file, ensure_ascii=False)

    def make_word_properties(word: str) -> dict:
        model_properties['wordtypes'] += 1
        if model_properties['wordtypes'] % 10000 == 0:
            logging.info('Processing word {word}'.format(word=word))
        return {}

    logging.info('Starting conversion')
    os.makedirs(os.path.join(args.output_dir, 'words'), mode=0o755, exist_ok=True)
    for line in model:
        if mode == Mode.NONE:
            if line.startswith('#LONGRANULARITY#'):
                tokens = line.rstrip().split(' ')
                granularity = int(tokens[1])
                model_properties['granularity'] = granularity
            elif line.startswith('#TWEETMATRIX#'):
                model_properties['tweetsmatrix'] = [None] * (granularity * granularity // 2)
                mode = Mode.TWEETMATRIX
            elif line.startswith('#CENTROIDS#'):
                index = 0
                model_properties['centroids'] = []
                mode = Mode.CENTROIDS
            elif line.startswith('#WORD#'):
                logging.debug(line.rstrip())
                tokens = line.split(' ')
                word = tokens[2].rstrip()
                word_properties = make_word_properties(word)
                if args.weight:
                    weight = float(tokens[3]) if len(tokens) == 4 else 1.0
                    word_properties['weight'] = weight
                if args.word_id:
                    word_id = int(tokens[1])
                    word_properties['word_id'] = word_id
                mode = Mode.WORD
            elif line.startswith('#WORDMATRIX#'):
                model_properties['wordmatrix'] = []
                mode = Mode.WORDMATRIX
            else:
                log_unknown_line(line)
        elif mode == Mode.TWEETMATRIX:
            if re.match(r'^\d+ \d+ [0-9e\.+-]+', line):
                tokens = line.rstrip().split(' ')
                x = int(tokens[0])
                y = int(tokens[1])
                value = float(tokens[2])
                model_properties['tweetsmatrix'][x + y * granularity] = value
            elif line.startswith('#END'):
                mode = Mode.NONE
            else:
                log_unknown_line(line)
        elif mode == Mode.CENTROIDS:
            if re.match(r'^[0-9e\.+-]+ [0-9e\.+-]+', line):
                tokens = line.rstrip().split(' ')
                lat = float(tokens[0])
                lon = float(tokens[1])
                model_properties['centroids'].insert(index, [lat, lon])
                index += 1
            elif line.startswith('#END#'):
                mode = Mode.NONE
            else:
                log_unknown_line(line)
        elif mode == Mode.WORD:
            if re.match(r'^[0-9e\.+-]+ [0-9e\.+-]+', line):
                tokens = line.rstrip().split(' ')
                lat = float(tokens[0])
                lon = float(tokens[1])
                if args.coords:
                    if 'coords' not in word_properties:
                        word_properties['coords'] = []
                    word_properties['coords'].append([lat, lon])
            elif line.startswith('#MATRIX#'):
                if 'matrix' not in word_properties:
                    word_properties['matrix'] = []
                mode = Mode.MATRIX
            elif line.startswith('#END#'):
                save_word(word, word_properties)
                mode = Mode.NONE
            else:
                log_unknown_line(line)
        elif mode == Mode.MATRIX:
            if re.match(r'^\d+ \d+ [0-9e\.+-]+', line):
                tokens = line.rstrip().split(' ')
                x = int(tokens[0])
                y = int(tokens[1])
                value = float(tokens[2])
                word_properties['matrix'].append({
                    'x': x,
                    'y': y,
                    'value': value
                })
            elif line.startswith('#END#'):
                save_word(word, word_properties)
                mode = Mode.NEXTWORD
            else:
                log_unknown_line(line)
        elif mode == Mode.NEXTWORD:
            if line.startswith('#WORD#'):
                logging.debug(line.rstrip())
                tokens = line.split(' ')
                word = tokens[2].rstrip()
                word_properties = make_word_properties(word)
                if args.weight:
                    weight = float(tokens[3]) if len(tokens) == 4 else 1.0
                    word_properties['weight'] = weight
                if args.word_id:
                    word_id = int(tokens[1])
                    word_properties['word_id'] = word_id
                mode = Mode.WORD
            elif line.startswith('#END#'):
                save_word(word, word_properties)
                mode = Mode.NONE
            else:
                log_unknown_line(line)
        elif mode == Mode.WORDMATRIX:
            if re.match(r'^\d+ \d+ [0-9e\.+-]+', line):
                tokens = line.rstrip().split(' ')
                x = int(tokens[0])
                y = int(tokens[1])
                value = float(tokens[2])
                model_properties['wordmatrix'].append({
                    'x': x,
                    'y': y,
                    'value': value
                })
            elif line.startswith('#END#'):
                mode = Mode.NONE
            else:
                log_unknown_line(line)
    with open(os.path.join(args.output_dir, 'model.json'), 'w', encoding='utf-8') as model_file:
        json.dump(model_properties, model_file)
    logging.info('Finished conversion')
