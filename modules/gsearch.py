
"""Search the question and one given option.

The module searches the question and one option; it then tries to count the number of matches.

TODO improve the accuracy of the search
"""

import json
import io
import urllib.request as urllib2
import urllib.parse as urllib
from bs4 import BeautifulSoup
import googlesearch
import re
import modules.mydecorators as mydecorators
import sys
import gzip
import os

# list of words to clean from the question during google search
remove_words   = json.loads(open("Data/settings.json").read())["remove_words"]

# negative words
negative_words = json.loads(open("Data/settings.json").read())["negative_words"]

# negative words
no_end_char    = r'[!@#$?:,;]'

class ParsedQuestion:
    """Holding some elements extracted from the question"""
    def __init__(self, originalq, proper_nouns, simplyfiedq):
        self.original = originalq
        self.proper_nouns = proper_nouns
        self.simplyfied = simplyfiedq

    def __str__(self):
        return "simplyfied:{}\nproper_nouns:{}".format(self.simplyfied, self.proper_nouns)
        #string = '-'.join(self.proper_nouns) + '\n' + '-'.join(self.simplyfied)
        #return string


def simplify_ques(question):
    """Simplify question and remove the words in the setting.json"""

    question = question.strip('?')
    splitted_question = question.split()
    # this line should remove the first words like 'Quale' 'Chi' 'In'
    splitted_question = splitted_question[1:] if splitted_question[0].lower() in remove_words else splitted_question

    # proper noun is a list with elements like "Marco Rossi" or "Title of a Song" or "GPRS"
    # this line catches element between quotes
    proper_nouns = re.findall('"([^"]*)"', " ".join(splitted_question))
    for i, _ in enumerate(splitted_question):
        # check for acronyms "NBA"
        if splitted_question[i].isupper():
            proper_nouns.append(splitted_question[i])
            continue
        # if two subsequent words has the first letter uppercased they probably refers to a proper noun
        try:
            if splitted_question[i][0].isupper() and splitted_question[i + 1][0].isupper():
                proper_nouns.append(splitted_question[i] + " " + splitted_question[i + 1])
        except IndexError:
            pass

    qwords = question.lower().split()
    # check if the question is a negative one
    neg = False
    for w in qwords:
        if w in negative_words:
            neg = True
            break

    cleanwords = [word for word in qwords if word not in remove_words]

    return ParsedQuestion(question, proper_nouns, " ".join(cleanwords)), neg

@mydecorators.handle_exceptions
def babelfyAPI(params):
    service_url = 'https://babelfy.io/v1/disambiguate'

    url = service_url + '?' + urllib.urlencode(params)
    request = urllib2.Request(url)
    request.add_header('Accept-encoding', 'gzip')
    response = urllib2.urlopen(request)

    buf = io.BytesIO( response.read())
    f = gzip.GzipFile(fileobj=buf)
    return json.loads(f.read())

@mydecorators.handle_exceptions
def babelAPI(params):
    service_url = 'https://babelnet.io/v5/getSynset'

    url = service_url + '?' + urllib.urlencode(params)
    request = urllib2.Request(url)
    request.add_header('Accept-encoding', 'gzip')
    response = urllib2.urlopen(request)

    if response.info().get('Content-Encoding') == 'gzip':
        buf = io.BytesIO( response.read())
        f = gzip.GzipFile(fileobj=buf)
        data = json.loads(f.read())
        
        # retrieving BabelSense data
        senses = data['senses']
        lemma = senses[0]['properties'].get('simpleLemma')
        return " ".join(lemma.split('_'))
        #for result in senses:
        #    lemma = result['properties'].get('simpleLemma')
        #    language = result['properties'].get('language')
        #    print(language.encode('utf-8') + "\t" + str(lemma.encode('utf-8')))

def simplify_ques_fy(question):
    
    params = {
	'text' : question,
	'lang' : 'IT',
	'key'  : os.environ['BABEL']
    }

    data = babelfyAPI(params)
    question = re.sub(no_end_char, '', question)
    splitted_question = question.split()
    simplfy_ques = []
    for result in data:
        for token in splitted_question[result['tokenFragment']['start']:result['tokenFragment']['end']+1]:
            if token not in simplfy_ques and token not in remove_words:
                simplfy_ques.append(token)

    #squestion = " ".join(simplfy_ques)
    #params['text'] = squestion
    params['match'] = 'PARTIAL_MATCHING'
    data = babelfyAPI(params)

    qwords = question.lower().split()
    # check if the question is a negative one
    neg = False
    for w in qwords:
        if w in negative_words:
            neg = True
            break
    
    for w in negative_words:
        if w in splitted_question:
            splitted_question.remove(w)

    rank_dict        = {}
    simply_rank_dict = {}
    simply_rank_list = []
    check_synset     = []
    senses           = []

    for i, _ in enumerate(splitted_question):
        # if two subsequent words has the first letter uppercased they probably refers to a proper noun
        try:
            if splitted_question[i][0].isupper() and splitted_question[i + 1][0].isupper():
                senses.append(splitted_question[i] + " " + splitted_question[i + 1])
        except IndexError:
            pass

    for result in data:
        result['score'] += result['coherenceScore']
        result['score'] += result['globalScore']
        for i in range(result['tokenFragment']['start'],result['tokenFragment']['end']+1):
            rank_dict.setdefault(i, []).append(result)
    
    for i in rank_dict:
        best = None
        for j, result in enumerate(rank_dict[i]):
            if best is None:
                best = result
            else:
                if result['score'] > best['score']:
                    best = result
        
        if best['babelSynsetID'] not in simply_rank_dict:
            simply_rank_dict[best['babelSynsetID']] = best
            check_synset.append(best['babelSynsetID'])
            els = " ".join(splitted_question[best['tokenFragment']['start']:best['tokenFragment']['end']+1])
            if els not in senses and els not in remove_words:
                senses.append(els)

    for bid in check_synset:
        if bid[-1] == 'n':
            params = {
                'id' : bid,
                'targetLang' : 'IT',
                'key'  : os.environ['BABEL']
            }
            ris = babelAPI(params)
            if ris not in senses and ris not in remove_words:
                senses.append(ris)

    return ParsedQuestion(question, senses, simplfy_ques), neg
    
# get web page
def get_page(link):
    try:
        if link.find('mailto') != -1:
            return ''
        req = urllib2.Request(link, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'})
        html = urllib2.urlopen(req).read()
        return html
    # TODO have a better exception handing here
    except (urllib2.URLError, urllib2.HTTPError, ValueError) or Exception:
        return ''


@mydecorators.timeit("actualsearch")
def search(searched_option):
    # searched_option += ' wiki'
    # get google search results for option + 'wiki'
    try:
        ret = googlesearch.search(searched_option, num=10, lang="it", tld='it')
    except Exception as e:
        print(e)        
         
    return ret


def get_score(link, words, sim_ques):
    points = 0
    # TO DO filter the wiki page
    content = get_page(link)
    soup = BeautifulSoup(content, "lxml")
    page = soup.get_text().lower()

    for word in words:
        points = points + page.count(word.lower())
    for pn in sim_ques.proper_nouns:
        points = points + page.count(pn.lower()) * 5

    return points


@mydecorators.handle_exceptions
@mydecorators.timeit("googlesearch")
def google_wiki(sim_ques, option, neg):
    """Searches the question and the single option on google and wikipedia.

    sim_ques must be a ParsedQuestion object.
    """
    print("Searching ..." + sim_ques.original + "?  " + option)

    # removing the first word like 'Il' 'Una'
    option = option.split()
    option = option[1:] if option[0].lower() in remove_words else option
    option = " ".join(option)


    if isinstance(sim_ques.simplyfied, str):
        words = sim_ques.simplyfied.split()
    else:
        words = sim_ques.simplyfied
    
    # TODO force google to search for the exact match ??? using quotes
    searched_option = option.lower()
    
    search_w = None
    search_wiki = search(searched_option)

    for sw in search_wiki:
        search_w = sw
        print(search_w)
        break

    if not search_w:
        # maxint was removed
        # not so clear
        print("searched: {}".format(searched_option))
        print(search_wiki)
        return -sys.maxsize if not neg else sys.maxsize

    points = get_score(search_w, words, sim_ques)

    return points if not neg else -points