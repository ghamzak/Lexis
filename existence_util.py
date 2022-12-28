from util2 import *
from from_spacy import *

def create(data_created_entities, states, pid, sid, creation_location,raw_paragraph=None,verbose=False):        
    # if verbose:
    #     print('data_created_entities, raw_created_entities:', data_created_entities, raw_created_entities)
    for jj in range(len(data_created_entities)):
        ce = data_created_entities[jj]

        # if it's the first step, or if there is no cos prior to this, mark it as CREATE. 
        # 10/10/2022: following commented out
        # if set([states[pid][ce][i+1]['cos_type'] for i in range(0,sid)]) == set(['NONE']) or sid == 0:
        states[pid][ce][sid+1]['cos_type'] = 'CREATE'

        for i in range(sid-1, -1, -1):
            # 10/10/2022: commented out
            # if states[pid][ce][i+1]['cos_type'] != 'NONE':
            #     break  
            # 10/10/2022: added
            states[pid][ce][i+1]['cos_type'] = 'NONE'
            # 10/10/2022: following not changed
            states[pid][ce][i+1]['s1'] = '-'
            states[pid][ce][i+1]['s2'] = '-'
        states[pid][ce][sid+1]['s1'] = '-'
        states[pid][ce][sid+1]['s2'] = '?'
        potential_creation_location = commonsense_location(tokenize(raw_paragraph), ce)
        potential_creation_location = ''
        if (creation_location and creation_location[0] != '-') or states[pid][ce][sid+1]['s2'] == '?' or potential_creation_location: # 
            to_update = ''
            if creation_location and creation_location[0]:
                to_update = creation_location[0]
            elif potential_creation_location:
                print('actually updated using commonsense')
                to_update = potential_creation_location[0]
            else:
                to_update = states[pid][ce][sid+1]['s2']
            states[pid][ce][sid+1]['s2'] = to_update
            if sid+2 < len(states[pid][ce])+1:
                for i in range(sid+2, len(states[pid][ce])+1):
                    if states[pid][ce][i]['cos_type'] != 'NONE':
                        break
                    states[pid][ce][i]['s1'] = to_update
                    states[pid][ce][i]['s2'] = to_update       

    return states

def destroy(data_destroyed, states, pid, sid, destruction_location, verbose=False):
    # if verbose:
    #     print('data_destroyed, raw_destroyed:', data_destroyed, raw_destroyed)   
    for jj in range(len(data_destroyed)):
        de = data_destroyed[jj]
        if states[pid][de][sid+1]['s1'] != '-':
            states[pid][de][sid+1]['cos_type'] = 'DESTROY'
            states[pid][de][sid+1]['s2'] = '-'
            if destruction_location:
                states[pid][de][sid+1]['s1'] = destruction_location[-1]
            if sid+2 < len(states[pid][de])+1:
                for i in range(sid+2, len(states[pid][de])+1):
                    states[pid][de][i]['s1'] = '-'
                    states[pid][de][i]['s2'] = '-'        
        # do I need to extract the potentially mentioned location of de entity in sentence sid?
    return states

def updateExistence(target_entities, events, spans, states, pid, sid, sentence, split, vn_sense, raw_paragraph, verbose=False):
    args_vn, args_pb = createArgsDicts(events, spans, vn_sense, sentence) 
    if args_pb and 'V <-> Verb' in args_pb:
        focus_verb = args_pb['V <-> Verb']
        focus_verb = token_lemmatize(focus_verb)
    if verbose:
        print('args_vn:', args_vn)
        print('args_pb:', args_pb)

    _, _, args, polarpreds, pred_triples_abstract, pb_pred_triples_abstract, pred_tuple_abstract, pb_pred_tuples_abstract, vn_tuples_abstract_general, pb_tuples_abstract_general = predlist_polarity_args(events, args_pb)
    raw_created, data_created, raw_source, data_destroyed, raw_destroyed, creation_location = [], [], [], [], [], []

    create_update, destroy_update = False, False
    with open('/data/ghazaleh/datasets/verb_vsf2.pickle', 'rb') as rf:
            vsf_dict_verb = pickle.load(rf)        
    with open('/data/ghazaleh/datasets/bso_direct_vsf_propara3.pickle', 'rb') as rf:
        bso_vsf_verbs = pickle.load(rf)

    propara_vsf_map = {'destroy': ['end_state: destroyed', 'result: +destroy', 'v_final_state: broken', 'v_final_state: destroyed', 'v_final_state: disintegrated'],
                'create': ['result: +create', 'v_final_state: created'], 
                'move': ['activity: remove', 'activity: free', 'activity_type: hike', 'activity_type: sport', 'activity_type: travel', 'activity_type: walk', 'direction_of_motion: x', 'manner_of_motion: x', 'motion_path: x', 'motion_medium: x', 'property_changed: location', 'result: +join', 'result: -join', 'result: free', 'vehicle_type: x']}
    destruction_location, creation_location = [], []
    if verbose:
        print('updateExistence')
        print('vn_tuples_abstract_general:',vn_tuples_abstract_general)
        print('pb_tuples_abstract_general:',pb_tuples_abstract_general)
    # check vn
    if verbose:
        y = tuple([x for x in polarpreds if x == 'be' or x == '!be'])
        if y:
            print(y)
        y = tuple([x for x in polarpreds if x == '!has_state' or x == 'has_state'])
        if y:
            print(y)
        
    if [vnc for vnc in ['birth', 'create', 'become', 'turn', 'build', 'engender', 'establish', 'exist', 'grow', 'knead', 'preparing', 'scribble', 'transcribe', 'rear', 'calve', 'convert'] if vn_sense.startswith(vnc+'-')]:        
        if vn_sense.startswith('birth-') and tuple([x for x in polarpreds if x == 'be' or x == '!be']) == ('!be', 'be'):            
            raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A1', vn_role='patient', vn_source_role='agent', pb_source_role='A0', split=split, pid=split, sid=sid, sentence=sentence, verbose=verbose)            
        elif vn_sense.startswith('create-') and tuple([x for x in polarpreds if x=='be' or x == '!be']) == ('!be', 'be'):            
            raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A1', vn_role='result', vn_source_role='material', pb_source_role='A2', split=split, pid=pid, sid=sid, sentence=sentence, verbose=verbose)
        elif vn_sense.startswith('become-') and tuple([x for x in polarpreds if x=='has_state' or x=='!has_state']) == ('!has_state', 'has_state'):
        #     # check if the result argument is not headed by an adjective
            if 'result' in args_vn and args_vn['result']:
                curdoc = nlp(args_vn['result'])
                root = [token for token in curdoc if token.head == token]
                if root:
                    root = root[0]
                    # if root.pos_ == 'ADJ':
                    #     pass
                    if root.pos_ == 'NOUN':
                        raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A2', vn_role='result', vn_source_role='patient', pb_source_role='A1', split=split, pid=pid, sid=sid, sentence=sentence, verbose=verbose)          
        elif vn_sense.startswith('turn-') or vn_sense.startswith('convert-'):
            jj = tuple([x for x in vn_tuples_abstract_general if x ==('has_state', 'patient', 'initial_state') or x == ('has_state', 'patient', 'result')])
            if jj == (('has_state', 'patient', 'initial_state'), ('has_state', 'patient', 'result')):
                raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A2', vn_role='result', vn_source_role='patient', pb_source_role='A1', split=split, pid=pid, sid=sid, sentence=sentence, verbose=verbose)                
                creation_location = list(set(findLocation(args_vn, args_pb, None, 'AM-LOC', sentence)).union(set(findLocation(args_vn, args_pb, None, 'A0', sentence))))

        elif vn_sense.startswith('build-') and tuple([x for x in polarpreds if x=='be' or x=='!be']) == ('!be', 'be'):
            raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A1', vn_role='product', vn_source_role='material', pb_source_role='A2', split=split, pid=pid, sid=sid, sentence=sentence, verbose=verbose) 
            if not raw_source:
                raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A1', vn_role='product', vn_source_role='agent', pb_source_role='A0', split=split, pid=pid, sid=sid, sentence=sentence, verbose=verbose) 
        elif vn_sense.startswith('engender-') and tuple([x for x in polarpreds if x == 'be' or x == '!be']) in [('!be', 'be'), ('!be', 'be', 'be')]:
            raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A1', vn_role='patient', vn_source_role='precondition', pb_source_role='A0', split=split, pid=split, sid=sid, sentence=sentence, verbose=verbose) 
        elif vn_sense.startswith('establish-') and tuple([x for x in polarpreds if x == 'be' or x == '!be']) == ('!be', 'be'):
            raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A1', vn_role='patient', vn_source_role='agent', pb_source_role='A0', split=split, pid=split, sid=sid, sentence=sentence, verbose=verbose)    
        elif vn_sense.startswith('exist-') and tuple(polarpreds) in [('be'), ('be', 'has_location')] :
            raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A1', vn_role='theme', vn_source_role='location', pb_source_role='AM-LOC', split=split, pid=split, sid=sid, sentence=sentence, verbose=verbose)    
        elif vn_sense.startswith('grow-') and tuple([x for x in polarpreds if x == 'be' or x == '!be']) == ('!be', 'be'):
            raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A1', vn_role='product', vn_source_role='patient', pb_source_role=None, split=split, pid=split, sid=sid, sentence=sentence, verbose=verbose)    # vn_source_role='patient'
        elif vn_sense.startswith('knead-') and tuple([x for x in polarpreds if x == 'be' or x == '!be']) == ('!be', 'be'):
            raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role=None, vn_role='product', vn_source_role='material', pb_source_role='A1', split=split, pid=split, sid=sid, sentence=sentence, verbose=verbose)            
        elif vn_sense.startswith('preparing-') and tuple([x for x in polarpreds if x == 'be' or x == '!be']) == ('!be', 'be'):
            raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A1', vn_role='product', vn_source_role='material', pb_source_role=None, split=split, pid=split, sid=sid, sentence=sentence, verbose=verbose)
        elif (vn_sense.startswith('scribble-') or vn_sense.startswith('transcribe-')) and tuple([x for x in polarpreds if x == 'be' or x == '!be']) == ('!be', 'be'):
            raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A1', vn_role='theme', vn_source_role=None, pb_source_role=None, split=split, pid=split, sid=sid, sentence=sentence, verbose=verbose)            
        elif vn_sense.startswith('rear-') and tuple([x for x in polarpreds if x == 'develop']) == ('develop'):
            raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A1', vn_role='product', vn_source_role='material', pb_source_role=None, split=split, pid=split, sid=sid, sentence=sentence, verbose=verbose)
        elif vn_sense.startswith('calve-') and tuple([x for x in polarpreds if x == 'give_birth']) == ('give_birth'):
            raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A1', vn_role='patient', vn_source_role='agent', pb_source_role='A0', split=split, pid=split, sid=sid, sentence=sentence, verbose=verbose)        
        
        if not creation_location:
            creation_location = findLocation(args_vn, args_pb, None, 'AM-LOC', sentence)
            if not creation_location:
                creation_location = findLocation(args_vn, args_pb, 'agent', 'A0', sentence)
                if not creation_location and raw_source:
                    creation_location = raw_source
                    
        if data_created:
            if not creation_location and raw_paragraph:
                for dc in data_created:
                    creation_location = commonsense_location(tokenize(raw_paragraph), dc)
                    if creation_location:
                        break
            states = create(data_created, states, pid, sid, creation_location, raw_paragraph, verbose=verbose) 
            create_update = True
    # ablation: vsf
    if not create_update:        
        if focus_verb in vsf_dict_verb.keys():
            for vsf in vsf_dict_verb[focus_verb]:
                if vsf in propara_vsf_map['create']:
                    raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A1', vn_role='patient', vn_source_role=None, pb_source_role=None, split=split, pid=split, sid=sid, sentence=sentence, verbose=verbose)
                    if data_created:
                        if not creation_location:
                            l1 = findLocation(args_vn, args_pb, None, 'AM-LOC', sentence)
                            l2 = findLocation(args_vn, args_pb, None, 'A0', sentence)
                            creation_location = l1 + l2
                        states = create(data_created, states, pid, sid, creation_location, raw_paragraph, verbose=verbose) 
                        create_update = True                        
        if not create_update:
            for l in bso_vsf_verbs:
                if l['vsf'] == 'create':
                    if focus_verb in l['verbs']:
                        raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A1', vn_role='patient', vn_source_role=None, pb_source_role=None, split=split, pid=split, sid=sid, sentence=sentence, verbose=verbose)
                        if data_created:
                            if not creation_location:
                                l1 = findLocation(args_vn, args_pb, None, 'AM-LOC', sentence)
                                l2 = findLocation(args_vn, args_pb, None, 'A0', sentence)
                                creation_location = l1 + l2 
                            states = create(data_created, states, pid, sid, creation_location, raw_paragraph, verbose=verbose) 
                            create_update = True
    
    
    # destroy
    if [vnc for vnc in ['break', 'break_down', 'carve', 'cut', 'murder', 'die', 'destroy', 'disappearance', 'turn', 'become', 'convert', 'absorb', 'remove', 'stop'] if vn_sense.startswith(vnc+'-')]:        
        destruction_location = []
        for vnc in ['break', 'break_down', 'carve', 'cut']:
            if vn_sense.startswith(vnc+'-') and tuple([x for x in polarpreds if 'degradation_material_integrity' in x]) == ('!degradation_material_integrity', 'degradation_material_integrity'):
                if verbose:
                    print('break, carve, cut, degradation_material_integrity')
                raw_destroyed, data_destroyed = findDestroyedEntity(target_entities, args_pb, args_vn, 'A1', 'patient', split, pid, sid, sentence, verbose=verbose)
                if verbose:
                    print(raw_destroyed, data_destroyed)
        for vnc in ['murder', 'die']:
            if vn_sense.startswith(vnc+'-') and tuple([x for x in polarpreds if 'alive' in x]) == ('alive', '!alive'):
                raw_destroyed, data_destroyed = findDestroyedEntity(target_entities, args_pb, args_vn, 'A1', 'patient', split, pid, sid, sentence, verbose=verbose) 
        if vn_sense.startswith('destroy-') and tuple([x for x in polarpreds if 'destroyed' in x]) == ('!destroyed', 'destroyed'):
            raw_destroyed, data_destroyed = findDestroyedEntity(target_entities, args_pb, args_vn, 'A1', 'patient', split, pid, sid, sentence, verbose=verbose) 
        if (vn_sense.startswith('turn-') or vn_sense.startswith('convert-')) and tuple([x for x in vn_tuples_abstract_general if x == ('has_state', 'patient', 'initial_state')]):
            jj = tuple([x for x in vn_tuples_abstract_general if x ==('has_state', 'patient', 'initial_state') or x == ('has_state', 'patient', 'result')]) 
            if verbose:
                print(jj)
            if jj == (('has_state', 'patient', 'initial_state'), ('has_state', 'patient', 'result')): 
                if findDestroyedEntity(target_entities, args_pb, args_vn, 'A1', 'patient', split, pid, sid, sentence, verbose=verbose) :
                    res = findRawLocation(args_vn, args_pb, 'result', 'A2', sentence)
                    if res and (res[0].startswith('to ') or res[0].startswith('into ')):
                        raw_destroyed, data_destroyed = findDestroyedEntity(target_entities, args_pb, args_vn, 'A1', 'patient', split, pid, sid, sentence, verbose=verbose) 
                        if verbose:
                            print(data_destroyed, raw_destroyed)
                        destruction_location = list(set(findLocation(args_vn, args_pb, None, 'AM-LOC', sentence)).union(set(findLocation(args_vn, args_pb, None, 'A0', sentence))))

        if vn_sense.startswith('become-') and tuple([x for x in vn_tuples_abstract_general if x == ('!has_state', 'patient', 'result') or x == ('has_state', 'patient', 'result')]) == (('!has_state', 'patient', 'result'), ('has_state', 'patient', 'result')):
            if 'result' in args_vn and args_vn['result']:
                curdoc = nlp(args_vn['result'])
                root = [token for token in curdoc if token.head == token]
                if root:
                    root = root[0]
                    # if root.pos_ == 'ADJ':
                    #     pass
                    if root.pos_ == 'NOUN':
                        raw_created, data_created, raw_source = findCreatedEntity(target_entities=target_entities, args_pb=args_pb, args_vn=args_vn, pb_role='A2', vn_role='result', vn_source_role='patient', pb_source_role='A1', split=split, pid=pid, sid=sid, sentence=sentence, verbose=verbose)          
                        raw_destroyed, data_destroyed = findDestroyedEntity(target_entities, args_pb, args_vn, 'A1', 'patient', split, pid, sid, sentence, verbose=verbose)


        if vn_sense.startswith('absorb-') and tuple([x for x in vn_tuples_abstract_general if x == ('take_in', 'goal', 'theme')]):
            raw_destroyed, data_destroyed = findDestroyedEntity(target_entities, args_pb, args_vn, 'A1', 'goal', split, pid, sid, sentence, verbose=verbose)
        if vn_sense.startswith('remove-') or vn_sense.startswith('stop-'):
            raw_destroyed, data_destroyed = findDestroyedEntity(target_entities, args_pb, args_vn, 'A1', 'theme', split, pid, sid, sentence, verbose=verbose)
        
        if not destruction_location:
            destruction_location = findLocation(args_vn, args_pb, None, 'AM-LOC', sentence)
            

        if verbose:
            print('raw_destroyed: {}, data_destroyed: {}'.format(raw_destroyed, data_destroyed))
    # ablation: vsf            
    if not data_destroyed and spans:
        # patient = findDestroyedEntity(target_entities, args_pb, args_vn, 'A1', None, split, pid, sid, sentence, verbose=verbose)        
        if focus_verb in vsf_dict_verb.keys():
            for vsf in vsf_dict_verb[focus_verb]:
                if vsf in propara_vsf_map['destroy']:                    
                    raw_destroyed, data_destroyed = findDestroyedEntity(target_entities, args_pb, args_vn, 'A1', 'patient', split, pid, sid, sentence, verbose)
                    if data_destroyed:
                        if not destruction_location:
                            l1 = findLocation(args_vn, args_pb, None, 'AM-LOC', sentence)                            
                            destruction_location = l1                        
                        
        if not data_destroyed:
            for l in bso_vsf_verbs:
                if l['vsf'] == 'destroy':
                    if focus_verb in l['verbs']:
                        raw_destroyed, data_destroyed = findDestroyedEntity(target_entities, args_pb, args_vn, 'A1', 'patient', split, pid, sid, sentence, verbose)
                        if data_destroyed:
                            if not destruction_location:
                                l1 = findLocation(args_vn, args_pb, None, 'AM-LOC', sentence)                                
                                destruction_location = l1
    data_destroyed = [x.strip() for x in data_destroyed]
    if data_destroyed and [x for x in raw_destroyed if 'some ' in x] == []:
        # if not destruction_location and raw_paragraph:
        #     for dd in data_destroyed:
        #         destruction_location = commonsense_location(tokenize(raw_paragraph), dd)
        #         if destruction_location:
        #             break
        states = destroy(data_destroyed, states, pid, sid, destruction_location, verbose=verbose) 
        destroy_update = True
    return states, destroy_update