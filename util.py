import os, random, re
import pandas as pd
from vnpreds import readParse


setting = 'ego'
# switch to local if local

def entitiesToBeTrackedForSplit(split):
    """
    Here, we take a split, and for each paragraph,
    we extract the entities needed to be tracked.
    input: name of the split (train/dev/test)
    output: a dictionary that maps paragraph IDs to lists of particpants
    the keys of this dictionary are integers, representing paragraph IDs
    """
    if setting == 'local':
        dummypreds = os.path.join(os.path.expanduser('~'), 'codes/github/aristo-leaderboard/propara/data', split, 'dummy-predictions.tsv')
    elif setting == 'ego':
        dummypreds = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'aristo-leaderboard/propara/data', split, 'dummy-predictions.tsv') 
    split_df = pd.read_csv(dummypreds, sep='\t', header=None)
    split_paragraphs = split_df[0].unique().tolist()
    split_participants = dict(zip(split_paragraphs, [[] for i in range(len(split_paragraphs))]))
    for i in range(split_df.shape[0]):
        pid = split_df[0].iloc[i]
        partcipant = split_df[2].iloc[i]
        if partcipant not in split_participants[pid]:
            split_participants[pid] += [partcipant] 
    return split_participants

def get_split_raw_data(split):
    if setting == 'local':
        sentences = os.path.join(os.path.expanduser('~'), 'codes/github/aristo-leaderboard/propara/data', split, 'sentences.tsv')
    elif setting == 'ego':
        sentences = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'aristo-leaderboard/propara/data', split, 'sentences.tsv') 
    sentence_df = pd.read_csv(sentences, sep='\t', header=None)
    split_paragraphs = sentence_df[0].unique().tolist()    
    split_sentences = dict(zip(split_paragraphs, [dict() for p in split_paragraphs]))
    for i in range(sentence_df.shape[0]):
        pid, sid, s = sentence_df[0].iloc[i], sentence_df[1].iloc[i], sentence_df[2].iloc[i]
        split_sentences[pid][sid] = s  
    return split_sentences


def get_split_dummy_predictions(split):
    if setting == 'local':
        pass
    elif setting == 'ego':
        dummy = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'aristo-leaderboard/propara/data', split, 'answers.tsv')
    dummy_df = pd.read_csv(dummy, sep='\t', header=None)
    dummy_df_selected = dummy_df.drop([3,4,5], axis=1)   
    return dummy_df_selected

def reorder_parses_for_split(split):
    """
    purpose: takes a split and for each paragraph, reorders the list of parses.
    this is b/c for an unknown reason, the parses have not been appended to a list in the correct order.
    input: the name of a split
    output: the list of parses for the paragraphs in the given split, with the correct order
    """
    if setting == 'local':
        sentences = os.path.join(os.path.expanduser('~'), 'codes/github/aristo-leaderboard/propara/data', split, 'sentences.tsv')
    elif setting == 'ego':        
        sentences = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'aristo-leaderboard/propara/data', split, 'sentences.tsv') 
    sentence_df = pd.read_csv(sentences, sep='\t', header=None)
    split_paragraphs = sentence_df[0].unique().tolist()    
    split_sentences = dict(zip(split_paragraphs, [dict() for p in split_paragraphs]))
    for i in range(sentence_df.shape[0]):
        pid, sid, s = sentence_df[0].iloc[i], sentence_df[1].iloc[i], sentence_df[2].iloc[i]
        split_sentences[pid][sid] = s 

    # split_sentences = get_split_raw_data(split)
    reordered_split = dict()
    for pid in split_paragraphs:
        parsedparagraph = readParse(split=split, paragraphid=str(pid))
        reordered_paragraph = reorder_parsed_paragraph(parsedparagraph, split_sentences, pid)
        reordered_split[pid] = reordered_paragraph
    return reordered_split

def textextractfromparse(parse):
    """
    purpose: extract the sentence text from a given parse
    input: a sentence parse (semparse output)
    output: the sentence text (inverse parse)
    """   
    text = '' 
    if 'tokens' in parse:
        text = ' '.join([t['text'] for t in parse['tokens']])
    return text


def reorder_parsed_paragraph(parsedparagraph, split_sentences, pid):
    """
    purpose: given a list of parses for one paragraph, reorder
    input: list of parses for one paragraph, pid: paragraph id, dev_sentence: a dictionary that maps sentence id to sentence text in a paragraph of the data
    output: same paragraph parse, reordered
    """
    # test passed
    from difflib import get_close_matches
    reordered_parses = []
    current_order = {i: textextractfromparse(parse) for i, parse in enumerate(parsedparagraph)}
    for k, v in split_sentences[pid].items():
        wrong_index = -1
        s_in_parse = get_close_matches(v, current_order.values())
        if s_in_parse:
            for i, j in current_order.items():
                if j == s_in_parse[0]:
                    wrong_index = i
                    reordered_parses += [parsedparagraph[wrong_index]]
        else:
            reordered_parses += [{'props': [], 'tokens': []}]
    return reordered_parses

class dataPrepare:
    def __init__(self, split) -> None:
        self.split = split
        # parseddata returns a dictionary of parses for each pid for the given split
        self.parseddata = reorder_parses_for_split(self.split)
        # rawdata returns a dictionary of pid as keys and as values, a dictionary mapping sentence id to sentence string.
        self.rawdata = get_split_raw_data(self.split)
        # participants returns a dictionary of lists of participants for each pid in the given split
        self.participants = entitiesToBeTrackedForSplit(self.split)
        # since in the dummy predictions and answers file, the entities are sometimes not in correct order, we will need this in the evaluation step
        self.dummy_ordered = get_split_dummy_predictions(self.split)




# if __name__ == '__main__':
#     x = dataPrepare('test')
#     print(type(x.rawdata), x.rawdata[411])
#     print(len(x.rawdata[411]))
#     print(len(x.parseddata[411]))

#     # example pids: test > 69; dev > 396; train > 43
#     example_test_pid, example_dev_pid, example_train_pid = 69, 396, 43
#     split = 'dev'
#     # testing entity list retrieval; passed
#     sp = entitiesToBeTrackedForSplit(split)
#     if split == 'train':
#         cur_ex = example_train_pid
#     elif split == 'dev':
#         cur_ex = example_dev_pid
#     else:
#         cur_ex = example_test_pid
    
#     print(sp[cur_ex])

#     # testing reorder_parses_for_split, but hopefully renaming this function, since we shouldn't need to reorder when reading the data
#     # ss = reorder_parses_for_split(split)
#     # print(ss[cur_ex])

#     # okay, now I remember. The problem was not with reading the data in order. 
#     # It's accessing the parsed data, and the data have been parsed out of order. 



#     # reordered = reorder_parses_for_split(split) 
#     # print({i: textextractfromparse(p) for i, p in enumerate(reordered[4])})
#     # print({i: textextractfromparse(p) for i, p in enumerate(reordered[388])})
#     print('test passed!')