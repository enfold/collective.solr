from logging import getLogger
from zope.interface import implements
from zope.component import queryUtility
from re import compile

from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISearch

logger = getLogger('collective.solr.search')


word = compile('^\w+$')
special = compile('([-+&|!(){}[\]^"~*?\\:])')

def quote(term):
    """ quote a given term according to the solr/lucene query syntax;
        see http://lucene.apache.org/java/docs/queryparsersyntax.html """
    if isinstance(term, unicode):
        term = term.encode('utf-8')
    if term.startswith('"') and term.endswith('"'):
        term = term[1:-1]
    elif not word.match(term):
        term = '"%s"' % special.sub(r'\\\1', term)
    return term


class Search(object):
    """ a search utility for solr """
    implements(ISearch)

    def __init__(self):
        self.manager = queryUtility(ISolrConnectionManager)

    def search(self, **query):
        """ perform a search with the given parameters """
        pass

    def buildQuery(self, default=None, **args):
        """ helper to build a querystring for simple use-cases """
        schema = self.manager.getSchema() or {}
        args[None] = default
        query = []
        for name, value in args.items():
            field = schema.get(name or schema.defaultSearchField, None)
            if field is None or not field.indexed:
                continue
            if isinstance(value, (tuple, list)):
                quoted = False
                value = '(%s)' % ' '.join(map(quote, value))
            elif isinstance(value, basestring):
                quoted = value.startswith('"') and value.endswith('"')
                value = quote(value)
            else:
                continue
            if name is None:
                if not quoted:      # don't prefix when value was quoted...
                    value = '+%s' % value
                query.append(value)
            else:
                query.append('+%s:%s' % (name, value))
        return ' '.join(query)
