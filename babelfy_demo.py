#from modules.pybabelfy.pybabelfy.babelfy import *
import os
from babelpy.babelfy import BabelfyClient

# Instantiate BabelFy client.
params = dict()
params['lang'] = 'IT'
params['th'] = '.0'
params['match'] = 'PARTIAL_MATCHING'
babel_client = BabelfyClient(os.environ['BABEL'], params)

# Babelfy sentence.
babel_client.babelfy("Chi tra i seguenti non e un nano di 'Biancaneve'")

# Get entity data.
print(babel_client.entities)
print('\n')
# Get entity and non-entity data.
print(babel_client.all_entities)
print('\n')
# Get merged entities only.
print(babel_client.merged_entities)
print('\n')
# Get all merged entities.
babel_client.all_merged_entities

"""
def frag(semantic_annotation, input_text):
    start = semantic_annotation.char_fragment_start()
    end = semantic_annotation.char_fragment_end()
    return input_text[start:end+1]

text= u"Chi tra i seguenti non e un nano di Biancaneve"
lang = "IT"
key = os.environ['BABEL'] #This only works for the demo example. Change for the key you get once registered

babelapi = Babelfy()

semantic_annotations = babelapi.disambiguate(text,lang,key, anntype=AnnTypeValues.ALL, match=MatchValues.PARTIAL_MATCHING)
for semantic_annotation in semantic_annotations:
    print(frag(semantic_annotation,text))
    semantic_annotation.pprint()
"""
