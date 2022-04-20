from habanero import Crossref
import Levenshtein
import re
from scholarly import scholarly, ProxyGenerator
import pickle
import os
import base64
from lib.backward import PUBLISHED_IN, get_by_doi

TEMP = 'temp'

def drop_duplicates_normalized(result_pd, column):
    result_pd[TEMP] = result_pd[column].str.lower()
    result_pd[TEMP] = result_pd[TEMP].str.strip()
    result_pd[TEMP] = result_pd[TEMP].str.replace(r'[^a-zA-Z0-9]', '', regex=True)
    result_pd.drop_duplicates(subset=[TEMP], inplace=True, keep='last')
    result_pd.drop(columns = TEMP, inplace = True)

def normalize_text(text):
    text_small = text.lower().strip()
    return re.sub(r'[^a-zA-Z0-9]', '', text_small)

def resolve_doi(name): 
    filename = 'doi-cache/' + str(base64.b32encode(name.encode()))[:250]
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)

    cr = Crossref()
    result = cr.works(query=name)
    items = result['message']['items']
    if (len(items) <= 0):
        return None
    item = items[0]
    if ('title' not in item):
        return None
    title = item['title'][0]
    ratio = Levenshtein.ratio(normalize_text(title), normalize_text(name))
    if (ratio < 0.95):
        with open(filename, 'wb') as f:
            pickle.dump(None, f)
        return None
    doi = item['DOI']

    with open(filename, 'wb') as f:
        pickle.dump(doi, f)

    return item['DOI']

def get_abstract(doi):
    if (doi is None):
        return None
    pg = ProxyGenerator()
    pg.Tor_Internal(tor_cmd = "tor")
    scholarly.use_proxy(pg)
    #scholarly.use_proxy(None)
    search_query = scholarly.search_pubs(doi)
    pub = scholarly.fill(next(search_query))
    return pub['bib']['abstract']

def get_published_in(title):
    doi = resolve_doi(title)
    if (doi is None):
        return None
    data = get_by_doi(doi)
    if (data is None):
        return None
    return data[PUBLISHED_IN]