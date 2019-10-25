
"""Search the question and one given option.

The module searches the question and one option; it then tries to count the number of matches.
"""

import json
import io
import urllib.request as urllib2
import urllib.parse as urllib
from bs4 import BeautifulSoup
import googlesearch
import re
import modules.mydecorators as mydecorators
import gzip
import os
import time
from babelpy.babelfy import BabelfyClient
import requests
import multiprocessing
from multiprocessing import Process, Manager, sharedctypes

# list of words to clean from the question during google search
remove_words   = json.loads(io.open("Data/settings.json", encoding="utf-8").read())["remove_words"]

# negative words
negative_words = json.loads(io.open("Data/settings.json", encoding="utf-8").read())["negative_words"]

# negative words
no_end_char    = r'[!@#$?:,;]'

# wikipedia url
wiki_url       = r'(https:\/\/|http:\/\/)([a-z]*.wikipedia.org)'

# No Score
NO_SCORE       = 969696 

class ParsedQuestion:
    """Holding some elements extracted from the question"""
    def __init__(self, originalq, proper_nouns, simplyfiedq):
        self.original = originalq
        self.proper_nouns = proper_nouns
        self.simplyfied = simplyfiedq

    def __str__(self):
        return "simplyfied:{}\nproper_nouns:{}".format(self.simplyfied, self.proper_nouns)

class Searcher(object):
    def __init__(self, manager: Manager):
        self._manager = manager

    def simplify(self):
        pass

    @mydecorators.handle_exceptions
    @mydecorators.timeit("googlesearch")
    def search(self, sim_ques: ParsedQuestion, option, neg, tmax=3):
        """Searches the question and the single option on google and wikipedia.
        sim_ques must be a ParsedQuestion object.
        """
        
        return_dict = self._manager.dict()
        h = str(time.time())
        print("Searching ..." + sim_ques.original + "?  " + option)
        tasks = []
        proc = Process(target=google_from_options, args=(h, sim_ques, option, neg, tmax, return_dict))
        proc.start()
        tasks.append(proc)

        #google_results_number(sim_ques, option)
        
        for t in tasks:
            t.join()

        print(return_dict)
        return return_dict[h]

def simplify_ques(question):
    """Simplify question and remove the words in the setting.json"""

    question = re.sub(no_end_char, '', question)
    splitted_question = question.split()
    # this line should remove the first words like 'Quale' 'Chi' 'In'
    splitted_question = splitted_question[1:] if splitted_question[0].lower() in remove_words else splitted_question


    splitted_question = [word for word in splitted_question if word != 'NON']

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
    
    cleanwords = []
    for word in qwords:
        if word not in remove_words:
            temp = re.match(r'["([^|\'](\w+)[")\]^|\']', word)
            #temp = re.findall('"([^"]*)"', word)
            if temp:
                cleanwords.append(temp.group(1))
            else:
                cleanwords.append(word)
        
    #cleanwords = [re.findall('"([^"]*)"', word) | word for word in qwords if word not in remove_words]
    #cleanwords = re.findall() ('"([^"]*)"', " ".join(cleanwords))

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
	'lang' : 'IT',
    'th': '.0',
    'match': 'PARTIAL_MATCHING'
    }

    babel_client = BabelfyClient(os.environ['BABEL'], params)
    # Babelfy sentence.
    babel_client.babelfy(question)

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

def simplify_ques_fy2(question):
    
    params = {
    'lang' : 'IT',
    'th'   : '.0',
    'match': 'PARTIAL_MATCHING'
    }
    simpl_ques = list()
    senses = list()
    check_synset = list()
    neg = False

    babel_client = BabelfyClient(os.environ['BABEL'], params)

    # check if the question is a negative one
    splitted_question = question.split()
    for w in splitted_question:
        if w.lower() in negative_words:
            neg = True
            splitted_question.remove(w)
            break

    # Babelfy sentence.
    question = " ".join(splitted_question)
    babel_client.babelfy(" ".join(splitted_question))

    proper_nouns = re.findall('"([^"]*)"', " ".join(splitted_question).lower())

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

    for bcme in babel_client.merged_entities:
        simpl_ques.append(bcme['text'].lower())
        check_synset.append(bcme['babelSynsetID'])

    for bid in check_synset:
        if bid[-1] == 'n':
            params = {
                'id' : bid,
                'targetLang' : 'IT',
                'key'  : os.environ['BABEL']
            }
            ris = babelAPI(params).lower()
            if ris not in senses and ris not in simpl_ques and ris not in remove_words:
                senses.append(ris)

    for pn in proper_nouns:
        if pn not in senses:
            senses.append(pn)  

    return ParsedQuestion(question, senses, simpl_ques), neg

# get web page
def get_page(link):
    print("link:{}".format(link))
    try:
        #if link.find('mailto') != -1:
        #    return ''
        req = urllib2.Request(link, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'})
        html = urllib2.urlopen(req).read()
        return html
    # TODO have a better exception handing here
    except (urllib2.URLError, urllib2.HTTPError, ValueError) or Exception as e:
        print(e)
        return ''

#@mydecorators.timeit("actualsearch")
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
    soup = BeautifulSoup(content, "lxml").text
    page = soup.lower()

    for word in words:
        points = points + page.count(word.lower())
    for pn in sim_ques.proper_nouns:
        points = points + page.count(pn.lower()) * 5

    return points

def google_results_number(i, sim_ques, option, ret_arr):
    re_val = r'[a-zA-Z ]+(\d+|\d+.\d+)[ a-zA-Z]+'
    query = " ".join(sim_ques.original.split() + option.split())
    par={'q': query}
    par_url = urllib.urlencode(par)

    USER_AGENT = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
    req = requests.get('https://www.google.com/search?{}'.format(par_url), headers=USER_AGENT)
    soup = BeautifulSoup(req.text, 'lxml')
    response = soup.find('div', {'id': 'resultStats'})
    if response:
        pr = re.match(re_val, response.text)
        if pr:
            res = int(re.sub('[.,]','',pr.group(1)))
            ret_arr[i] = res
            return res
    
    ret_arr[i] = -NO_SCORE
    return -NO_SCORE


def google_from_options(h, sim_ques, option, tmax, return_dict):
    ts = time.time()
    # removing the first word like 'Il' 'Una' ...
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
    search_wiki = search(searched_option) # generator

    for sw in search_wiki:
        # scan for wikipedia url
        if re.match(wiki_url, sw):
            search_w = sw
            break
        elif (time.time()-ts) > tmax:
            print("No Link Found")
            break

    if not search_w:
        # maxint was removed
        # not so clear
        print("searched: {}".format(searched_option))
        return_dict[h] = -NO_SCORE
    else:
        points = get_score(search_w, words, sim_ques)
        return_dict[h] = points
        #return points if not neg else -points
    
    return return_dict[h]

@mydecorators.handle_exceptions
@mydecorators.timeit("googlesearch")
def google_wiki(sim_ques, option, neg, tmax=4):

    """Searches the question and the single option on google and wikipedia.
    sim_ques must be a ParsedQuestion object.
    """
    ret_arr = multiprocessing.Array('i', 3)
    print("Searching ... {}  {}".format(sim_ques.original, option))
    tasks = []

    # google_from_options(Wikipedia)
    proc = Process(target=google_from_options, args=(0, sim_ques, option, tmax, ret_arr))
    proc.start()
    tasks.append(proc)
    #google_from_options(0, sim_ques, option, ret_arr)


    proc = Process(target=google_results_number, args=(1, sim_ques, option, ret_arr))
    proc.start()
    tasks.append(proc)
    #google_results_number(1, sim_ques, option, ret_arr)
    
    for t in tasks:
        t.join()

    return ret_arr