from scholarly import scholarly, ProxyGenerator
import pickle
import os
from random import uniform
import time
import logging

IDENTIFIER = 'Identifier'
DOI = 'DOI'

def set_scholarly_logging(enable_logging):
    if not enable_logging:
        return
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.FileHandler("scholarly.log")
    #handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.handlers = []
    root.addHandler(handler)


def get_forward_references(entry, retry=3):
    doi = entry[DOI]
    identifier = entry[IDENTIFIER]

    scholarly.use_proxy(None)

    filename = 'scholar-cache/' + identifier
    if os.path.exists(filename):
        #print('loading ' + identifier + ' from cache')
        with open(filename, 'rb') as f:
            return pickle.load(f)

    #print('loading ' + identifier + ' from scholar')
    try:
        #pg = ProxyGenerator()
        #pg.Tor_Internal(tor_cmd = "tor")
        #scholarly.use_proxy(pg)
        scholarly.use_proxy(None)
        search_query = scholarly.search_pubs(doi)
        time.sleep(uniform(1, 5))
        pub = scholarly.fill(next(search_query))
        if 'citedby_url' not in pub:
            print('Not cited: ' + identifier)
            result = []
        else:
            time.sleep(uniform(1, 5))
            result = list(scholarly.citedby(pub))
    except Exception as e:
        if retry <= 1:
            raise e
        print("fechting data failed, waiting and retry...")
        time.sleep(60)
        result = get_forward_references(entry, retry-1)
    with open(filename, 'wb') as f:
        pickle.dump(result, f)
    return result
