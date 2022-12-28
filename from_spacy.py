import spacy
import re

nlp = spacy.load("en_core_web_sm")
nlp2 = spacy.load("en_core_web_lg")

def spacyObject(sentence):
  return nlp(sentence)

# def spacyObject2(sentence):
#   return nlp2(sentence)  


def tokenize(paragraph: str):
    """
    Change the paragraph to lower case and tokenize it!
    """
    paragraph = re.sub(' +', ' ', paragraph)  # remove redundant spaces in some sentences.
    para_doc = nlp(paragraph.lower())  # create a SpaCy Doc instance for paragraph
    tokens_list = [token.text for token in para_doc]
    return ' '.join(tokens_list)

def token_lemmatize(token):
    # lemmatizer = nlp.add_pipe("lemmatizer")    
    doc = nlp(token)    
    token = doc[0]
    return token.lemma_

def lemmatize(token, clause):
    doc = nlp(clause)
    lemma = [t.lemma_ for t in doc if t.text == token]
    if lemma:
      return lemma[0]   
    else:
      return token

def getNPhead(clause, np):
    doc = nlp(clause)
    from difflib import get_close_matches
    # find the chunk closest to np 
    chunk_doc = spacyObject(np)
    nphead = [chunk.root.text for chunk in chunk_doc.noun_chunks]
    if nphead:   
      my_chunk = get_close_matches(nphead[-1], [chunk.root.text for chunk in doc.noun_chunks]) # , n=3, cutoff=0.3
      if my_chunk:
        my_chunk_object = [chunk for chunk in doc.noun_chunks if chunk.text == my_chunk[0] or chunk.root.text == my_chunk[0]][0]
        return my_chunk_object.root.text
      else:
        return nphead[-1]
    else:
      r = findRoot(np)
      if r:
        return r
      else:
        return ''



def getPPnominalHead(clause, pp):
    doc = nlp(clause)
    from difflib import get_close_matches
    # find the chunk closest to pp     
    my_chunk = get_close_matches(pp, [chunk.text for chunk in doc.noun_chunks], n=3, cutoff=0.3)
    if my_chunk:
        # print(my_chunk)
        head = []
        for c in range(len(my_chunk)):
            if head:
              break
            my_chunk_object = [chunk for chunk in doc.noun_chunks if chunk.text == my_chunk[c]][0]
            if 'of' in [c.text for c in my_chunk_object.root.rights]:
                ofobject = [c for c in my_chunk_object.root.rights if c.text == 'of'][0]
                head += [[r.text for r in ofobject.rights if r.dep_ == 'pobj'][0]]
            else:
                head += [my_chunk_object.root.text]
        if head:
          return head[0]
        else:
          return ''
    else:      
        return '' 

def checkRootPOS(phrase):
  doc = nlp(phrase)
  pos = [token.pos_ for token in doc if token.dep_ == 'ROOT']
  if pos:
    return pos[0]
  else:
    return ''

def findRoot(phrase):
  doc = nlp(phrase)  
  root = [token.text for token in doc if token.dep_ == 'ROOT']
  if root:
    root = root[0]
  return root

def get_subject_phrase(sentence):
    doc = spacyObject(sentence)
    for token in doc:
        if ("subj" in token.dep_):
            subtree = list(token.subtree)
            start = subtree[0].i
            end = subtree[-1].i + 1
            return doc[start:end]


def getSubsumedPobj(np_obj):    
    prep_object = [c for c in np_obj.children if c.dep_ == 'prep'][0]
    pobj = list(prep_object.rights)[0]
    pp_np = []
    for pd in pobj.subtree:
        assert pobj is pd or pobj.is_ancestor(pd)
        pp_np += [pd.text]
    return ' '.join(pp_np)

def getNPPobj(doc, np):
    out = []
    if [token for token in doc if token.head == token]:
      root = [token for token in doc if token.head == token][0]
      
      if list(root.lefts):
        subject = list(root.lefts)[0]
        subject_text = []   
        for descendant in subject.subtree:
          assert subject is descendant or subject.is_ancestor(descendant)
          subject_text += [descendant.text]
        if ' '.join(subject_text) == np and 'prep' in [c.dep_ for c in subject.children]:
            pobjtext = getSubsumedPobj(subject)
            out += [(subject.text, pobjtext)] 
      
      rights = list(root.rights)      
      if rights:
        rights = [r for r in rights if r.dep_ != 'punct']      
        all_rights = [[] for _ in range(len(rights))]
        for i in range(len(rights)):
            right = rights[i]    
            for d in right.subtree:
                assert right is d or right.is_ancestor(d)
                all_rights[i] += [d.text]
            if ' '.join(all_rights[i]) == np and 'prep' in [c.dep_ for c in right.children]:
                pobjtext = getSubsumedPobj(right)
                out += [(right.text, pobjtext)]        
    return out           

def isVerb(word):
    from nltk.corpus import wordnet as wn
    try:
        if wn.synsets(word, pos=wn.VERB):
            return True
    except LookupError:
            return False    
    return False     


if __name__ == '__main__':
    # token = input('token: ')
    # clause = input('clause in which token in used: ')
    clause = 'The bottom layers of sediment become compacted by this pressure.'
    np = 'The bottom layers of sediment'
    pp = 'by this pressure'

    clause = 'The generator converts mechanical energy into electrical energy.'
    np = 'the generator'

    clause = 'Martha carved the piece of wood into a toy at her bedroom.'
    np = 'at her bedroom'

    clause = 'A fuel goes into the generator.'
    np = 'into the generator.'

    clause = 'The stone is in the volcano.'
    np = 'in the volcano'

    clause = 'The stone is upstairs.'
    np = 'upstairs'

    clause = 'cook in the center of the oven , 35 to 40 mins , untill golden .'
    pp = 'in the center of the oven'

    clause = 'you should place the onion , garlic , and sambal in a mortar and pestle and pound to a smooth paste .' 
    pp = 'in a mortar and'
    # doc = spacyObject(clause)    
    # print([x.pos_ for x in doc if x.text == np])
    # print(isVerb(np))    
    doc2 = nlp2(clause)


    
    # clause = 'My mother weaved me a shawl at her workplace.'
    # np = 'at her workplace'
    # print(lemmatize(token, clause))
    # print(getNPhead(clause, np))
    # print(getPPnominalHead(clause, np))
    # print(checkRootPOS(np))
    # print(findRoot(np))
    # print('test passed!')
    # print(getPPnominalHead(clause, pp))
    # print(token_lemmatize('mortar'))
    # print(isVerb('mortar'))
