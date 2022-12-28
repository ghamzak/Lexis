"""
1. SemParse is able to parse only sentences shorter than 256 characters.
2. Some punctuation characters such as ( [ ] ) are not parsable. 
3. 
"""
import re

def clean(sentence):
    x = re.sub(r'●', ' ', sentence.strip())
    assert type(x) == str
    x = re.sub(r'\(|\)|\[|\]', '-', x)
    assert type(x) == str    
    x = re.sub(r'\s\s+', ' ', x)
    assert type(x) == str    
    return x

def preprocess(sentenceList):
    return [clean(t) for t in sentenceList if len(clean(t)) <= 256]

def generateParserCommand(sentence):
    if type(sentence) == str:
        sentence = clean(sentence)
        assert type(sentence) == str
        if len(sentence) <= 256:
            x1 = "curl -s localhost:8080/predict/semantics?utterance="
            x2 = re.sub(r'\s', '%20', sentence)
            x3 = " | python -m json.tool"
            return x1 + x2 + x3
    elif type(sentence) == list:
        outlist = [generateParserCommand(s) for s in preprocess(sentence)]
        return outlist

if __name__ == '__main__':
    s = 'More chemical changes happen and the buried material becomes oil.'
    