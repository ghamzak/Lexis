from util import dataPrepare
from util2 import *
from util3 import *
from motion_util import *
from existence_util import *
from from_spacy import *
import time
from semparse2 import getParse
from statistics import mean

def create_states_for_split(split):
    states = dict()
    split_data = dataPrepare(split)
    start_time = time.time()
    split_data_parsed, split_data_raw, split_data_participants = split_data.parseddata, split_data.rawdata, split_data.participants
    print(f'[INFO] Reading split time: {time.time() - start_time}s')
    print("Updating states for the split '{}'".format(split))
    times = []
    print('There are {} paragraphs to be processed in the {} set!'.format(len(split_data_participants), split))
    for pid in split_data_participants.keys():
        # print(pid)
        start_time = time.time()
        states[pid] = dict(zip(split_data_participants[pid], [dict(zip(list(split_data_raw[pid]), [{'cos_type': 'NONE', 's1': '?', 's2': '?'} for j in range(len(split_data_raw[pid]))])) for i in range(len(split_data_participants[pid]))]))
        paragraph_parsed_ids, paragraph_parsed_sents = [], []
        for kkk in range(len(split_data_parsed[pid])):
            txt = ' '.join([jjj['text'] for jjj in split_data_parsed[pid][kkk]['tokens']])
            if len(paragraph_parsed_sents) > 1 and txt == paragraph_parsed_sents[-1]:            
                pass
            else:
                paragraph_parsed_sents += [txt]
                paragraph_parsed_ids += [kkk]
        parsed_paragraph = [split_data_parsed[pid][z] for z in paragraph_parsed_ids]
        raw_paragraph = ' '.join([split_data_raw[pid][sid+1] for sid in range(len(split_data_raw[pid]))])
        for sid in range(len(split_data_raw[pid])):
            sentence = split_data_raw[pid][sid+1]
            # if sid > 0 and checkSubjectAbsence(sentence):
            #     sentence = fixSubjectAbsence(sentence, split_data_raw[pid][sid])
            #     # see what happens if you re-parse this            
            #     sentence_parse = getParse(sentence)
            sentence_parse = parsed_paragraph[sid]
            for event_id in range(len(sentence_parse['props'])):
                current_event = sentence_parse['props'][event_id]
                current_sense, events, spans = current_event['sense'], current_event['events'], current_event['spans']
                states, destroy_update = updateExistence(target_entities=split_data_participants[pid], events=events, spans=spans, states=states, pid=pid, sid=sid, sentence=sentence, split=split, vn_sense=current_sense, raw_paragraph=raw_paragraph)
                states = updateMotion(target_entities=split_data_participants[pid], events=events, spans=spans, states=states, pid=pid, sid=sid+1, sentence=sentence, split=split, vn_sense=current_sense, destroy_update=destroy_update, raw_paragraph=raw_paragraph)
            
            
        times += [time.time() - start_time]
        if len(times) % 10 == 0:            
            print(f'[INFO] Average time to get states for each paragraph so far: {mean(times)}s')
            print(f'[INFO] {len(times)} paragraphs processed so far!')
        states = transitive_location_update(states, pid)
        # for ent in states[pid].keys():
        #     for sid in states[pid][ent].keys():
        #         states = persistence_function(states, pid, ent, sid)
        states = finalConsistencyCheck(states)
        # print('States Updated for Paragraph ID: "{}"'.format(pid))

    return states

def create_states_for_split_paragraph(split, pid, verbose=True):
    # this is for testing purposes only
    states = dict()
    split_data = dataPrepare(split)
    split_data_parsed, split_data_raw, split_data_participants = split_data.parseddata, split_data.rawdata, split_data.participants
    states[pid] = dict(zip(split_data_participants[pid], [dict(zip(list(split_data_raw[pid]), [{'cos_type': 'NONE', 's1': '?', 's2': '?'} for j in range(len(split_data_raw[pid]))])) for i in range(len(split_data_participants[pid]))]))
    print('Updating states for split "{}", paragraph ID "{}", sentence ID: '.format(split, pid))      
    print(len(split_data_raw[pid]), len(split_data_parsed[pid]))
    paragraph_parsed_ids, paragraph_parsed_sents = [], []
    for kkk in range(len(split_data_parsed[pid])):
        txt = ' '.join([jjj['text'] for jjj in split_data_parsed[pid][kkk]['tokens']])
        if len(paragraph_parsed_sents) > 1 and txt == paragraph_parsed_sents[-1]:            
            pass
        else:
            paragraph_parsed_sents += [txt]
            paragraph_parsed_ids += [kkk]
    parsed_paragraph = [split_data_parsed[pid][z] for z in paragraph_parsed_ids]
    raw_paragraph = ' '.join([split_data_raw[pid][sid+1] for sid in range(len(split_data_raw[pid]))])
    for sid in range(len(split_data_raw[pid])):
        print(sid+1)
        sentence = split_data_raw[pid][sid+1]
        # if sid > 0 and checkSubjectAbsence(sentence):
        #     sentence = fixSubjectAbsence(sentence, split_data_raw[pid][sid])
        #     # see what happens if you re-parse this            
        #     sentence_parse = getParse(sentence)
        sentence_parse = parsed_paragraph[sid]
        for event_id in range(len(sentence_parse['props'])):
            current_event = sentence_parse['props'][event_id]
            current_sense, events, spans = current_event['sense'], current_event['events'], current_event['spans']
            states, destroy_update = updateExistence(target_entities=split_data_participants[pid], events=events, spans=spans, states=states, pid=pid, sid=sid, sentence=sentence, split=split, vn_sense=current_sense, raw_paragraph=raw_paragraph, verbose=verbose)
            states = updateMotion(target_entities=split_data_participants[pid], events=events, spans=spans, states=states, pid=pid, sid=sid+1, sentence=sentence, split=split, vn_sense=current_sense, destroy_update=destroy_update, raw_paragraph=raw_paragraph, verbose=verbose)

    # if len(split_data_parsed[pid]) > len(split_data_raw[pid]):
    #     for kkk in range(len(split_data_parsed[pid])):
    #         txt = ' '.join([jjj['text'] for jjj in split_data_parsed[pid][kkk]['tokens']])
    #         if len(paragraph_parsed_sents) > 1 and txt == paragraph_parsed_sents[-1]:            
    #             pass
    #         else:
    #             paragraph_parsed_sents += [txt]
    #             paragraph_parsed_ids += [kkk]
    #     parsed_paragraph = [split_data_parsed[pid][z] for z in paragraph_parsed_ids]
    # else: 
    #     parsed_paragraph = split_data_parsed[pid]
    # raw_paragraph = ' '.join([split_data_raw[pid][sid+1] for sid in range(len(split_data_raw[pid]))])
    # for sid in range(len(split_data_raw[pid])):
    #     sentence = split_data_raw[pid][sid+1]         
    #     sentence_parse = parsed_paragraph[sid]
    #     if sid > 0 and checkSubjectAbsence(sentence):
    #         sentence = fixSubjectAbsence(sentence, split_data_raw[pid][sid])
    #         # see what happens if you re-parse this            
    #         sentence_parse = getParse(sentence)
    #     print(sid+1, sentence)      
    #     for event_id in range(len(sentence_parse['props'])):
    #         current_event = sentence_parse['props'][event_id]
    #         current_sense, _, events, spans = current_event['sense'], current_event['mainEvent'], current_event['events'], current_event['spans']
    #         print('event_id: {}, vn_sense: {}'.format(event_id, current_sense))
    #         states, destroy_update = updateExistence(target_entities=split_data_participants[pid], events=events, spans=spans, states=states, pid=pid, sid=sid, sentence=sentence, split=split, vn_sense=current_sense, raw_paragraph=raw_paragraph, verbose=verbose)
    #         states = updateMotion(target_entities=split_data_participants[pid], events=events, spans=spans, states=states, pid=pid, sid=sid+1, sentence=sentence, split=split, vn_sense=current_sense, destroy_update=destroy_update, raw_paragraph=raw_paragraph, verbose=verbose)   
    states = transitive_location_update(states, pid)    
    # states = finalConsistencyCheck(states)
    return states


def create_states_for_split_paragraph_sentence(split, pid, sid):
    # this is for testing purposes only
    states = dict()
    split_data = dataPrepare(split)
    split_data_parsed, split_data_raw, split_data_participants = split_data.parseddata, split_data.rawdata, split_data.participants 
    states[pid] = dict(zip(split_data_participants[pid], [dict(zip(list(split_data_raw[pid]), [{'cos_type': 'NONE', 's1': '?', 's2': '?'} for j in range(len(split_data_raw[pid]))])) for i in range(len(split_data_participants[pid]))]))
    print('Updating states for split "{}", paragraph ID "{}", sentence ID "{}".'.format(split, pid, sid))
    sentence = split_data_raw[pid][sid+1]   
    print(sentence)
    sentence_parse = split_data_parsed[pid][sid]
    current_event = sentence_parse['props'][0]
    current_sense, _, events, spans = current_event['sense'], current_event['mainEvent'], current_event['events'], current_event['spans']            
    states, destroy_update = updateExistence(target_entities=split_data_participants[pid], events=events, spans=spans, states=states, pid=pid, sid=sid, sentence=sentence, split=split, vn_sense=current_sense)
    states = updateMotion(target_entities=split_data_participants[pid], events=events, spans=spans, states=states, pid=pid, sid=sid+1, sentence=sentence, split=split, vn_sense=current_sense, destroy_update=destroy_update)
    return states    


if __name__ == '__main__':
    # nnn = 1029
    nnn=37
    # xx = create_states_for_split_paragraph('test', nnn)
    # # split_dummy = dataPrepare('dev').dummy_ordered
    # # current_paragraph_dummy_df = split_dummy[split_dummy[0] == nnn]  
    # # x = create_states_for_split_paragraph('test', 1033)
    # for k, v in xx.items():
    #     print(k)
    #     for kk, vv in v.items():
    #         print(kk)
    #         print(vv)
