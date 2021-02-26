## begin license ##
#
# "Meresco Harvester" consists of two subsystems, namely an OAI-harvester and
# a web-control panel.
# "Meresco Harvester" is originally called "Sahara" and was developed for
# SURFnet by:
# Seek You Too B.V. (CQ2) http://www.cq2.nl
#
# Copyright (C) 2015, 2017, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
#
# This file is part of "Meresco Harvester"
#
# "Meresco Harvester" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Harvester" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Harvester"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from weightless.core import NoneOfTheObserversRespond
from meresco.core import Observable
from meresco.components.http.utils import okJson
from meresco.components.json import JsonDict


class HarvesterDataRetrieve(Observable):
    paths = ['/dataset', '/get']

    #path, query, fragments, arguments
    def handleRequest(self, arguments, path=None, **kwargs):
        if path and path.startswith('/dataset'):
            yield self.handlePublicData(arguments, path, **kwargs)
            return
        yield okJson
        verb = arguments.get('verb', [None])[0]
        messageKwargs = dict((k,values[0]) for k,values in list(arguments.items()) if k != 'verb')
        request = dict(**messageKwargs)
        message = None
        if verb is not None:
            message = verb[0].lower() + verb[1:]
            request['verb'] = verb
        response = JsonDict(request=request)
        try:
            if message is None:
                raise ValueError('badVerb')
            if not message.startswith('get'):
                raise ValueError('badVerb')
            response['response']={
                    verb: self.call.unknown(message=message, **messageKwargs)
                }
        except NoneOfTheObserversRespond:
            response['error'] = error('badVerb')
        except Exception as e:
            response['error'] = error(str(e), repr(e))
        yield response.dumps()

    def handlePublicData(self, arguments, path, **kwargs):
        """
        Context: resolvable URI like: http://data.digitalecollectie.nl/dataset/natag/DiMCoN/dimcon_museum_amsterdam
        Paths have form:
          /dataset/domain/repositorygroup/repository which return the LASTEST or
          /dataset/<uuid> which returns a specific version
        IMPL NOTES:
         1. alle data in een dir data/<uuid>.json schrijven (ivm lookup)
         2. laatste versie in <domain>.<repositoryid>.repository is een (symbolic) link
        """
        yield okJson
        subpaths = path.split('/')
        if len(subpaths) == 5:
            _, dataset, domain, repositorygroup, repository = subpaths
            yield toJsonLd(
                    toSchema(
                        self.call.getRepository(repository, domain)))
        elif len(subpaths) == 3:
            _, public, uuid = subpaths
            yield toJsonLd(
                    toSchema(
                        self.call.getPublicRecord(uuid)))
        else:
            yield 'bugger'


messages = {
    'badDomain': 'The domain does not exist.',
    'badVerb': 'Value of the verb argument is not a legal verb, the verb argument is missing, or the verb argument is repeated.',
    'badArgument': 'The request includes illegal arguments, is missing required arguments, includes a repeated argument, or values for arguments have an illegal syntax.',
    'idDoesNotExist': 'The value of an argument (id or key) is unknown or illegal.'
}

def error(code, alternative=None):
    message = messages.get(code)
    if message is None:
        return {'code': 'unknown', 'message': alternative or code}
    return {'code':code, 'message': message}


def toSchema(d):
    e = d.get('extra', {})
    return {
        '@type': 'http://schema.org/Dataset',
        '@id': d.get('@id'),
        'http://schema.org/isBasedOn': d.get('@base'),
        'http://schema.org/identifier' :d.get('identifier'),
        'http://schema.org/name': e.get('name'),
        'http://schema.org/creator': e.get('creator'),
        'http://schema.org/publisher': e.get('publisher'),
        'http://schema.org/license': e.get('license'),
        'http://schema.org/description': e.get('description'),
        }

def toJsonLd(d):
    # copied from NDECatalogTest.... @TODO make a lib from from it??
    from pyld import jsonld
    import json
    return json.dumps(jsonld.compact(d, ctx={'@vocab': 'http://schema.org/'}), indent=2)
