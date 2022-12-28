# import os
import pickle
# from semparse2 import getParse
import random
# from from_spacy import getPPnominalHead, token_lemmatize
# from collections import defaultdict
import spacy
nlp = spacy.load('en_core_web_sm')

def prepare_dataset():
    with open('/data/ghazaleh/datasets/recipes/dev2.pickle', 'rb') as rf:
        dev = pickle.load(rf)
    with open('/data/ghazaleh/datasets/recipes/test2.pickle', 'rb') as rf:
        test = pickle.load(rf)

    dataset = dev + test

    train_indices, dev_indices, test_indices = [], [], []
    train_size, dev_size, test_size = 0, 0, 0
    train_size = int(len(dataset)*0.8) + 1
    dev_size = int((len(dataset) - train_size)/2.0)
    # test_size = len(dataset) - train_size - dev_size

    while len(train_indices) < train_size:
        n = random.randint(0, len(dataset)-1)
        if n not in train_indices:
            train_indices += [n]
    # print(len(train_indices))
    while len(dev_indices) < dev_size:
        n = random.randint(0, len(dataset)-1)
        if n not in train_indices and n not in dev_indices:
            dev_indices += [n]
    # print(len(dev_indices))
    for i in range(len(dataset)):
        if i not in train_indices and i not in dev_indices:
            test_indices += [i]
    # print(len(test_indices))

    train_data, dev_data, test_data = [dataset[i] for i in train_indices], [dataset[i] for i in dev_indices], [dataset[i] for i in test_indices]
    return train_data, dev_data, test_data 


def writeDataToPickle():
    train_data, dev_data, test_data = prepare_dataset()
    with open('/data/ghazaleh/datasets/recipes/revamped_data_split/train.pickle', 'wb') as wf:
        pickle.dump(train_data, wf)
    with open('/data/ghazaleh/datasets/recipes/revamped_data_split/dev.pickle', 'wb') as wf:
        pickle.dump(dev_data, wf)
    with open('/data/ghazaleh/datasets/recipes/revamped_data_split/test.pickle', 'wb') as wf:
        pickle.dump(test_data, wf)
    

def getDataPoint(split_data, idx):  
    # data = getSplit(split)    
    return split_data[idx]

def getSplit(split):
    if split == 'train':
        with open('/data/ghazaleh/datasets/recipes/revamped_data_split/train.pickle', 'rb') as rf:
            data = pickle.load(rf)
    elif split == 'dev':
        with open('/data/ghazaleh/datasets/recipes/revamped_data_split/dev.pickle', 'rb') as rf:
            data = pickle.load(rf)
    elif split == 'test':
        with open('/data/ghazaleh/datasets/recipes/revamped_data_split/test.pickle', 'rb') as rf:
            data = pickle.load(rf)
    return data



def convertListToStr(tokenized_sentence):
    return ' '.join(tokenized_sentence)

def ingredient_occurrence(recipe_instance):
    ing_occ = dict()
    for k, v in recipe_instance['ingredients'].items():
        ing_occ[k] = []
        for i in v:
            ing_occ[k] += [recipe_instance['ingredient_list'][i]]
    return ing_occ   

def fixImperative(sentence, verblist):
    doc = nlp(sentence)
    if doc[0].pos_ == 'VERB' or doc[0].text.lower() in verblist:
        sentence = 'you should ' + sentence
    return sentence    



if __name__ == '__main__':
    print()
    # writeDataToPickle()