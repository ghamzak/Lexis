from from_spacy import *
from vnpreds import overlap


def utility_for_transitive_location_function(target_entities, current_l2):
    # returns the single target entity that overlaps with current_l2
    answer = None
    if current_l2 in target_entities:
        answer = current_l2
    elif current_l2.lower() in target_entities:
        answer = current_l2.lower()
    elif token_lemmatize(current_l2) in target_entities:
        answer = token_lemmatize(current_l2)
    elif token_lemmatize(current_l2) in [token_lemmatize(x) for x in target_entities]:
        for x in target_entities:
            if token_lemmatize(current_l2) == token_lemmatize(x):
                answer = x
                break
    elif [e for e in target_entities if overlap(current_l2, e)]:
        answer = [e for e in target_entities if overlap(current_l2, e)][0]
    elif [e for e in target_entities if overlap(e, current_l2)]:
        answer = [e for e in target_entities if overlap(e, current_l2)][0]
    return answer

def persistence_function(states, pid, ent, sid):
    # print('using persistence_function')
    change_to_loc = states[pid][ent][sid]['s2']
    sentence_count = list(states[pid][ent].keys())[-1]
    if sid+1 <= sentence_count:
        states[pid][ent][sid+1]['s1'] = change_to_loc
        i = sid + 1
        for i in range(sid+2, sentence_count+1):
            if states[pid][ent][i]['cos_type'] != 'NONE':
                break
            states[pid][ent][i-1]['s2'] = states[pid][ent][i]['s1'] = change_to_loc
        if i == sentence_count and states[pid][ent][i]['cos_type'] == 'NONE':
            states[pid][ent][i]['s2'] = change_to_loc
    return states    

def transitive_location_update(states, pid): # , sid, ent, loc
    test_ent = list(states[pid].keys())[0]
    sentence_count = len(states[pid][test_ent])
    de = list(states[pid].keys())
    new_destination = None
    """
    we actually need a dict to keep all entities locations in each step, not just data entities.
    but let's keep that for later. for now, we focus on when a location is among data entities.
    """
    for ent in states[pid].keys():
        for sid in states[pid][ent].keys():
            current_l2 = states[pid][ent][sid]['s2']
            answer = utility_for_transitive_location_function(de, current_l2)
            if answer and states[pid][answer][sid]['s2'] not in ['?', '-']:
                new_destination = states[pid][answer][sid]['s2']
                states[pid][ent][sid]['s2'] = new_destination
                if states[pid][ent][sid]['cos_type'] == 'NONE' and states[pid][ent][sid]['s2'] != states[pid][ent][sid]['s1']:
                    states[pid][ent][sid]['cos_type'] = 'MOVE'
                states = persistence_function(states, pid, ent, sid)

    return states

def finalConsistencyCheck(states):
    for pid in states.keys():
        for ent in states[pid].keys():
            sentence_count = list(states[pid][ent].keys())[-1]
            for sid in states[pid][ent].keys():

                # if states[pid][ent][sid]['s1'] == '-' and states[pid][ent][sid]['s2'] != '-':
                #     states[pid][ent][sid]['cos_type'] == 'CREATE'
                
                # if ent has any cos, it can't be created later
                # if sid > 1 and states[pid][ent][sid]['cos_type'] == 'CREATE':
                #     if set([states[pid][ent][i]['cos_type'] for i in range(1,sid)]) != set(['NONE']):
                #         states[pid][ent][sid]['cos_type'] = 'NONE'

                # this removes any earlier cos and location info if an entity is created in a certain step
                # we need to compare it with the situation if instead of converting all prior info to NONE,
                # we just ignore the "CREATE" cos.
                if sid > 1 and states[pid][ent][sid]['cos_type'] == 'CREATE':
                    for i in range(1,sid):
                        states[pid][ent][i]['cos_type'] = 'NONE'
                        states[pid][ent][i]['s1'] = '-'
                        states[pid][ent][i]['s2'] = '-'
                    states[pid][ent][sid]['s1'] = '-'
                    
                
                
                if states[pid][ent][sid]['s1'] != states[pid][ent][sid]['s2'] and states[pid][ent][sid]['cos_type'] == 'NONE' and states[pid][ent][sid]['s1'] != '-' and states[pid][ent][sid]['s2'] != '-':                    
                    states[pid][ent][sid]['cos_type'] = 'MOVE'
                    # states[pid][ent][sid]['s2'] = states[pid][ent][sid]['s1']                
               
                if states[pid][ent][sid]['cos_type'] == 'MOVE':
                    if 'DESTROY' in set([states[pid][ent][i]['cos_type'] for i in range(1,sid)]):
                        states[pid][ent][sid]['cos_type'] == 'NONE'
                    elif states[pid][ent][sid]['s1'] == '-':
                        states[pid][ent][sid]['s1'] = '?'
                    elif states[pid][ent][sid]['s1'] == states[pid][ent][sid]['s2']:                        
                        states[pid][ent][sid]['s1'] = 'location'

                # if states[pid][ent][sid]['s1'] == states[pid][ent][sid]['s2'] and states[pid][ent][sid]['cos_type'] == 'MOVE' and states[pid][ent][sid]['s2'] != '?':
                #     states[pid][ent][sid]['s1'] = '?'


                

                if states[pid][ent][sid]['cos_type'] == 'DESTROY':
                    states[pid][ent][sid]['s2'] = '-'
                    if sid != sentence_count:
                        for i in range(sid+1, sentence_count+1):
                            if states[pid][ent][i]['cos_type'] == 'CREATE':
                                break
                            else:
                                states[pid][ent][i]['cos_type'] = 'NONE'
                                states[pid][ent][i]['s1'] = states[pid][ent][i]['s2'] = '-'
                # an entity cannot be created twice. keep only the latest create event
                if sid > 1 and states[pid][ent][sid]['cos_type'] == 'CREATE':
                    for i in range(sid-1, 0, -1):
                        if states[pid][ent][i]['cos_type'] == 'CREATE':
                            states[pid][ent][i]['cos_type'] = 'NONE'  
                        
                # if sid > 1 and states[pid][ent][sid]['s1'] != states[pid][ent][sid-1]['s2']:
                #     states[pid][ent][sid-1]['s2'] = states[pid][ent][sid]['s1']                  
                    
    return states    