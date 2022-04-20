from habanero import Crossref
import pickle
import os
import bibtexparser
from bibtexparser.bparser import BibTexParser
import base64

IDENTIFIER = 'Identifier'
DOI = 'DOI'
TITLE = 'Title'
AUTHORS = 'Authors'
PUBLISHED = 'Published'
PUBLISHED_IN = 'Published_In'

def get_backward_references(entry):
    doi = entry[DOI]
    identifier = entry[IDENTIFIER]

    filename = 'crossref-cache/' + identifier
    if os.path.exists(filename):
        # print('loading ' + identifier + ' from cache')
        with open(filename, 'rb') as f:
            response = pickle.load(f)
    else:
        cr = Crossref()
        try:
            response = cr.works(ids = doi)
            with open(filename, 'wb') as f:
                pickle.dump(response, f)
        except:
            # print("An exception occurred: " + identifier + ' - ' + doi)
            response = None

    if response is None:
        return None

    message = response['message']
    if 'reference' not in message:
        # print('no reference: ' + identifier + ' - ' + doi)
        return None

    references = message['reference']

    references_with_doi = filter(lambda r: 'DOI' in r, references)
    reference_dois = list(map(lambda r: r['DOI'], references_with_doi))

    references_without_doi = list(filter(lambda r: 'DOI' not in r, references))

    return {
        'dois': reference_dois,
        'non_dois': references_without_doi
    }


def get_by_doi(doi):
    if (doi is None):
        return None
    filename = 'crossref-cache/doi/' + str(base64.b64encode(doi.encode('utf-8')))
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            response = pickle.load(f)
    else:
        cr = Crossref()
        try:
            response = cr.works(ids = doi)
            with open(filename, 'wb') as f:
                pickle.dump(response, f)
        except:
            # print("An exception occurred: " + doi)
            return None
    message = response['message']
    authors_obj = message.get('author', [])
    authors = list(map(lambda a: ' '.join([a.get('given', ''), a.get('familiy', '')]).strip(), authors_obj))
    date_parts = message.get('published', {}).get('date-parts', [[]])[0]
    published_in = message.get('container-title', [])

    return {
        TITLE: ', '.join(message.get('title', [])),
        AUTHORS: ', '.join(authors),
        PUBLISHED: '-'.join(list(map(str, date_parts))),
        DOI: doi,
        PUBLISHED_IN: ', '.join(published_in)
    }

def add_reference_by(entry, referenced_by):
    entry['referenced_by']=referenced_by
    return entry

def read_bib_file(root, file):
    path = os.path.join(root, file)
    name = file.replace(".bib", "")
    with open(path) as bibtex_file:
        parser = BibTexParser()
        parser.ignore_nonstandard_types = False
        bib_database = bibtexparser.load(bibtex_file, parser)
        # print('loaded ' + str(len(bib_database.entries)) + ' bib-entries for ' + file)
    return list(map(lambda x: add_reference_by(x, name), bib_database.entries))
