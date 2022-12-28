
# host = 'cn'
from from_spacy import token_lemmatize
import pickle
import os


#host = 'aws' or 'cn' or 'csv'
cn_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'CN')
cn_dir = '/data/ghazaleh/datasets/knowledge_pickles/'
with open(os.path.join(cn_dir, 'isa.pickle'), 'rb') as rf:
    isadict = pickle.load(rf)
with open(os.path.join(cn_dir, 'synonym.pickle'), 'rb') as rf:
    syndict = pickle.load(rf)   



def findserver(hostname):
  if hostname == 'cn':
    return 'http://api.conceptnet.io/c/en/'
  elif hostname == 'aws': 
    return 'http://172.31.2.195/c/en/'
  elif hostname == 'csv':
    return '/data/ghazaleh/neuralsymbolic/cn/ConceptNet.csv'

def getCNobject(term):
  import requests
  hostname = 'csv'
  prefix = findserver(hostname)
  if prefix.startswith('http'):
    suffix = '?offset=0&limit=2000'
    address = prefix + term + suffix
    obj = requests.get(address).json()  
    return obj
  else:
    fin = open(prefix, 'r', encoding="utf8")
    lines = fin.readlines()
    keep = []
    for line in lines:
      ls = line.split('\t')
      if ls[1] == term or ls[2] == term:
        keep += [(ls[0], ls[1], ls[2])]
    fin.close()
    return keep

# def findParentsByLabel(term):  
#   import re
#   if ' ' in term:
#     term2 = re.sub(' ', '_', term)
#   else:
#     term2 = term
#   obj = getCNobject(term2)
#   if type(obj) == list:
#     return [triple[2] for triple in obj if triple[0] == 'isa' and triple[1] == term]    
#   if '@id' not in obj.keys() or not obj['@id']:
#     return []
#   return [edge['end']['label'] for edge in obj['edges'] if edge['rel']['label'] == 'IsA' and edge['start']['label'] == term]

def findParentsByLabel(term):  
  return set(isadict[term])

def findParentsRecursive(phrase, stopterms = None, verbose=False):
  all_parents = set()
  traced = [phrase]
  really_traced = []
  if stopterms:  
    while traced and not [k for k in stopterms if k in all_parents]:
      i = 0      
      while len(traced) > i and traced[i] not in really_traced and not [k for k in stopterms if k in all_parents]:        
        term = traced.pop(i)
        x = findParentsByLabel(term)
        really_traced += [term]
        i += 1
        y = [i for i in set(x) if i not in traced]
        traced += y
        all_parents.update(set(y))
        if verbose:
          print(all_parents)
    return all_parents
  else:
    while traced:
      if verbose:
        print(traced)
      term = traced.pop(0)
      x = findParentsByLabel(term)
      # y = list(set(traced).union(set(x)))
      y = [i for i in x if i not in traced]
      traced += y
      all_parents.update(set(y))
    return all_parents

def isLocative(phrase):  
  x = findParentsRecursive(phrase, ['spatial_thing', 'location'])
  return 'spatial_thing' in x or 'location' in x

def isTangible(phrase):
  phrase = token_lemmatize(phrase)
  x = findParentsRecursive(phrase, ['tangible thing', 'finite spatial thing'])
  return 'tangible thing' in x or 'finite spatial thing' in x

def findRelatedTerms(term):
  import requests, re
  # prefix = findserver('aws')
  # # prefix = 'http://api.conceptnet.io/c/en/'
  # suffix = '?offset=0&limit=2000'
  if ' ' in term:
    term2 = re.sub(' ', '_', term)
  else:
    term2 = term
  # address = prefix + term2 + suffix
  # obj = requests.get(address).json()
  obj = getCNobject(term2)
  # related = set([edge['end']['label'] for edge in obj['edges'] if edge['rel']['label'] == 'RelatedTo' and edge['start']['label'] == term]).union(set([edge['start']['label'] for edge in obj['edges'] if edge['rel']['label'] == 'RelatedTo' and edge['end']['label'] == term]))
  rels = set()  
  if '@id' not in obj.keys() or not obj['@id']:
    return rels
  for edge in obj['edges']:
    if edge['rel']['label'] == 'RelatedTo':
      id_list = edge['@id'].split('/c/en/')[1:]
      if len(id_list) > 1:
        keep = [re.sub(r'[\W_]+$', '', s) for s in id_list]
        rels.update([x.split('/')[0] for x in keep if x != term2])
  return rels



# def ablative_allative(term):
#   ablative_terms = ['out', 'away', 'exit', 'leave']
#   allative_terms = ['go', 'come', 'join']
#   related = findRelatedTerms(term)
#   if [x for x in allative_terms if x in related]:
#     return 'to'
#   elif [x for x in ablative_terms if x in related]:
#     return 'from'
#   else:
#     return None  

# def findSynonyms(term):
#   import re # requests
#   # prefix = findserver('aws')
#   # # prefix = 'http://api.conceptnet.io/c/en/'
#   # suffix = '?offset=0&limit=2000'
#   if ' ' in term:
#     term2 = re.sub(' ', '_', term)
#   else:
#     term2 = term
#   # address = prefix + term2 + suffix
#   # obj = requests.get(address).json()
#   obj = getCNobject(term2)
#   if '@id' not in obj.keys() or not obj['@id']:
#     # this prevents crashing if the server is down. you can avoid also crashing by running a local copy (on AWS)
#     return set()
#   # related = set([edge['end']['label'] for edge in obj['edges'] if edge['rel']['label'] == 'RelatedTo' and edge['start']['label'] == term]).union(set([edge['start']['label'] for edge in obj['edges'] if edge['rel']['label'] == 'RelatedTo' and edge['end']['label'] == term]))
#   syns = set()  
#   for edge in obj['edges']:
#     if edge['rel']['label'] == 'Synonym':
#       id_list = edge['@id'].split('/c/en/')[1:]
#       if len(id_list) > 1:
#         keep = [re.sub(r'[\W_]+$', '', s) for s in id_list]
#         syns.update([x.split('/')[0] for x in keep if x != term2])
#   return syns

def findSynonyms(term):
  return set(syndict[term])



if __name__ == '__main__':
  # print(findSynonyms('electrical energy'))
  # print(findParentsByLabel('plant'))
  print(isLocative('underground'))
  # print(findParentsByLabel('underground'))
  # print(findParentsRecursive('underground', ['spatial_thing', 'location']))
  # print(getCNobject('plant'))