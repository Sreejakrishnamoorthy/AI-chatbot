import nltk
nltk.download('punkt')
from nltk.stem.lancaster import LancasterStemmer

import tensorflow as tf
import numpy as np
import tflearn
import random

import pickle
from tensorflow.python.framework import ops
import os

import json

with open('./resources/intents.json') as json_file:
    intents = json.load(json_file)

intents_file_path = './resources/intents.json'

if not os.path.exists(intents_file_path):
    print(f"Error: The file '{intents_file_path}' does not exist. Please make sure the file exists.")

    exit()

with open(intents_file_path) as json_data:
    intents = json.load(json_data)
stemmer = LancasterStemmer()
ERROR_THRESHOLD = 0.30

with open('./resources/intents.json') as json_data:
    intents = json.load(json_data)

with open('./resources/model_data.json') as json_data:
    model_data = json.load(json_data)


def train():
    words = []
    classes = []
    documents = []
    for intent in intents['intents']:
        for pattern in intent['patterns']:
            token = nltk.word_tokenize(pattern)
            words.extend(token)
            documents.append((token, intent['tag']))
            if intent['tag'] not in classes:
                classes.append(intent['tag'])

    words = [stemmer.stem(w.lower()) for w in words]
    words = sorted(list(set(words)))
    classes = sorted(list(set(classes)))

    training = []
    output = []
    output_empty = [0] * len(classes)

    for doc in documents:
        bag = []
        pattern_words = doc[0]
        pattern_words = [stemmer.stem(word.lower()) for word in pattern_words]
        for w in words:
            bag.append(1) if w in pattern_words else bag.append(0)

        output_row = list(output_empty)
        output_row[classes.index(doc[1])] = 1

        training.append([bag, output_row])

    random.shuffle(training)
    training = np.array(training)

    train_x = list(training[:, 0])
    train_y = list(training[:, 1])

    model_data['inputNodeLength'] = len(train_x[0])
    model_data['outputNodeLength'] = len(train_y[0])

    net = tflearn.input_data(shape=[None, len(train_x[0])])
    net = tflearn.fully_connected(net, 10)
    net = tflearn.fully_connected(net, 10)
    net = tflearn.fully_connected(net, len(train_y[0]), activation='softmax')
    net = tflearn.regression(net)

    # Defining model and setting up tensorboard
    model = tflearn.DNN(net, tensorboard_dir='tflearn_logs')

    # Start training
    model.fit(train_x, train_y, n_epoch=1000, batch_size=8, show_metric=True)
    pickle.dump({'words': words, 'classes': classes, 'train_x': train_x, 'train_y': train_y},
                open("./model/training_data", "wb"))
    with open('./resources/model_data.json', 'w') as meta_data:
        meta_data.write(json.dumps(model_data, indent=4))
    model.save('./model/model.tflearn')


def classify(sentence):
    data = pickle.load(open("./model/training_data", "rb"))
    words = data['words']
    classes = data['classes']
    train_x = data['train_x']
    train_y = data['train_y']

    ops.reset_default_graph()

    net = tflearn.input_data(shape=[None, len(train_x[0])])
    net = tflearn.fully_connected(net, 10)
    net = tflearn.fully_connected(net, 10)
    net = tflearn.fully_connected(net, len(train_y[0]), activation='softmax')
    net = tflearn.regression(net)

    model = tflearn.DNN(net, tensorboard_dir='tflearn_logs')
    model.load('./model/model.tflearn')

    results = model.predict([bow(sentence, words)])[0]
    # filter out predictions below a threshold
    results = [[i, r] for i, r in enumerate(results) if r > ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append((classes[r[0]], r[1]))
    # return tuple of intent and probability
    return return_list


def clean_up_sentence(sentence):
    # tokenizing the pattern
    sentence_words = nltk.word_tokenize(sentence)
    # stemming each word
    sentence_words = [stemmer.stem(word.lower()) for word in sentence_words]
    return sentence_words


# returning bag of words array: 0 or 1 for each word in the bag that exists in the sentence
def bow(sentence, words, show_details=False):
    # tokenizing the pattern
    sentence_words = clean_up_sentence(sentence)
    # generating bag of words
    bag = [0]*len(words)
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s:
                bag[i] = 1
                if show_details:
                    print("found in bag: %s" % w)

    return np.array(bag)


def predict(sentence):
    results = classify(sentence)
    # if we have a classification then find the matching intent tag
    if results:
        # loop as long as there are matches to process
        while results:
            for i in intents['intents']:
                # find a tag matching the first result
                if i['tag'] == results[0][0]:
                    # a random response from the intent
                    return random.choice(i['response'])

            results.pop(0)




