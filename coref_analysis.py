import pickle, os, pprint
from util import dataPrepare
from vnpreds import overlap
import re
import spacy
nlp = spacy.load("en_core_web_sm")

pp = pprint.PrettyPrinter(indent=1, compact=True)




def find_coref_for_paragraph(split, paragraph_id, target_entities_only=True, forRebuilding=False):
    filename = 'coref_results_propara_'+split+'_08_17_2022.pickle'
     
    results_address = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'coref_results', filename)
    with open(results_address, 'rb') as handle:
        results = pickle.load(handle)
    focus = results[paragraph_id]

    split_data = dataPrepare(split)
    split_data_raw = split_data.rawdata
    focus_paragraph_raw = split_data_raw[paragraph_id]
    split_participants = split_data.participants
    focus_participants = split_participants[paragraph_id]
    i = 100
    tracking_coreference = []
    if not target_entities_only:
        return focus['clusters']
    entity2mention = dict(zip(focus_participants, [[] for i in range(len(focus_participants))]))
    
    
    for cluster in focus['clusters']:
        cluster_code = 'cc_' + str(i)    
        i += 100    
        tracking_coreference += [{'cluster_code': cluster_code, 'mentions': [], 'target_entities': [], 'mention_sid': []}]
        for mention in cluster:
            tracking_coreference[-1]['mentions'] += [mention]
            id_tuple, entity_span = mention
            first_guess_sent_id = (focus['tokenized_doc']['sentence_map'][id_tuple[0]], focus['tokenized_doc']['sentence_map'][id_tuple[1]])            
            # print(first_guess_sent_id[0].tolist()+1)
            true_sent_id = None
            if first_guess_sent_id[0] == first_guess_sent_id[1]:
                if first_guess_sent_id[0].tolist()+1 in focus_paragraph_raw and overlap(focus_paragraph_raw[first_guess_sent_id[0].tolist()+1], entity_span):
                    true_sent_id = first_guess_sent_id[0].tolist()+1
                elif first_guess_sent_id[0].tolist() in focus_paragraph_raw and overlap(focus_paragraph_raw[first_guess_sent_id[0].tolist()], entity_span):
                    true_sent_id = first_guess_sent_id[0].tolist()
                elif first_guess_sent_id[0].tolist()+2 in focus_paragraph_raw and overlap(focus_paragraph_raw[first_guess_sent_id[0].tolist()+2], entity_span):
                    true_sent_id = first_guess_sent_id[0].tolist()+2
            if true_sent_id:
                tracking_coreference[-1]['mention_sid'] += [(entity_span, true_sent_id)]
                if target_entities_only:
                    for t in focus_participants:
                        if overlap(entity_span.lower(), t):
                            if t not in tracking_coreference[-1]['target_entities']:
                                tracking_coreference[-1]['target_entities'] += [t]                                       
            else:                   
                pass
    for cluster in tracking_coreference:
        if cluster['target_entities']:
            for te in cluster['target_entities']:
                entity2mention[te] += cluster['mention_sid']
    if forRebuilding:
        return entity2mention, tracking_coreference
    else:
        return entity2mention


# entity2mention = find_coref_for_paragraph('dev', 4) 
# pp.pprint(entity2mention)

def checkCoreference(split, paragraph_id, span, sentence_id):
    entity2mention = find_coref_for_paragraph(split, paragraph_id)
    coreferences = []
    for entity, cluster in entity2mention.items():
        cluster = [(x[0].lower(), x[1]) for x in cluster]
        if (span, sentence_id) in cluster:
            coreferences += [entity]    
    return coreferences

def tokenize(paragraph: str):
    """
    Change the paragraph to lower case and tokenize it!
    """
    paragraph = re.sub(' +', ' ', paragraph)  # remove redundant spaces in some sentences.
    para_doc = nlp(paragraph.lower())  # create a SpaCy Doc instance for paragraph
    tokens_list = [token.text for token in para_doc]
    return ' '.join(tokens_list), len(tokens_list)

def createNewResolvedParagraph(split, paragraph_id):
    """
    get the raw paragraph, get the coref resolution results, substitute if pronominal (use a list of pronominals)
    """
    split_data = dataPrepare(split)
    split_data_raw = split_data.rawdata
    focus_paragraph_raw = split_data_raw[paragraph_id]
    pronouns = ['you', 'he', 'him', 'his', 'she', 'her', 'it', 'we', 'our', 'us', 'they', 'them', 'their']

    _, tracking = find_coref_for_paragraph(split, paragraph_id, target_entities_only=True, forRebuilding=True)
    focus_paragraph_raw_whole = ' '.join(list(focus_paragraph_raw.values()))
    tokenized_paragraph = tokenize(focus_paragraph_raw_whole)
    tokenized_paragraph = tokenized_paragraph[0].split(' ')
    new_paragraph_tokens = tokenized_paragraph
    
    for cl in tracking:
        mentions, target_entities, mention_sid = cl['mentions'], cl['target_entities'], cl['mention_sid']
        # example: {'cluster_code': 'cc_100', 'mentions': [((0, 0), 'Plants'), ((3, 3), 'They')], 'target_entities': ['plants'], 'mention_sid': [('Plants', 1), ('They', 2)]}
        for mention in mentions:
            # ((0, 0), 'Plants')
            # ((3, 3), 'They')
            if len(mention) == 2 and type(mention[1]) == str and type(mention[0]) == tuple and mention[1].lower() in pronouns and mention[0][0] in list(range(len(tokenized_paragraph))) and mention[1].lower() == tokenized_paragraph[mention[0][0]]:
                if target_entities:
                    new_paragraph_tokens[mention[0][0]] = target_entities[0]
    new_paragraph = ' '.join(new_paragraph_tokens)
    # new_paragraph_sentence_split = new_paragraph.split(' . ')
    new_paragraph_sentence_split = [x.strip() for x in new_paragraph.split('. ')]
    new_paragraph_sentence_split[-1] = new_paragraph_sentence_split[-1][:-1].strip()
    new_paragraph_dict = {i: new_paragraph_sentence_split[i-1]+'.' for i in range(1,len(new_paragraph_sentence_split)+1)}
    return new_paragraph, new_paragraph_dict


if __name__ == '__main__':
    # print(checkCoreference('dev', 4, 'buried area', 8))
    # print(find_coref_for_paragraph('test', 661, target_entities_only=True))
    print(find_coref_for_paragraph('dev', 4, target_entities_only=False))
    # print(createNewResolvedParagraph('dev', 4))