import pickle
from semparse2 import getParse
# import random
from from_spacy import getPPnominalHead, token_lemmatize, isVerb
from recipes_data_preprocessing import *
from collections import defaultdict
import spacy
nlp = spacy.load('en_core_web_sm')


class RecipeInstance:
    def __init__(self, split, split_data, idx):        
        self.split = split
        self.idx = idx
        # split_data = getSplit(split)
        self.raw_data = getDataPoint(split_data, self.idx)
        self.paragraph_size = len(self.raw_data['text'])
        with open('/data/ghazaleh/datasets/vn_vsf2.pickle', 'rb') as rf:
            self.vsf_dict = pickle.load(rf)
        with open('/data/ghazaleh/datasets/verb_vsf2.pickle', 'rb') as rf:
            self.vsf_dict_verb = pickle.load(rf)
        self.raw_paragraph = dict()
        for k, v in self.raw_data['text'].items():
            self.raw_paragraph[k] = convertListToStr(v)
        self.ingredient_list = self.raw_data['ingredient_list']
        self.ingredients_occurrence_id = self.raw_data['ingredients']
        self.ingredients_occurrence_str = ingredient_occurrence(self.raw_data)
        self.gold_states = self.raw_data['events']
        self.verbs = self.raw_data['verb']
        self.sentence_level = dict()
        for i in range(self.paragraph_size):
            sid = str(i)
            self.sentence_level[sid] = dict()
            self.sentence_level[sid]['sentence'] = self.raw_paragraph[sid]  
            # print(self.sentence_level[sid]['sentence'])          
            if sid in self.verbs:
                self.sentence_level[sid]['sentence_verbs'] = self.verbs[sid]
            else:
                self.sentence_level[sid]['sentence_verbs'] = []
            self.sentence_level[sid]['toparse'] = fixImperative(self.sentence_level[sid]['sentence'], self.sentence_level[sid]['sentence_verbs'])            
            self.sentence_level[sid]['semantic_parse'] = getParse(self.sentence_level[sid]['toparse'])            
            if sid in self.gold_states:
                self.sentence_level[sid]['sentence_gold_states'] = self.gold_states[sid]
            else:
                self.sentence_level[sid]['sentence_gold_states'] = dict()
            if sid in self.ingredients_occurrence_str:
                self.sentence_level[sid]['sentence_ingredients'] = self.ingredients_occurrence_str[sid]
            else:
                self.sentence_level[sid]['sentence_ingredients'] = []
            if self.sentence_level[sid]['sentence_ingredients']:
                try:
                    self.sentence_level[sid]['sentence_predicted_states'] = self.predict_states(sid)
                except IndexError:
                    # print('Culprit:', self.sentence_level[sid]['sentence'])
                    self.sentence_level[sid]['sentence_predicted_states'] = dict()
            else:
                self.sentence_level[sid]['sentence_predicted_states'] = dict()
                        
    def extract_location(self, sid):
        cur_parse = self.sentence_level[sid]['semantic_parse']
        sentence = self.sentence_level[sid]['toparse']
        current_entities = self.sentence_level[sid]['sentence_ingredients']
        locs = []
        if 'props' in cur_parse:
            for i in range(len(cur_parse['props'])):
                spans = cur_parse['props'][i]['spans']
                for constituent in spans:
                    condition1_or = constituent['pb'] == 'AM-LOC'
                    condition2_or = constituent['vn'].lower() == 'destination'
                    condition3_or = (constituent['pb'] == 'AM-MNR' and (constituent['text'].startswith('in ') or constituent['text'].startswith('on ') or constituent['text'].startswith('into ') or constituent['text'].startswith('onto ')))
                    condition4_or = (constituent['pb'] == 'A2' and (constituent['text'].startswith('in ') or constituent['text'].startswith('on ') or constituent['text'].startswith('into ') or constituent['text'].startswith('onto ')))
                    condition5_and = not constituent['text'].startswith('for ')
                    if condition1_or or condition2_or or condition3_or or condition4_or and condition5_and:
                        pp = constituent['text']
                        nphead = getPPnominalHead(sentence, pp)
                        nphead = token_lemmatize(nphead.strip())
                        if nphead.strip() and nphead not in current_entities:
                            if pp.startswith('to '):
                                if not isVerb(nphead):
                                    locs += [nphead.strip()]
                            else:
                                locs += [nphead.strip()]

        if locs:
            return {'location': locs}
        else:
            return {}
    def dictify_vsf(self, vsflist):
        vsf_dict = defaultdict(list)
        for f in vsflist:
            if len(f.split(':')) != 2:
                if f.split(':')[0] == 'accessibility':
                    k, v = 'accessibility', 'not_accessible'
                    vsf_dict[k] += [v]
                else:
                    print('[NOTE] ', f)
            else:
                k, v = [i.strip() for i in f.split(':')]
                vsf_dict[k] += [v]
        return dict(vsf_dict)
    def extract_vsf(self, sid):
        cur_vsf = []
        allowed_keys = ['composition', 'cookedness', 'temperature', 'rotation', 'shape', 'cleanliness', 'accessibility']
        allowed_values = ['change', 'cooked', 'cold', 'hot', 'room', 'nc', 'turned', 'deformed', 'hit', 'molded', 'separated', 'clean', 'dry', 'not_accessible']
        cur_parse = self.sentence_level[sid]['semantic_parse'] 
        sentence = self.sentence_level[sid]['sentence']
        with open('/data/ghazaleh/datasets/bso_direct_vsf3.pickle', 'rb') as rf:
            bso_vsf_verbs = pickle.load(rf)
        if 'props' in cur_parse:       
            for i in range(len(cur_parse['props'])):
                vnc = cur_parse['props'][i]['sense']
                verb = [s['text'] for s in cur_parse['props'][i]['spans'] if s['isPredicate']]
                if verb:
                    verb = verb[0].lower()
                    if ' ' in verb:
                        verb = verb.split(' ')[0]
                    verb = token_lemmatize(verb)
                    # switch this to on and off and see how the eval changes
                    if verb in self.sentence_level[sid]['sentence_verbs']:
                        vnc_main = '-'.join(vnc.split('-')[:2])
                        if vnc_main in self.vsf_dict:
                            if self.vsf_dict[vnc_main][verb]:
                                cur_vsf += self.vsf_dict[vnc_main][verb]
                            elif verb in self.vsf_dict_verb:
                                cur_vsf += self.vsf_dict_verb[verb] 
                        elif verb in self.vsf_dict_verb:
                            cur_vsf += self.vsf_dict_verb[verb]
                spans = cur_parse['props'][i]['spans']
                for constituent in spans:                    
                    condition2_or = constituent['vn'].lower() == 'destination'
                    condition4_or = (constituent['pb'] == 'A2' and (constituent['text'].startswith('in ') or constituent['text'].startswith('on ') or constituent['text'].startswith('into ') or constituent['text'].startswith('onto ')))
                    if condition2_or or condition4_or:
                        pp = constituent['text']
                        nphead = getPPnominalHead(sentence, pp)
                        if nphead.strip() and isVerb(token_lemmatize(nphead.strip())):
                            v = token_lemmatize(nphead.strip())
                            if v in self.vsf_dict_verb:
                                cur_vsf += self.vsf_dict_verb[v]
                
        for v in self.sentence_level[sid]['sentence_verbs']:
            if v != '<NO_CHANGE>' and v in self.vsf_dict_verb:
                cur_vsf += self.vsf_dict_verb[v]
            for l in bso_vsf_verbs:
                if v in l['verbs']:
                    cur_vsf += [l['vsf']]
        
        # if location isA cooking appliance, then cookedness: cooked
        with open('/data/ghazaleh/datasets/cooking_appliances.pickle', 'rb') as rf:
            cooking_appliances = pickle.load(rf)
        for l in self.extract_location(sid):
            if l.lower() in [x.lower() for x in cooking_appliances]:
                cur_vsf += ['cookedness: cooked']
    
        censored = defaultdict(list)
        for k, v in self.dictify_vsf(cur_vsf).items():
            for vv in v:
                if k in allowed_keys and vv in allowed_values:
                    if vv not in censored[k]:
                        censored[k] += [vv]
        return dict(censored)
    def predict_states(self, sid):
        vsf_dict = defaultdict(list)
        vsf_dict.update(self.extract_location(sid))
        vsf_dict.update(self.extract_vsf(sid))
        return dict(vsf_dict)


if __name__ == '__main__':
    print()
    # inst = RecipeInstance('train', 0)
    # for sid in inst.sentence_level.keys():
    #     print(inst.sentence_level[sid]['sentence'])
    #     print(inst.sentence_level[sid]['sentence_gold_states'])
    #     print(inst.sentence_level[sid]['sentence_predicted_states'])
    #     print(inst.sentence_level[sid]['sentence_ingredients'])
    #     print(inst.sentence_level[sid]['sentence_verbs'])
    #     print('\n')