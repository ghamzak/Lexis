"""
This module contains rules of inference. 
Given verbnet semantic parse, it will deterministically predict the state of entities participating in events.
The moduel is written to read the format of the parse output of SemParse
"""

import json, os, re
import pandas as pd
from from_spacy import token_lemmatize, spacyObject
from vsf_extract import vnclassparse, vsffinder
import pprint
pp = pprint.PrettyPrinter(indent=1, compact=True)

def readParse(split, paragraphid):
    """
    returns the list of parses of the sentences in a pragragraph in a certain data split
    """    
    paragraph_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'propara_parsed', split, paragraphid)    
    paragraph_parse_list = []
    for filename in os.listdir(paragraph_directory):
        fileaddress = os.path.join(paragraph_directory, filename)        
        with open(fileaddress) as rf:
            try:
                paragraph_parse_list += [json.load(rf)]
            except json.decoder.JSONDecodeError:
                paragraph_parse_list += [dict()]
                
    return paragraph_parse_list

def readParseOnline(split, paragraphid):    
    raw_sentences_address = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'aristo-leaderboard', 'propara', 'data', split, 'sentences.tsv')
    split_raw_df = pd.read_csv(raw_sentences_address, sep='\t', header=None, names=['pid', 'sid', 'sentence'])
    paragraph = split_raw_df.loc[split_raw_df['pid']==paragraphid].sentence.tolist()
    
    return

def statePrediction(parsedParagraph, participantsList):
    """
    scope: one paragraph
    input: a list of parses for each sentence in a paragraph
    output: a list of states for each participant
    """
    # print(participantsList)
    # print(len(parsedParagraph))
    # print(parsedParagraph[0])
    states = dict(zip(participantsList, [[] for i in range(len(participantsList))]))
    # print(states)
    initial = dict(zip(participantsList, [[] for i in range(len(participantsList))]))
    final = dict(zip(participantsList, [[] for i in range(len(participantsList))])) 
    i = 0
    for sentence_parse in parsedParagraph:
        i += 1        
        numberofevents = len(sentence_parse['props'])
        # print('numberofevents in Sentence {}: {}'.format(i, numberofevents))
        if numberofevents > 0:
            for eventid in range(numberofevents):
                current_event = sentence_parse['props'][eventid]
                current_sense, mainevent, events, spans = current_event['sense'], current_event['mainEvent'], current_event['events'], current_event['spans']
                eventive = [x['text'] for x in spans if x['isPredicate']][0]
                eventive_lemma = token_lemmatize(eventive)
                cur_clause = ' '.join([k['text'] for k in spans])        
                # verb_sense_clause_tuple = (current_sense, eventive, cur_clause)
                # verblemma_sense_tuple = (eventive_lemma, current_sense)
                # print('Event lemma: {}, VN sense: {}'.format(eventive_lemma, current_sense))                
                
                x = vsffinder()
                if eventive_lemma in x.class_based_finder(current_sense): 
                    vsf_current = x.class_based_finder(current_sense)[eventive_lemma]
                    # print('VSF for the verb {} in class {}: {}'.format(eventive_lemma, current_sense, vsf_current))
                
                if events:
                    # print('Events is not empty for this sentence!\n {}'.format(events))
                    states, initial, final = entity_state_update_events(events, states, initial, final)
                    
    return states, initial, final

def entity_state_update_events(events, states, initial, final):
    """
    Here, Lexis only uses VerbNet semantic predicates.
    the scope of this is one sentence. 
    in each sentence, more than one motion can happen to an entity. we need to keep only the first source and last destination.
    we also need to keep track of every entity occurring in a sentence.
    """
    target_entities = list(states.keys())
    predlist, polarity, args, polarpreds = predlist_polarity_args(events) 
    # print('polarpreds: {} \n args: {}'.format(polarpreds, args))   

    destroy_preds = ['alive', 'degradation_material_integrity', 'destroyed', 'suffocated']
    # destroy_preds = {'alive': 'patient', 'degradation_material_integrity': 'patient', 'destroyed': 'patient', 'suffocated': 'patient'}
    create_preds = ['be', 'give_birth', 'develop']
    col_preds = ['emit', 'admit', 'reside', 'avoid', 'free', 'contain', 'has_location', 'penetrating'] #emit with second arg being theme 
    collocation_preds = ['attached', 'mingled', 'contact', 'together']
    vsf_preds = ['emit', 'has_configuration', 'has_material_integrity_state', 'has_position', 'has_orientation'] #emit with second arg being vsf (V_Theme, V_Sound, V_Odor, etc.)
    vsf_preds += ['has_physical_form', 'has_spatial_relationship']
    manner_preds = ['pace']
    cos_preds = ['has_state']
    cos_results_preds = ['adjusted', 'cooked', 'voided', 'harmed', 'covered', 'endangered', 'confined']


    # COE: DESTROY
    def handle_destroy(pred, ppred, polar, states, initial, final):
        # print('handle_destroy')
        entity_in_data, actual_arg_text = findarg(args=args, thematic_role='Patient', role_index_in_subevent=polarpreds.index(ppred.lower()), target_entities=target_entities)
        # if this is in the set of entities in the dataset and should be counted
        if entity_in_data:
            if (pred.lower() == 'alive' and not polar) or (pred.lower() == 'degradation_material_integrity' and polar) or (pred.lower() == 'destroyed' and polar):
                states, initial, final = destroyEntity(entity_in_data[0], states, initial, final)
        return states, initial, final
    
    # COE: CREATE
    # create_preds = ['be', 'give_birth', 'develop'] 
    def handle_create(pred, ppred, polar, states, initial, final):
        if pred.lower() == 'be':
            # print(args)
            entity_in_data, actual_arg_text = findArgByIndex(args=args, argindex=0, role_index_in_subevent=polarpreds.index(ppred.lower()), target_entities=target_entities)            
            # print(entity_in_data)
            # print(actual_arg_text)
            if entity_in_data and checkOrderedConditionOneArg('!be', 'be', events, actual_arg_text):
                states, initial, final = createEntity(entity_in_data[0], states, initial, final)
        elif pred.lower() == 'give_birth':
            entity_in_data, actual_arg_text = findArgByIndex(args=args, argindex=1, role_index_in_subevent=polarpreds.index(ppred.lower()), target_entities=target_entities)
            if entity_in_data:
                states, initial, final = createEntity(entity_in_data[0], states, initial, final)
        elif pred.lower() == 'develop':
            entity_in_data, actual_arg_text = findArgByIndex(args=args, argindex=0, role_index_in_subevent=polarpreds.index(ppred.lower()), target_entities=target_entities)
            if entity_in_data:
                states, initial, final = createEntity(entity_in_data[0], states, initial, final)
                       
        return states, initial, final

    #col_preds = ['emit', 'admit', 'reside', 'avoid', 'free', 'contain', 'has_location', 'penetrating'] #emit with second arg being theme 
    def handle_col(pred, ppred, polar, args, subevent_index, states, initial, final):
        # print('handle_change_of_location')
        if pred.lower() == 'emit':
            moved_entity, source, destination = args[subevent_index][1]['value'], args[subevent_index][0]['value'], '?'                        
        elif pred.lower() == 'admit':
            moved_entity, destination, source = args[subevent_index][1]['value'], args[subevent_index][2]['value'], 'persist'            
        elif pred.lower() == 'reside':
            moved_entity, destination, source = args[subevent_index][0]['value'], args[subevent_index][1]['value'], 'persist'            
        elif pred.lower() == 'avoid':
            # we only can record the locus of a theme, not when the theme is NOT at a location
            pass
        elif pred.lower() == 'free':
            moved_entity, source, destination = args[subevent_index][1]['value'], args[subevent_index][0]['value'], '?'
        elif pred.lower() == 'contain':
            moved_entity, destination, source = args[subevent_index][1]['value'], args[subevent_index][0]['value'], 'persist'            
        elif pred.lower() == 'has_location':
            moved_entity = args[subevent_index][0]['value']
            argrole = args[subevent_index][1]            
            if argrole['type'].lower() in ['source', 'initial location', 'initial_location']: # intersection of source and location
                if ppred == 'has_location':
                    source = argrole['value']                    
                elif ppred == '!has_location':
                    source = '-'
                destination = '?'
                    
            elif argrole['type'].lower() in ['goal', 'destination', 'recipient']: # intersection of goal and location
                if ppred == 'has_location':
                    destination = argrole['value']                    
                elif ppred == '!has_location':
                    destination = '-'
                source = 'persist'  

            elif argrole['type'].lower() == 'location':
                if ppred == 'has_location':
                    destination = argrole['value']                    
                elif ppred == '!has_location':
                    destination = '-'
                source = 'persist'
            


        elif pred.lower() == 'penetrating':
            moved_entity, source, destination = args[subevent_index][0]['value'], 'persist' ,args[subevent_index][1]['value']            

        t = [entity for entity in target_entities for t in entity.split(';') if overlap(t, moved_entity) or overlap(moved_entity, t)]
        if t:
            states, initial, final = moveEntity(entity=t[0], source=source, destination=destination, states=states, initial=initial, final=final)
        return states, initial, final
    
    def handle_collocation(pred, ppred, polar, args, subevent_index, states, initial, final):
        """
        collocation_preds = ['attached', 'mingled', 'contact', 'together']

        """
        if pred.lower() == 'attached':
            pass
        elif pred.lower() == 'mingled':
            pass 
        elif pred.lower() == 'contact':
            pass
        elif pred.lower() == 'together':
            pass
        return states, initial, final
    def handle_vsf(pred, ppred, polar, args, subevent_index, states, initial, final, verb):
        """
        - list of vsf indicating COE:
            * create
            * destroy
        - list of vsf indicateing COL
        - list of vsf indicating other types of change (check recipes dataset)
        """
        
        pass
        return

    for i in range(len(events)):
        """
        iterating over subevents 
        """
        # print(i, events[i])
        pred = predlist[i]
        ppred = polarpreds[i]
        polar = polarity[i]
        if pred in destroy_preds:  
            # handle destroy preds
            states, initial, final = handle_destroy(pred, ppred, polar, states, initial, final)
        elif pred in create_preds:
            # handle create preds
            states, initial, final = handle_create(pred, ppred, polar, states, initial, final)            
        elif pred in col_preds:
            # handle change of location preds
            states, initial, final = handle_col(pred, ppred, polar, args, i, states, initial, final)            
        elif pred in collocation_preds:
            # handle collocation preds
            states, initial, final = handle_collocation(pred, ppred, polar, args, i, states, initial, final)            
        elif pred in vsf_preds:
            pass # handle vsf preds
        elif pred in cos_results_preds:
            pass # handle change of state results preds

    


    return states, initial, final

def destroyEntity(entity, states, initial, final):
    states[entity] += ['DESTROY'] 
    initial[entity] += ['persists']
    final[entity] += ['-']
    return states, initial, final  

def createEntity(entity, states, initial, final):
    states[entity] += ['CREATE']
    initial[entity] += ['-']
    # check how you can modify this line to include the locus of creation
    final[entity] += ['-']
    return states, initial, final    

def moveEntity(entity, source, destination, states, initial, final):
    states[entity] += ['MOVE']
    initial[entity] += [source]
    final[entity] += [destination]
    return states, initial, final


def checkOrderedConditionOneArg(pred1: str, pred2: str, events: list, arg_text: str):
    _, _, args, polarpreds = predlist_polarity_args(events)
    entity_state_change, subevent_states = False, []
    for i in range(len(events)):
        if polarpreds[i] == pred1 and args[i][0]['value'] == arg_text:
            subevent_states += [pred1]
        elif polarpreds[i] == pred2 and args[i][0]['value'] == arg_text:
            subevent_states += [pred2]
    if subevent_states.index(pred1) < subevent_states.index(pred2):
        entity_state_change = True
    return entity_state_change

def predlist_polarity_args(events):
    predlist = [subevent['predicates'][0]['predicateType'] for subevent in events]
    predlist = [re.sub(' ', '_', x).lower() for x in predlist]
    # print(predlist)
    polarity = [subevent['predicates'][0]['polarity'] for subevent in events]
    # print(polarity)
    args = [subevent['predicates'][0]['args'] for subevent in events]
    polarpreds = []
    for i in range(len(events)):
        if not polarity[i]:
            polarpreds += ['!'+predlist[i]]
        else:
            polarpreds += [predlist[i]] 
    # print(polarpreds)
    return predlist, polarity, args, polarpreds

def findVerb(parsedParagraph):    
    return [parsedParagraph[0]['tokens'][i]['text'] for i in range(len(parsedParagraph[0]['tokens'])) if parsedParagraph[0]['tokens'][i]['isPredicate']]

def findarg(args, thematic_role, role_index_in_subevent, target_entities):
    """
    finds the actual entity (per dataset): t
    """
    i = [i for i in range(len(args)) if args[role_index_in_subevent][i]['type'] == thematic_role]
    # print('i found in findarg: {}'.format(i))
    t, a = None, None
    if i:    
        t, a = findArgByIndex(args, i[0], role_index_in_subevent, target_entities)
        # a = args[role_index_in_subevent][i[0]]['value']
        # t = [entity for entity in target_entities for t in entity.split(';') if overlap(t, a)]
        # print('arg in sentence: {}, arg in dataset: {}'.format(a, t))
    return t, a

def findArgByIndex(args, argindex, role_index_in_subevent, target_entities):
    a = args[role_index_in_subevent][argindex]['value']
    t = [entity for entity in target_entities for t in entity.split(';') if overlap(t, a) or overlap(a, t)]    
    return t, a
    

def overlap(string, sub):
    count = start = 0
    while True:
        start = string.find(sub, start) + 1
        if start > 0:
            count+=1
        else:
            return count

def extractClauses(sentenceParse):
    clauses = []
    for i in range(len(sentenceParse['props'])):
        cur_s = ''
        for k in range(len(sentenceParse['props'][i]['spans'])):
            cur_s += sentenceParse['props'][i]['spans'][k]['text']
        clauses += [cur_s]
    return clauses


if __name__ == "__main__":
    print()
    # from util import dataPrepare
    # dev_data = dataPrepare('dev')
    # dev_data_parsed, dev_data_raw, dev_data_participants = dev_data.parseddata, dev_data.rawdata, dev_data.participants
    # # print(dev_data_participants.keys())
    # pid = 4
    # states = dict(zip(dev_data_participants[pid], [[] for i in range(len(dev_data_participants[pid]))]))
    # initial = dict(zip(dev_data_participants[pid], [[] for i in range(len(dev_data_participants[pid]))]))
    # final = dict(zip(dev_data_participants[pid], [[] for i in range(len(dev_data_participants[pid]))]))
    # move = dict(zip(dev_data_participants[pid], [[] for i in range(len(dev_data_participants[pid]))])) 
    # create = dict(zip(dev_data_participants[pid], [[] for i in range(len(dev_data_participants[pid]))]))
    # destroy = dict(zip(dev_data_participants[pid], [[] for i in range(len(dev_data_participants[pid]))]))
    # # print(states) 
    # for sid in range(len(dev_data_parsed[pid])):    
    #     # print(dev_data_raw[pid][sid+1])
    #     sentence_parse = dev_data_parsed[pid][sid]
    #     # pp.pprint(sentence_parse)
    #     # print(sentence_parse)

    #     current_event = sentence_parse['props'][0]
    #     current_sense, _, events, spans = current_event['sense'], current_event['mainEvent'], current_event['events'], current_event['spans']
    #     eventive = [x['text'] for x in spans if x['isPredicate']][0]
    #     eventive_lemma = token_lemmatize(eventive)
    #     cur_clause = ' '.join([k['text'] for k in spans])        
    #     # verb_sense_clause_tuple = (current_sense, eventive, cur_clause)
    #     # verblemma_sense_tuple = (eventive_lemma, current_sense)
    #     # print('Event lemma: {}, VN sense: {}'.format(eventive_lemma, current_sense))               
    #     predlist, polarity, args, polarpreds = predlist_polarity_args(events) 
    #     # print('polarpreds: {} \n args: {}'.format(polarpreds, args))

    #     for i in range(len(events)):
    #         # print('subevent index: {}'.format(i))
    #         pred = predlist[i]        
    #         ppred = polarpreds[i]
    #         polar = polarity[i]
    #         # print('pred: {}, ppred: {}, polarity: {}'.format(pred, ppred, polar))
    #         if pred == 'has_location':
    #             moved_entity = args[i][0]['value'].lower()
    #             loc_argrole = args[i][1]            
    #             if loc_argrole['type'].lower() in ['source', 'initial location', 'initial_location']: # intersection of source and location
    #                 if ppred == 'has_location':
    #                     source = loc_argrole['value']                    
    #                 elif ppred == '!has_location':
    #                     source = '-'
    #                 destination = '?'
                        
    #             elif loc_argrole['type'].lower() in ['goal', 'destination', 'recipient']: # intersection of goal and location
    #                 if ppred == 'has_location':
    #                     destination = loc_argrole['value']                    
    #                 elif ppred == '!has_location':
    #                     destination = '-'
    #                 source = 'persist'  

    #             elif loc_argrole['type'].lower() == 'location':
    #                 if ppred == 'has_location':
    #                     destination = loc_argrole['value']                    
    #                 elif ppred == '!has_location':
    #                     destination = '-'
    #                 source = 'persist'
    #             t = [entity for entity in dev_data_participants[pid] for t in entity.split(';') if overlap(t, moved_entity) or overlap(moved_entity, t)]
    #             # print('entity in dataset: {}'.format(t))
    #             if t:
    #                 states, initial, final = moveEntity(entity=t[0], source=source, destination=destination, states=states, initial=initial, final=final)
                    # states, initial, final = handle_col(pred, ppred, polar, args, i, states, initial, final)            
                    # print('states:',states)
                    # print('initial:',initial)
                    # print('final:',final)
