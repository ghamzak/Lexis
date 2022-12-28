from util2 import *
from from_spacy import *
from CN import isLocative

def move(events, theme, args_vn, args_pb, states, pid, sid, sentence, vn_sense, ss=[], dd=[], persists=True, raw_paragraph=None, verbose=False):
    if verbose:
        if ss and dd:
            print('trying to move', theme, ' from ', ss, ' to ', dd)
        elif ss and not dd:
            print('trying to move', theme, ' from ', ss)
        elif dd and not ss:
            print('trying to move', theme, ' to ', dd)
    updated=False
    source_updated, destination_updated = False, False
    source = ss
    destination = dd
    persists = True

    # if sid > 1:
    #     for t in theme:
    #         if states[pid][t][sid-1]['s2'] not in ['?', '-']:
    #             states[pid][t][sid]['s1'] = states[pid][t][sid-1]['s2']

    if source:
        source = source[0]
        head = getNPhead(sentence, source)
        for t in theme:
            if verbose:
                print('theme {} is now in {} and we are changing source to {}'.format(t, states[pid][t][sid]['s1'], head.lower()))
            sentence_count = list(states[pid][t].keys())[-1]
            if states[pid][t][sid]['s1'] != '-':
                if t in sentence and head and head.lower() != getNPhead(sentence, t):
                    states[pid][t][sid]['cos_type'] = 'MOVE'
                    states[pid][t][sid]['s1'] = head.lower()
                    source_updated = True
                elif head and head.lower() != t.lower():
                    states[pid][t][sid]['cos_type'] = 'MOVE'
                    states[pid][t][sid]['s1'] = head.lower()
                    source_updated = True
                elif source != t:
                    states[pid][t][sid]['cos_type'] = 'MOVE'
                    states[pid][t][sid]['s1'] = source
                    source_updated = True
            # using commonsense to find initial location
            # if not source_updated and raw_paragraph and states[pid][t][sid]['s1'] == '?':
            #     src = commonsense_location(tokenize(raw_paragraph), t)
            #     if src:                    
            #         src = src[0]
            #         states[pid][t][sid]['cos_type'] = 'MOVE'
            #         states[pid][t][sid]['s1'] = src
            #         source_updated = True
            #         print('Actually updated using commonsense')
            if verbose:
                print('theme {} is now in {} source'.format(t, states[pid][t][sid]['s1']))
        
    if destination:
        destination = destination[-1]
        head = getNPhead(sentence, destination)

        if verbose:
            print('real destination:', destination)
            print('head of destination:', head)
        for t in theme:
            sentence_count = list(states[pid][t].keys())[-1]
            if verbose:
                print(t, states[pid][t][sid])
            src = ''
            if states[pid][t][sid]['s1'] != '-':
                if states[pid][t][sid]['cos_type'] == 'CREATE':
                    # this captures when we have several events in one sentence and create is followed by motion. 
                    # we get the creation location as initial location of motion event
                    src = states[pid][t][sid]['s2']
                if t in sentence:
                    if head and head.lower() != getNPhead(sentence, t):
                        states[pid][t][sid]['cos_type'] = 'MOVE'
                        states[pid][t][sid]['s2'] = head.lower()
                        destination_updated = True
                elif head and head.lower() != t:
                    states[pid][t][sid]['cos_type'] = 'MOVE'
                    states[pid][t][sid]['s2'] = head.lower()
                    # if src: # and not source_updated
                    #     states[pid][t][sid]['s1'] = src    
                    #     source_updated = True
                    destination_updated = True                    
                elif destination != t: # else
                    states[pid][t][sid]['cos_type'] = 'MOVE'
                    states[pid][t][sid]['s2'] = destination                      
                    destination_updated = True
                if src: # and not source_updated
                    states[pid][t][sid]['s1'] = src 
                    source_updated = True 
            elif states[pid][t][sid]['cos_type'] == 'CREATE':
                src = states[pid][t][sid]['s2']
                if verbose:
                    print('src:', src)
                if head and head.lower() != t:
                    states[pid][t][sid]['cos_type'] = 'MOVE'
                    states[pid][t][sid]['s2'] = head
                    # if src and src not in ['?', '-']: # and not source_updated
                    #     states[pid][t][sid]['s1'] = src                    
                    #     source_updated = True
                    destination_updated = True
                elif destination != t:
                    states[pid][t][sid]['cos_type'] = 'MOVE'
                    states[pid][t][sid]['s2'] = destination                    
                    destination_updated = True 
                if src and src not in ['?', '-']: #  and not source_updated
                    states[pid][t][sid]['s1'] = src
                    source_updated = True
            if verbose:
                print(t, states[pid][t][sid])
                    
            
    if not source_updated and not destination_updated:        
        pass
    else:
        if verbose:
            print('persists: {}, source_updated: {}, destination_updated: {}'.format(persists, source_updated, destination_updated))
        # persistence rule: remains there until otherwise specified
        if persists:        
            for t in theme:
                if verbose:
                    print('before persisting:', states[pid][t])
                # if states[pid][t][sid]['s1'] != '-':
                if source_updated and not destination_updated: 
                    s = '?' #states[pid][t][sid]['s1']
                    states[pid][t][sid]['s2'] = s
                    if sid+1 <= sentence_count:
                        for i in range(sid+1, sentence_count+1):
                            states[pid][t][i]['s1'] = s
                            states[pid][t][i]['s2'] = s
                elif destination_updated and sid+1 <= sentence_count:
                    d = states[pid][t][sid]['s2']
                    for i in range(sid+1, sentence_count+1):
                        states[pid][t][i]['s1'] = d
                        states[pid][t][i]['s2'] = d
                if verbose:
                    print('after persisting:', states[pid][t])
            
    return states



def updateMotion(target_entities, events, spans, states, pid, sid, sentence, split, vn_sense, destroy_update, raw_paragraph, verbose=False):
    if destroy_update:
        return states
    args_vn, args_pb = createArgsDicts(events, spans, vn_sense, sentence)
    if args_pb and 'V <-> Verb' in args_pb.keys():
        focus_verb = args_pb['V <-> Verb']
        focus_verb = token_lemmatize(focus_verb)
    if verbose:
        print('args_vn:',args_vn)
        print('args_pb:',args_pb)
    _, _, args, polarpreds, pred_triples_abstract, pb_pred_triples_abstract, pred_tuple_abstract, pb_pred_tuples_abstract, vn_tuples_abstract_general, pb_tuples_abstract_general = predlist_polarity_args(events, args_pb)    
    if verbose:
        print('updateMotion')
        print('vn_tuples_abstract_general:',vn_tuples_abstract_general)
        print('pb_tuples_abstract_general:',pb_tuples_abstract_general)
        if not vn_tuples_abstract_general:
            print(events)
    updated_themes_for_event = []
    move_update = False
    persists = True
    source, destination = [], []
    agent_source, agent_destination = None, None
    theme, agent_theme = [], []

    with open('/data/ghazaleh/datasets/verb_vsf2.pickle', 'rb') as rf:
            vsf_dict_verb = pickle.load(rf)        
    with open('/data/ghazaleh/datasets/bso_direct_vsf_propara2.pickle', 'rb') as rf:
        bso_vsf_verbs = pickle.load(rf)

    propara_vsf_map = {'destroy': ['end_state: destroyed', 'result: +destroy', 'v_final_state: broken', 'v_final_state: destroyed', 'v_final_state: disintegrated'],
                'create': ['result: +create', 'v_final_state: created'], 
                'move': ['activity: remove', 'activity: free', 'activity_type: hike', 'activity_type: sport', 'activity_type: travel', 'activity_type: walk', 'direction_of_motion: x', 'manner_of_motion: x', 'motion_path: x', 'motion_medium: x', 'property_changed: location', 'result: +join', 'result: -join', 'result: free', 'vehicle_type: x']}

    # start here

    if vn_tuples_abstract_general:
        contain = [x for x in vn_tuples_abstract_general if x == ('contain', 'pivot', 'theme')]
        take_in_1 = [x for x in vn_tuples_abstract_general if x == ('take_in', 'goal', 'theme')]
        take_in_2 = [x for x in vn_tuples_abstract_general if x == ('take_in', 'agent', 'patient')] 
        take_in_3 = [x for x in vn_tuples_abstract_general if x == ('take_in', 'recipient', 'theme')]
        emit = [x for x in vn_tuples_abstract_general if x == ('emit', 'agent', 'theme')]
        appear = [x for x in vn_tuples_abstract_general if x == ('appear', 'theme') or x == ('has_location', 'theme', 'location')]
        motion_source = [x for x in vn_tuples_abstract_general if x == ('has_location', 'theme', 'source') or x == ('motion', 'theme')]
        body_motion = [x for x in vn_tuples_abstract_general if x == ('body_motion', 'agent') or x == ('has_location', 'agent', 'location')]
        
        trajectory_source = [x for x in vn_tuples_abstract_general if x == ('motion', 'theme', 'trajectory') or x == ('motion', 'theme', 'verbspecific') or x == ('!has_location', 'theme', 'source') or x == ('!has_location', 'theme', 'initial_location')]
        trajectory_source_agent = [x for x in vn_tuples_abstract_general if x == ('motion', 'agent', 'trajectory') or x == ('motion', 'agent', 'verbspecific') or x == ('!has_location', 'agent', 'source') or x == ('!has_location', 'agent', 'initial_location')]

        trajectory_destination = [x for x in vn_tuples_abstract_general if x == ('motion', 'theme', 'trajectory') or x == ('motion', 'theme', 'verbspecific') or x == ('has_location', 'theme', 'destination') or x == ('has_location', 'theme', 'goal')]
        trajectory_destination_agent = [x for x in vn_tuples_abstract_general if x == ('motion', 'agent', 'trajectory') or x == ('motion', 'agent', 'verbspecific') or x == ('has_location', 'agent', 'destination') or x == ('has_location', 'agent', 'goal')] 

        filled = [x for x in vn_tuples_abstract_general if x == ('filled_with', 'location', 'theme')]
        general_location = [x for x in vn_tuples_abstract_general if x == ('has_location', 'theme', 'location')]
        general_location_2 = [x for x in vn_tuples_abstract_general if x == ('has_location', 'theme', 'goal')]
        general_location_3 = [x for x in vn_tuples_abstract_general if x == ('has_location', 'theme', 'destination')]
        penetration = [x for x in vn_tuples_abstract_general if x == ('penetrating', 'instrument', 'patient')]
        # seem = [x for x in vn_tuples_abstract_general if x == ('seem', 'theme', 'attribute')]
        disappear = [x for x in vn_tuples_abstract_general if x == ('disappear', 'theme')]
        trajectory_only = [x for x in vn_tuples_abstract_general if x == ('motion', 'theme', 'trajectory')]
        vsf_goal = [x for x in vn_tuples_abstract_general if x == ('motion', 'theme', 'verbspecific') or x == ('has_location', 'theme', 'goal')]
        has_location_singleton = [x for x in vn_tuples_abstract_general if x[0] == 'has_location']
        if len(has_location_singleton) > 1:
            has_location_singleton = []
        together = [x for x in vn_tuples_abstract_general if x[0] == 'together' or x[0] == '!together']
        # free = [x for x in vn_tuples_abstract_general if x[0] == 'free' or x[0] == '!free']
        attached = [x for x in vn_tuples_abstract_general if x[0] == 'attached' or x[0] == '!attached']
        
        if attached and len(attached) == 2 and len(attached[0]) == 3 and attached[0][0] == 'attached' and attached[1][0] == '!attached':
            if verbose:
                print('attached sempred')
            t, d = attached[0][1], attached[0][2]
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, t, 'A1', split, pid, sid, sentence)
            if theme and not destination:
                destination = findLocation(args_vn, args_pb, d, None, sentence)
                if not destination:
                    destination = findSubsumedNP_as_Loc(theme, args_vn, t, sentence)            
                
        if together and len(together) == 2 and len(together[0]) == 3 and together[0][0] == '!together' and together[1][0] == 'together':
            if verbose:
                print('together sempred')
            t, d = together[0][1], together[0][2]
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, t, 'A1', split, pid, sid, sentence)
            if theme and not destination:
                destination = findLocation(args_vn, args_pb, d, None, sentence)
                if not destination:
                    destination = findSubsumedNP_as_Loc(theme, args_vn, t, sentence)
                    
        if len(has_location_singleton) == 1 and len(has_location_singleton[0]) == 3:
            if verbose:
                print('has_location_singleton')
            t, d = has_location_singleton[0][1], has_location_singleton[0][2]
            # if we start using SemLink, we can give a more accurate pb role for finding theme and location
            # but let's keep that for later maybe
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, t, 'A1', split, pid, sid, sentence)
            if theme and not destination:
                destination = list(set(findLocation(args_vn, args_pb, d, 'AM-GOL', sentence)).union(set(findLocation(args_vn, args_pb, d, 'AM-LOC', sentence)))) # .union(set(findLocation(args_vn, args_pb, d, 'A2', sentence)))
                if not destination:
                    destination = findSubsumedNP_as_Loc(theme, args_vn, t, sentence)

                
        if vsf_goal and vsf_goal[0] == ('motion', 'theme', 'verbspecific'):
            if verbose:
                print('vsf_goal')
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', None, split, pid, sid, sentence)
            if verbose:
                print('theme:', theme)
                print('target_entities:',target_entities)
            if theme:
                if not destination:
                    destination = list(set(findLocation(args_vn, args_pb, 'destination', 'AM-GOL', sentence)).union(set(findLocation(args_vn, args_pb, 'destination', 'AM-LOC', sentence))).union(set(findLocation(args_vn, args_pb, 'goal', None, sentence))))
                    if not destination:
                        destination = findSubsumedNP_as_Loc(theme, args_vn, 'theme', sentence)
                if verbose:
                    print('destination:', destination)
                
        
        if trajectory_source and trajectory_destination:
            if verbose:
                print('it is both trajectory source and destination ')
            if (tuple(trajectory_source) == (('motion', 'theme', 'trajectory'), ('!has_location', 'theme', 'initial_location')) and tuple(trajectory_destination) == (('motion', 'theme', 'trajectory'), ('has_location', 'theme', 'destination'))) or (tuple(trajectory_source) == (('motion', 'theme', 'trajectory'), ('!has_location', 'theme', 'initial_location')) and tuple(trajectory_destination) == (('motion', 'theme', 'trajectory'), ('has_location', 'theme', 'goal'))) or (tuple(trajectory_source) == (('motion', 'theme', 'trajectory'), ('!has_location', 'theme', 'source')) and tuple(trajectory_destination) == (('motion', 'theme', 'trajectory'), ('has_location', 'theme', 'destination'))) or (tuple(trajectory_source) == (('motion', 'theme', 'trajectory'), ('!has_location', 'theme', 'source')) and tuple(trajectory_destination) == (('motion', 'theme', 'trajectory'), ('has_location', 'theme', 'goal'))) or (tuple(trajectory_source) == (('motion', 'theme', 'verbspecific'), ('!has_location', 'theme', 'initial_location')) and tuple(trajectory_destination) == (('motion', 'theme', 'verbspecific'), ('has_location', 'theme', 'destination'))):                
                theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
                if verbose:
                    print('theme:', theme)
                    print('target_entities:',target_entities)
                if theme:
                    if not source:
                        source = list(set(findLocation(args_vn, args_pb, 'source', None, sentence)).union(set(findLocation(args_vn, args_pb, 'initial_location', None, sentence))))
                        if not source:
                            source = findLocation(args_vn, args_pb, 'agent', 'A0', sentence)
                        if verbose:
                            print('source:', source)
                    if not destination:
                        destination = list(set(findLocation(args_vn, args_pb, 'destination', 'AM-GOL', sentence)).union(set(findLocation(args_vn, args_pb, 'goal', 'AM-LOC', sentence))))
                        if not destination:
                            destination = findSubsumedNP_as_Loc(theme, args_vn, 'theme', sentence)
                        if verbose:
                            print('destination:', destination)
                    if source and not destination:
                        persists = False
        
        if not source and trajectory_source and not trajectory_destination: 
            if verbose:
                print('trajectory_source')
            if tuple(trajectory_source) == (('motion', 'theme', 'trajectory'), ('!has_location', 'theme', 'initial_location')):
                theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
                if theme:
                    source = list(set(findLocation(args_vn, args_pb, 'source', 'A2', sentence)).union(set(findLocation(args_vn, args_pb, 'initial_location', 'A2', sentence))))
                    persists = False
            elif disappear:
                theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
                if theme:
                    if not source:
                        source = findLocation(args_vn, args_pb, 'initial_location', None, sentence)
                    persists = False
        
        if not destination and trajectory_destination and not trajectory_source:
            if verbose:
                print('trajectory_destination')
            if tuple(trajectory_destination) == (('motion', 'theme', 'trajectory'), ('has_location', 'theme', 'destination')): 
                theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
                if theme:
                    destination = list(set(findLocation(args_vn, args_pb, 'destination', 'AM-GOL', sentence)).union(set(findLocation(args_vn, args_pb, 'destination', 'AM-LOC', sentence))))
                    if not destination:
                        destination = findSubsumedNP_as_Loc(theme, args_vn, 'theme', sentence) 
        if not source and not destination and trajectory_only:            
            if verbose:
                print('trajectory only')
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
            
            if theme:
                trajectory = list(set(findRawLocation(args_vn, args_pb, 'trajectory', 'AM-DIR', sentence)).union(set(findRawLocation(args_vn, args_pb, 'trajectory', 'A2', sentence))))
                # distinguish allative vs. ablative
                if verbose:
                    print(trajectory)
                if trajectory:
                    source, destination = ablative_allative(trajectory, sentence)
                    if verbose:
                        print('source and destination found using ablative_allative distinction:', source, destination)


        if not source and not destination and motion_source:
            if verbose:
                print('motion_source')
            if tuple(motion_source) == (('has_location', 'theme', 'source'), ('motion', 'theme')):
                theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
                if theme:
                    source, destination = findLocation(args_vn, args_pb, 'source', 'A2', sentence), findLocation(args_vn, args_pb, 'goal', 'A0', sentence)
                    if not destination:
                        destination = findSubsumedNP_as_Loc(theme, args_vn, 'theme', sentence)

        if not source and not destination and general_location:
            if verbose:
                print('general_location')
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
            if theme:
                if not destination:
                    destination = list(set(findLocation(args_vn, args_pb, 'location', 'AM-LOC', sentence)))
                    if not destination:
                        destination = findSubsumedNP_as_Loc(theme, args_vn, 'theme', sentence)
        if not source and not destination and general_location_2:
            if verbose:
                print('general_location_2')
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
            if theme:              
                destination = list(set(findLocation(args_vn, args_pb, 'goal', 'A2', sentence)).union(set(findLocation(args_vn, args_pb, 'goal', 'AM-GOL', sentence))).union(findLocation(args_vn, args_pb, 'goal', 'AM-LOC', sentence)))
                if not destination:
                    destination = findSubsumedNP_as_Loc(theme, args_vn, 'theme', sentence)
        if not source and not destination and general_location_3:
            if verbose:
                print('general_location_3')
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
            if theme:
                set1 = set(findLocation(args_vn, args_pb, 'destination', 'A2', sentence))
                set2 = set(findLocation(args_vn, args_pb, 'destination', 'AM-LOC', sentence))
                set3 = set(findLocation(args_vn, args_pb, None, 'AM-DIR', sentence))
                set4 = set(findLocation(args_vn, args_pb, 'destination', 'AM-GOL', sentence))
                if not destination:
                    destination = list(set1.union(set2).union(set4))
                    if not destination:
                        destination = findSubsumedNP_as_Loc(theme, args_vn, 'theme', sentence)
        
        if not source and not destination and body_motion: 
            if verbose:
                print('body_motion')
            theme, raw_themes = findTargetEntity(target_entities, args_vn, args_pb, 'agent', 'A0', split, pid, sid, sentence)
            if theme:           
                destination = findLocation(args_vn, args_pb, 'location', 'AM-LOC', sentence)
                if not destination:
                    destination = findSubsumedNP_as_Loc(theme, args_vn, 'agent', sentence)
        
        if not source and not destination and contain: 
            if verbose:
                print('contain')
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'pivot', 'A0', split, pid, sid, sentence)
            if theme:
                destination = findLocation(args_vn, args_pb, 'theme', 'A1', sentence)
                if not destination:
                    destination = findSubsumedNP_as_Loc(theme, args_vn, 'pivot', sentence)
        
        if not source and not destination and take_in_1:
            if verbose:
                print('take_in_1')
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
            if theme:
                source, destination = findLocation(args_vn, args_pb, 'source', 'A2', sentence), findLocation(args_vn, args_pb, 'goal', 'A0', sentence)
                if not destination:
                    destination = findSubsumedNP_as_Loc(theme, args_vn, 'theme', sentence)
        
        if not source and not destination and take_in_2: 
            if verbose:
                print('take_in_2')
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'patient', 'A1', split, pid, sid, sentence)
            if theme:
                destination = findLocation(args_vn, args_pb, 'agent', 'A0', sentence) 
                if not destination:
                    destination = findSubsumedNP_as_Loc(theme, args_vn, 'patient', sentence)
        
        if not source and not destination and take_in_3:
            if verbose:
                print('take_in_3')
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
            if theme:
                destination = findLocation(args_vn, args_pb, 'recipient', 'A2', sentence)
                if not destination:
                    destination = findSubsumedNP_as_Loc(theme, args_vn, 'theme', sentence)
        
        if not source and not destination and emit:
            if verbose:
                print('emit')
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
            if theme:
                source = findLocation(args_vn, args_pb, 'agent', 'A0', sentence)
                persists = False
        
        if not source and not destination and appear: 
            if verbose:
                print('appear')
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
            if theme:
                destination = findLocation(args_vn, args_pb, 'location', 'AM-LOC', sentence)
                if not destination:
                    destination = findSubsumedNP_as_Loc(theme, args_vn, 'theme', sentence)
       
        if not source and not destination and filled: 
            if verbose:
                print('filled')
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A2', split, pid, sid, sentence)
            if theme:
                destination = findLocation(args_vn, args_pb, 'location', 'A1', sentence)

        if not source and not destination and penetration:
            if verbose:
                print('penetrating')
            theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'instrument', None, split, pid, sid, sentence) 
            if theme:
                destination = findLocation(args_vn, args_pb, 'patient', None, sentence)
                if not destination:
                    destination = findSubsumedNP_as_Loc(theme, args_vn, 'instrument', sentence)
        if trajectory_source_agent and trajectory_destination_agent:
            if verbose:
                print('agent motion')
            agent_theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'agent', 'A0', split, pid, sid, sentence)
            if verbose:
                print('moving agent:', agent_theme)
                print('target_entities:',target_entities)
            
            if agent_theme:
                if not agent_source:
                    agent_source = list(set(findLocation(args_vn, args_pb, 'source', 'AM-DIR', sentence)).union(set(findLocation(args_vn, args_pb, 'initial_location', 'AM-DIR', sentence))))
                    if verbose:
                        print('source:', agent_source)
                if not agent_destination:
                    agent_destination = list(set(findLocation(args_vn, args_pb, 'destination', 'AM-GOL', sentence)).union(set(findLocation(args_vn, args_pb, 'destination', 'AM-LOC', sentence))))
                    if not agent_destination:
                        agent_destination = findSubsumedNP_as_Loc(agent_theme, args_vn, 'agent', sentence)
                    if verbose:
                        print('destination:', agent_destination)
                if agent_source and not agent_destination:
                    persists = False        
    else:
        if args_vn:
            if verbose:
                print('only rely on args_vn')
            if 'theme' in args_vn:
                theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
                if theme:
                    if not source and ('source' in args_vn or 'initial_location' in args_vn):
                        source = list(set(findLocation(args_vn, args_pb, 'source', 'AM-DIR', sentence)).union(set(findLocation(args_vn, args_pb, 'initial_location', 'AM-DIR', sentence))))
                    if not destination and ('destination' in args_vn or 'location' in args_vn):
                        destination = list(set(findLocation(args_vn, args_pb, 'destination', 'AM-GOL', sentence)).union(set(findLocation(args_vn, args_pb, 'destination', 'AM-LOC', sentence))).union(set(findLocation(args_vn, args_pb, 'destination', 'A2', sentence))).union(set(findLocation(args_vn, args_pb, 'location', 'AM-GOL', sentence))).union(set(findLocation(args_vn, args_pb, 'location', 'A2', sentence))).union(set(findLocation(args_vn, args_pb, 'location', 'AM-LOC', sentence))))
                        if not destination:
                            destination = findSubsumedNP_as_Loc(theme, args_vn, 'theme', sentence)
        
    if vn_sense.startswith('seem-'): 
        if verbose:
            print('seem')
        theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
        if verbose:
            print('theme:', theme)
        if theme:
            d = findLocation(args_vn, args_pb, 'attribute', 'A2', sentence)
            if d:
                rootpos = checkRootPOS(d[0])
                d_root = getNPhead(sentence, d[-1])
                if rootpos and d_root:
                    if rootpos == 'ADP':
                        destination = [d_root]
                    elif rootpos == 'ADV' and isLocative(d_root):
                        destination = [d_root]
            else:
                d = findSubsumedNP_as_Loc(theme, args_vn, 'theme', sentence)
                if d:
                    rootpos = checkRootPOS(d[0])
                    d_root = getNPhead(sentence, d[-1])
                    if rootpos and d_root:
                        if rootpos == 'ADP':
                            destination = [d_root]
                        elif rootpos == 'ADV' and isLocative(d_root):
                            destination = [d_root]

    
    if theme:
        if source:
            source = [j.lower() for j in source]
        # else:
        #     for t in theme:
        #         source = commonsense_location(tokenize(raw_paragraph), t)
        #         if source:
        #             break
        if destination:
            destination = [j.lower() for j in destination]

        if verbose:
            print('theme: {}, source: {}, destination: {}'.format(theme, source, destination))
                
        states = move(events, theme, args_vn, args_pb, states, pid, sid, sentence, vn_sense, ss=source, dd=destination, persists=persists, raw_paragraph=raw_paragraph, verbose=verbose)
        move_update = True
        updated_themes_for_event += theme
    # ablation: vsf
    else:
        if focus_verb and focus_verb in vsf_dict_verb.keys():
            for vsf in vsf_dict_verb[focus_verb]:
                if vsf in propara_vsf_map['move']:
                    theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
                    # raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A1', vn_role='patient', vn_source_role=None, pb_source_role=None, split=split, pid=split, sid=sid, sentence=sentence, verbose=verbose)
                    if theme:
                        if not destination:
                            l1 = findLocation(args_vn, args_pb, None, 'AM-LOC', sentence)
                            l11 = findLocation(args_vn, args_pb, None, 'AM-GOL', sentence) 
                            l12 = findLocation(args_vn, args_pb, 'destination', None, sentence)
                            l13 = findLocation(args_vn, args_pb, 'goal', None, sentence)
                            l14 = findLocation(args_vn, args_pb, 'location', None, sentence)
                            l2 = findLocation(args_vn, args_pb, None, 'A0', sentence)
                            destination = l1 + l11 + l12 + l13 + l14 + l2
                                # move(events, theme, args_vn, args_pb, states, pid, sid, sentence, vn_sense, ss=source, dd=destination, persists=persists, raw_paragraph=raw_paragraph, verbose=verbose)
                        states = move(events, theme, args_vn, args_pb, states, pid, sid, sentence, vn_sense, source, destination,persists,raw_paragraph, verbose=verbose) 
                        move_update = True
        if not theme:
            for l in bso_vsf_verbs:
                if l['vsf'] == 'move':
                    if focus_verb in l['verbs']:
                        theme, _ = findTargetEntity(target_entities, args_vn, args_pb, 'theme', 'A1', split, pid, sid, sentence)
                        if theme:
                            if not destination:
                                l1 = findLocation(args_vn, args_pb, None, 'AM-LOC', sentence)
                                l11 = findLocation(args_vn, args_pb, None, 'AM-GOL', sentence) 
                                l12 = findLocation(args_vn, args_pb, 'destination', None, sentence)
                                l13 = findLocation(args_vn, args_pb, 'goal', None, sentence)
                                l14 = findLocation(args_vn, args_pb, 'location', None, sentence)
                                l2 = findLocation(args_vn, args_pb, None, 'A0', sentence)
                                destination = l1 + l11 + l12 + l13 + l14 + l2
                            states = move(events, theme, args_vn, args_pb, states, pid, sid, sentence, vn_sense, source, destination,persists,raw_paragraph, verbose=verbose) 
                            move_update = True        
    if agent_theme:
        for t in agent_theme:
            # if not agent_source:
            #     agent_source = commonsense_location(tokenize(raw_paragraph), t)            
            states = move(events, agent_theme, args_vn, args_pb, states, pid, sid, sentence, vn_sense, ss=agent_source, dd=agent_destination, persists=persists, raw_paragraph=raw_paragraph, verbose=verbose)
            move_update = True
            updated_themes_for_event += [t]
    return states