from CN import isLocative, findSynonyms
from from_spacy import *
from coref_analysis import checkCoreference
from vnpreds import overlap
import os, re, sys, string
import Levenshtein as lev
import pickle
import pandas as pd



with open('/data/ghazaleh/symbolic/mysemlink.pickle', 'rb') as rf:
    mysemlink = pickle.load(rf)

with open(os.path.join('/data/ghazaleh/datasets/knowledge_pickles/', 'located.pickle'), 'rb') as rf:
    locateddict = pickle.load(rf)    
# with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'CN', 'part.pickle'), 'rb') as rf:
#     partdict = pickle.load(rf)    

def commonsense_location(tokenized_paragraph, entity):
    sims = []    
    doc1 = nlp2(tokenized_paragraph)
    # doc1 = nlp(tokenized_paragraph)
    for tp in locateddict[entity]:
        word, weight = tp
        if word.strip():
            doc2 = nlp2(word)
            # doc2 = nlp(word)
            if doc2 and doc2.vector_norm:
                sims += [(word, doc1.similarity(doc2)*float(weight))]
    if sims:
        sims = sorted(sims, key=lambda x:x[1], reverse=True)
        # print('For ', entity, ': found commonsense location:', sims[0])
        return [sims[0][0]]
    else:
        return sims

def predlist_polarity_args(events, args_pb):
    predlist = [subevent['predicates'][i]['predicateType'] for subevent in events for i in range(len(subevent['predicates']))]
    predlist = [re.sub(' ', '_', x).lower() for x in predlist]
    polarity = [subevent['predicates'][i]['polarity'] for subevent in events for i in range(len(subevent['predicates']))]
    args = [subevent['predicates'][i]['args'] for subevent in events for i in range(len(subevent['predicates']))]
    polarpreds, pred_triples_abstract, pb_pred_triples_abstract, pred_tuple_abstract, pb_pred_tuples_abstract = [], [], [], [], []
    vn_tuples_abstract_general, pb_tuples_abstract_general = [], []
    for i in range(len(predlist)):
        if not polarity[i]:
            polarpreds += ['!'+predlist[i]]
        else:
            polarpreds += [predlist[i]] 

    for i in range(len(polarpreds)):
        pp = polarpreds[i]  
        aa = [a['type'].lower() for a in args[i]]
        if len(aa) == 2:
            pred_triples_abstract += [(pp, tuple(aa))]
        elif len(aa) == 1:
            pred_tuple_abstract += [(pp, aa[0])]
        cur_tuple_list = [pp]
        cur_tuple_list += [re.sub(' ', '_', x) for x in aa]
        vn_tuples_abstract_general += [tuple(cur_tuple_list)]

    for i in range(len(pred_triples_abstract)):
        if len(pred_triples_abstract[i][1]) == 2:
            pred, [a0, a1] = pred_triples_abstract[i]
            pb_a0, pb_a1 = '', ''
            for label in args_pb.keys():
                if a0 and a0 in label.lower():
                    if ' <-> ' in label.lower():
                        pb_a0 = label.split(' <-> ')[0]
                    else:
                        pb_a0 = label.strip()
                elif a1 in label.lower():
                    if ' <-> ' in label.lower():
                        pb_a1 = label.split(' <-> ')[0]
                    else:
                        pb_a1 = label.strip()
            pb_pred_triples_abstract += [(pred, (pb_a0, pb_a1))]
            pb_tuples_abstract_general += [(pred, pb_a0, pb_a1)]
        elif type(pred_triples_abstract[i][1]) == string:
            pred, a = pred_triples_abstract[i]
            pb_a = ''
            for label in args_pb.keys():
                if a and a in label.lower():
                    pb_a = label.split(' <-> ')[0]
            pb_pred_tuples_abstract += [(pred, pb_a)]
            pb_tuples_abstract_general += [(pred, pb_a)]
        
    return predlist, polarity, args, polarpreds, pred_triples_abstract, pb_pred_triples_abstract, pred_tuple_abstract, pb_pred_tuples_abstract, vn_tuples_abstract_general, pb_tuples_abstract_general


def substantiateVNargs(args_vn, args_pb, vn_sense, spans, sentence):
    from from_spacy import lemmatize
    verb = ''
    if 'V <-> Verb' in args_pb:
        verb = args_pb['V <-> Verb']
    elif 'V' in args_pb:
        verb = args_pb['V']
    if not verb:
        return args_vn    
    # print(verb)
    # print(vn_sense)
    # print(sentence)
    # print(args_pb)
    if ' ' not in verb:
        try:
            verb = lemmatize(verb, sentence)
        except IndexError:
            return args_vn
        if len([v for v in args_vn.values() if v]) != len(args_vn):
            all_rolesets = [x for x in mysemlink if x[0] == verb]
            y = [(rs[1], len(set(list(mysemlink[rs].values())).intersection(set(list(args_vn.keys()))))) for rs in all_rolesets]
            y = sorted(y, key=lambda x: x[1], reverse=True)
            if y:
                mypbroleset = y[0][0]
                # print('pb role:', mypbroleset)
                mykey = (verb, mypbroleset, vn_sense)
                semlinkmapping = mysemlink[mykey]
                empty_vn_args = [vnr for vnr, a in args_vn.items() if not a]
                for vnr in empty_vn_args:
                    prb = [re.sub('RG', '', k) for k, v in semlinkmapping.items() if v.lower() == vnr.lower()]
                    if prb and len(prb) == 1:
                        prb = prb[0]
                        instantiated_arg = [v for k, v in args_pb.items() if k.startswith(prb)]
                        if instantiated_arg and len(instantiated_arg) == 1:
                            args_vn[vnr] = instantiated_arg[0]
    return args_vn

def createArgsDicts(events, spans, vn_sense, sentence):
    args_vn, args_pb = dict(), dict()
    if events:
        args_vn = {arg['type'].lower(): arg['value'].lower() for subevent in events for arg in subevent['predicates'][0]['args']}
    if spans:
        args_pb = {span['label']: span['text'].lower() for span in spans}
        if not args_vn:
            for pk, v in args_pb.items():
                if ' <-> ' in pk and pk.count(' <-> ') == 2 or pk.count(' <-> ') == 1:
                    if pk.split(' <-> ')[1][0].isupper():
                        vn_role = pk.split(' <-> ')[1].lower()
                        args_vn[vn_role] = v
    args_vn = {re.sub(' ', '_', k):v for k, v in args_vn.items()}
    if len([v for v in args_vn.values() if v]) != len(args_vn):
        # we need verb, pb_roleset, and vn_class. challenge is in finding pb_roleset.
        # compare set of args you currently have with each roleset and find the most similar
        # print('args_vn before update:', args_vn)
        args_vn = substantiateVNargs(args_vn, args_pb, vn_sense, spans, sentence)
        # print('args_vn update:', args_vn)
    return args_vn, args_pb


def refactor_target_entities(target_entities):
    refactored_target_entities = dict()
    for t in target_entities:
        if ';' in t:
            for tt in t.split(';'):
                if tt not in refactored_target_entities:
                    refactored_target_entities[tt.strip()] = []
                refactored_target_entities[tt.strip()] += [t]
        else:
            if t not in refactored_target_entities:
                refactored_target_entities[t] = []
            refactored_target_entities[t] += [t]
    return refactored_target_entities

def findDataEntities(refactored_target_entities, comparable_span, target_entities, sentence=None):
    mydataentities = []
    if not [x for x in refactored_target_entities.keys() if "'" in x]:
        # method 1 >> overlap yields better results than get_close_matches
        # from difflib import get_close_matches
        # i = get_close_matches(comparable_span, list(refactored_target_entities.keys()))
        # if i:
        #     mydataentities += [jj for jj in refactored_target_entities[i[0]]]
        # mydataentities = []
        # for t in refactor_target_entities.keys():
        #     for j in refactor_target_entities[t]:
        mydataentities = []        
        if sentence:
            # print('sentence:', sentence)
            # print('comparable_span:', comparable_span)
            head = getNPhead(sentence, comparable_span).lower()
            # print('head:', head)
            entity_lemma = token_lemmatize(head)
            doc_comparable_span = spacyObject(comparable_span)
            entity_lemmas = []
            if [x for x in doc_comparable_span if x.dep_ == 'cc']:
                entity_lemmas = [chunk.text for chunk in doc_comparable_span.noun_chunks]                

            for t in refactored_target_entities.keys():
                # if len(t.split(' ')) == 1:
                for j in refactored_target_entities[t]:
                    if j == entity_lemma or t == entity_lemma or entity_lemma in t or entity_lemma in j:
                        mydataentities += [j]
                    elif j == head or t == head or head in t or head in j:
                        mydataentities += [j]
                    elif entity_lemmas:
                        for el in entity_lemmas:
                            if j == el or t == el or head in el or t in el:
                                mydataentities += [j]
                    elif j == comparable_span or t == comparable_span:
                        mydataentities += [j]
        if not mydataentities and sentence:
            # mydataentities = list(set([j for t in refactored_target_entities.keys() for j in refactored_target_entities[t] if overlap(comparable_span, t) or overlap(comparable_span.lower(), t.lower())]))
            mydataentities = list(set([j for t in refactored_target_entities.keys() for j in refactored_target_entities[t] if ';' in t and overlap(head.lower(), t.lower())]))
            # mydataentities = list(set([j for t in refactored_target_entities.keys() for j in refactored_target_entities[t] if overlap(t, comparable_span) or overlap(t.lower(), comparable_span.lower())]))
    else:
        # method 2
        mydataentities_scored = []
        for t in refactored_target_entities.keys():
            for j in refactored_target_entities[t]:
                mydataentities_scored += [(j, lev.distance(comparable_span, t))]
        mydataentities_scored_sorted = sorted(mydataentities_scored, key=lambda x:x[1])
        mydataentities = [mydataentities_scored_sorted[0][0]]            
    # print(f'from comparable span {comparable_span} I found {mydataentities}')
    return list(set(mydataentities))

def findTargetEntity(target_entities, args_vn, args_pb, vn_role, pb_role, split, pid, sid, sentence):
    raw_themes, data_themes = [], []
    updated_vn = False
    refactored_target_entities = refactor_target_entities(target_entities)
    # print('refactored_target_entities:', refactored_target_entities)
    if vn_role in args_vn and args_vn[vn_role]:
        raw_themes = [args_vn[vn_role]]
        # print('raw_themes:', raw_themes)
        data_themes = findDataEntities(refactored_target_entities, args_vn[vn_role], target_entities, sentence)
        if data_themes:
            updated_vn = True
            # print('found from findDataEntities()')

        # ablation: no coref > comment out
        # if not updated_vn:
        #     corefs = checkCoreference(split=split, paragraph_id=pid, span=args_vn[vn_role], sentence_id=sid)
        #     if corefs:
        #         data_themes = corefs
        #         updated_vn = True
                # print('found from corefs')

    if not updated_vn and pb_role:
        target_pb_label = [x for x in args_pb.keys() if pb_role in x]
        if target_pb_label:            
            target_pb_label = target_pb_label[0]
            if args_pb[target_pb_label]:
                if not raw_themes:
                    raw_themes = [args_pb[target_pb_label]]
                data_themes = findDataEntities(refactored_target_entities, args_pb[target_pb_label], target_entities, sentence)               
                # print('found from pb findDataEntities()')

                # ablation: no coref > comment out
                # if not data_themes:
                #     corefs = checkCoreference(split=split, paragraph_id=pid, span=args_pb[target_pb_label], sentence_id=sid)
                #     if corefs:
                #         data_themes = corefs 

                        # print('found from pb corefs')
    # print('raw_themes: {}, data_themes: {}'.format(raw_themes, data_themes))
    if raw_themes and not data_themes:
        # print('now attempting roots and their synonyms')
        for rt in raw_themes:            
            rt_root = findRoot(rt)
            # check synonyms
            for t in target_entities:
                ts = findSynonyms(t)
                # print('Synonyms for {}: {}'.format(t, ts))
                if ts:
                    if rt in ts:
                        data_themes += [t] 
                        # print('Found theme "{}" in synonyms of "{}"'.format(rt, t))
                    elif rt_root and rt_root in ts:
                        data_themes += [t] 
                        # print('Found theme "{}" in synonyms of "{}"'.format(rt, t))
    # if raw_themes and not data_themes:
    #     print(f'did not find data themes from {raw_themes}')
    # print('data_entities:', data_themes)
    return data_themes, raw_themes

def findLocation(args_vn, args_pb, vn_role, pb_role, sentence):
    raw_locations = []
    updated_vn = False
    args_vn = {re.sub(' ', '_', k): v for k, v in args_vn.items()}
    if vn_role in args_vn and args_vn[vn_role]:
        x = getNPhead(sentence, args_vn[vn_role])
        if x:
            raw_locations += [x]
            updated_vn = True
        # if not updated_vn:
        #     j = findSubsumedNP_as_Loc(theme, args_vn, vn_role, sentence)
        #     if j:
        #         raw_locations += j
        #         updated_vn = True
    if not updated_vn and pb_role:
        target_pb_label = [x for x in args_pb.keys() if pb_role in x]
        if target_pb_label:
            target_pb_label = target_pb_label[0]
            if args_pb[target_pb_label]:
                x = getNPhead(sentence, args_pb[target_pb_label])
                if x:
                    raw_locations += [x]
    return raw_locations

def findSubsumedNP_as_Loc(theme, args_vn, vn_role, sentence):
    if theme and type(theme) == list:
        theme = theme[0]
    loc = []
    args_vn = {re.sub(' ', '_', k): v for k, v in args_vn.items()}
    y = getNPPobj(nlp(sentence), args_vn[vn_role])
    if y:
        y_selected = [j for j in y if overlap(j[0], theme) or overlap(theme, j[0])]
        if y_selected:
            for j in y_selected:
                loc += [j[1]]
    return loc   

def findRawLocation(args_vn, args_pb, vn_role, pb_role, sentence):
    raw_locations = []
    updated_vn = False
    args_vn = {re.sub(' ', '_', k): v for k, v in args_vn.items()}
    if vn_role in args_vn and args_vn[vn_role]:
        # x = getNPhead(sentence, args_vn[vn_role])
        # if args_vn[vn_role]:
        raw_locations += [args_vn[vn_role]]
        updated_vn = True        
    if not updated_vn and pb_role:
        target_pb_label = [x for x in args_pb.keys() if pb_role in x]
        if target_pb_label:
            target_pb_label = target_pb_label[0]
            if args_pb[target_pb_label]:                
                raw_locations += [args_pb[target_pb_label]]
    return raw_locations


def str2dict(mystr):
    import json, re
    x = re.sub(r"'", '"', mystr)
    x = re.sub(r';', ',', x)
    x_dict = json.loads(x)
    return x_dict


def pb2vnmap(verb, vnclass, pbrole):
    semlink_ibm = '/data/ghazaleh/datasets/semlink/TEMP_Propbank_To_Verbnet_edit.tsv'
    semlink = pd.read_csv(semlink_ibm, sep='\t', header=None)
    res = []
    for i in range(semlink.shape[0]):
        if semlink[1].iloc[i].startswith(verb.lower()):
            if semlink[3].iloc[i] == vnclass:
                # pbrole should start with ARG
                if not pbrole.startswith('ARG'):
                    if pbrole.startswith('A'):
                        pbrole = 'ARG' + pbrole[1:]
                mymap = str2dict(semlink[4].iloc[i])
                return mymap[pbrole]['vnArg'].lower()  


def findEntityPB(args_pb, pbrole, vnclass, desiredvnrole):
    verb = args_pb['V <-> Verb']
    verb = token_lemmatize(verb)
    vnrolemap = pb2vnmap(verb, vnclass, pbrole)
    if vnrolemap and desiredvnrole.lower() == vnrolemap.lower():
        return True
    else:
        return False

def findCreatedEntity(target_entities, args_pb, args_vn, pb_role, vn_role, vn_source_role, pb_source_role, split, pid, sid, sentence, verbose=False):
    raw_created, data_created, raw_source = [], [], []
    refactored_target_entities = refactor_target_entities(target_entities)
    if vn_role and vn_role in args_vn and args_vn[vn_role]:     
        created_entities = findDataEntities(refactored_target_entities, args_vn[vn_role], target_entities, sentence)
        # print('created_entities:', created_entities)
        if created_entities:
            raw_created += [args_vn[vn_role]]
            
            data_created += created_entities
            if vn_source_role and vn_source_role in args_vn and args_vn[vn_source_role]:
                raw_source += [args_vn[vn_source_role]]
    elif pb_role:
        pb_role_target = [j for j in args_pb.keys() if j.startswith(pb_role)]
        if pb_role_target and args_pb[pb_role_target[0]]:
            created_entities = findDataEntities(refactored_target_entities, args_pb[pb_role_target[0]], target_entities, sentence)
            # print('created_entities:', created_entities)
            if created_entities and args_pb:
                raw_created += [args_pb[pb_role_target[0]]]
                data_created += created_entities
                if pb_source_role:              
                    pb_source_role_target = [r for r in args_pb.keys() if pb_source_role in r]
                    if pb_source_role_target and args_pb[pb_source_role_target[0]]:
                        raw_source += [args_pb[pb_source_role_target[0]]]
    # if not data_created and findEntityPB(args_pb, pb_role, None, vn_role):
    #     created_entities = findDataEntities(refactored_target_entities, )
        
    # if verbose:
    #     print('raw_created: {}, data_created: {}'.format(raw_created, data_created))
    return raw_created, data_created, raw_source

def findDestroyedEntity(target_entities, args_pb, args_vn, pb_role, vn_role, split, pid, sid, sentence, verbose=False):
    raw_destroyed, data_destroyed = [], []
    refactored_target_entities = refactor_target_entities(target_entities)

    if vn_role and vn_role in args_vn and args_vn[vn_role]:
        raw_destroyed += [args_vn[vn_role]]
        destroyed_entities = findDataEntities(refactored_target_entities, args_vn[vn_role], target_entities, sentence)
        
        if destroyed_entities:            
            data_destroyed += destroyed_entities
    elif pb_role:
        pb_role_target = [j for j in args_pb.keys() if j.startswith(pb_role)]
        if pb_role_target and args_pb[pb_role_target[0]]:
            raw_destroyed += [args_pb[pb_role_target[0]]]
            destroyed_entities = findDataEntities(refactored_target_entities, args_pb[pb_role_target[0]], target_entities, sentence)        
            if destroyed_entities:                
                data_destroyed += destroyed_entities
    return raw_destroyed, data_destroyed

def ablative_allative(trajectory, clause):
    # source
    ablative_prepositions = ['away', 'from', 'out', 'off']
    # destination
    allative_prepositions = ['into', 'onto', 'towards', 'toward', 'down', 'up', 'back', 'to', 'through']
    source, destination = [], []
    for tj in trajectory:
        if True in [tj.startswith(ab+' ') for ab in ablative_prepositions]:
            tj = getNPhead(clause, tj) # getPPnominalHead
            source += [tj]
        elif True in [tj.startswith(al+' ') for al in allative_prepositions]:
            tj = getNPhead(clause, tj) # getPPnominalHead
            destination += [tj]        
    return source, destination

def checkSubjectAbsence(sentence):
    # purpose: check if a sentence does not have subject (i.e. if subject is dropped!)
    doc = spacyObject(sentence)
    subject_is_absent = False
    if [t for t in doc if 'subj' in t.dep_] == []:
        subject_is_absent = True
    return subject_is_absent

def fixSubjectAbsence(sentence, last_sentence):
    """
    purpose: if a sentence does not have subject (i.e. if subject is dropped!), 
    insert the subject of the last sentence and parse the sentence again.
    """
    subject = get_subject_phrase(last_sentence)
    if subject:
        return subject.text + ' ' + sentence[0].lower() + sentence[1:]
    return sentence    

# def locationTrasitivity(all_entities_locations, ent1, ent2, ent3, step_number):
#     """
#     if ent1 in ent2 in step x and ent2 in ent3 in step x:
#         ent1 in ent3 in step x (update all_entities_locations)
#     """
#     return 

# def findAllEntitiesLocations(args_vn, args_pb, events):
#     """
#     find locations of all participants regardless of whether they are among target entities,
#     as they are explicitly mentioned in each step (derive from vn and pb parse).
#     map each entity to a list of a location in each step. 
#     location persists if not explicitly changed.
#     """
#     _, _, args, polarpreds, pred_triples_abstract, pb_pred_triples_abstract, pred_tuple_abstract, pb_pred_tuples_abstract, vn_tuples_abstract_general, pb_tuples_abstract_general = predlist_polarity_args(events, args_pb)
#     location_vn_args = ['destination', 'location', 'goal', 'trajectory', 'recipient']
#     participants = ['agent', 'patient', 'theme', 'co-agent', 'pivot', 'instrument', 'co-patient']
    
#     contain = [x for x in vn_tuples_abstract_general if x == ('contain', 'pivot', 'theme')]
#     take_in_1 = [x for x in vn_tuples_abstract_general if x == ('take_in', 'goal', 'theme')]
#     take_in_2 = [x for x in vn_tuples_abstract_general if x == ('take_in', 'agent', 'patient')] 
#     take_in_3 = [x for x in vn_tuples_abstract_general if x == ('take_in', 'recipient', 'theme')]
#     # emit = [x for x in vn_tuples_abstract_general if x == ('emit', 'agent', 'theme')]
#     appear = [x for x in vn_tuples_abstract_general if x == ('appear', 'theme') or x == ('has_location', 'theme', 'location')]
#     # motion_source = [x for x in vn_tuples_abstract_general if x == ('has_location', 'theme', 'source') or x == ('motion', 'theme')]
#     body_motion = [x for x in vn_tuples_abstract_general if x == ('body_motion', 'agent') or x == ('has_location', 'agent', 'location')]
    
#     # trajectory_source = [x for x in vn_tuples_abstract_general if x == ('motion', 'theme', 'trajectory') or x == ('motion', 'theme', 'verbspecific') or x == ('!has_location', 'theme', 'source') or x == ('!has_location', 'theme', 'initial_location')]
#     # trajectory_source_agent = [x for x in vn_tuples_abstract_general if x == ('motion', 'agent', 'trajectory') or x == ('motion', 'agent', 'verbspecific') or x == ('!has_location', 'agent', 'source') or x == ('!has_location', 'agent', 'initial_location')]

#     trajectory_destination = [x for x in vn_tuples_abstract_general if x == ('motion', 'theme', 'trajectory') or x == ('motion', 'theme', 'verbspecific') or x == ('has_location', 'theme', 'destination') or x == ('has_location', 'theme', 'goal')]
#     trajectory_destination_agent = [x for x in vn_tuples_abstract_general if x == ('motion', 'agent', 'trajectory') or x == ('motion', 'agent', 'verbspecific') or x == ('has_location', 'agent', 'destination') or x == ('has_location', 'agent', 'goal')] 

#     filled = [x for x in vn_tuples_abstract_general if x == ('filled_with', 'location', 'theme')]
#     general_location = [x for x in vn_tuples_abstract_general if x == ('has_location', 'theme', 'location')]
#     general_location_2 = [x for x in vn_tuples_abstract_general if x == ('has_location', 'theme', 'goal')]
#     general_location_3 = [x for x in vn_tuples_abstract_general if x == ('has_location', 'theme', 'destination')]
#     penetration = [x for x in vn_tuples_abstract_general if x == ('penetrating', 'instrument', 'patient')]
#     seem = [x for x in vn_tuples_abstract_general if x == ('seem', 'theme', 'attribute')]
#     disappear = [x for x in vn_tuples_abstract_general if x == ('disappear', 'theme')]
#     trajectory_only = [x for x in vn_tuples_abstract_general if x == ('motion', 'theme', 'trajectory')]



#     return      



if __name__ == '__main__':    
    # print(lev.distance("water's energy", 'the waters energy'))
    # print(lev.distance("water's energy", 'water'))
    # target_entities = ['magma', 'rock', 'sedimentary rock', 'third kind of rock']
    # refactored_target_entities = refactor_target_entities(target_entities)
    # comparable_span = 'a sedimentary rock'
    # print(findDataEntities(refactored_target_entities, comparable_span, target_entities))
    # args_vn = {'patient': 'the microbes that may proliferate in the food', 'agent': ''}

    # print(substantiateVNargs(args_vn, args_pb, vn_sense, spans))
    print()
    from util import dataPrepare
    split = 'dev'
    states = dict()
    split_data = dataPrepare(split)
    split_data_parsed, split_data_raw, split_data_participants = split_data.parseddata, split_data.rawdata, split_data.participants
    for pid in split_data_participants.keys():
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
            sentence_parse = parsed_paragraph[sid]
            for event_id in range(len(sentence_parse['props'])):
                current_event = sentence_parse['props'][event_id]
                current_sense, events, spans = current_event['sense'], current_event['events'], current_event['spans']
                print(createArgsDicts(events, spans, current_sense, sentence))
        break
    print()