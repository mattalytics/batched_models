from __future__ import unicode_literals

import logging
from django.db import transaction
import math
from bulk_update.manager import BulkUpdateManager
import hashlib

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

class BulkManager(BulkUpdateManager):
    """
    Not production ready - further testing required.

    This module dramatically increases the speed of get_or_create and update_or_create operations by providing a
    batching functionality.

    Relies on the fine work of Aykut Ozat: https://github.com/aykut

    """
    def __init__(self, bulk_update_size=2000):
        super(BulkManager, self).__init__()
        self.bulk_update_size = bulk_update_size #size used by bulk_update_mgr

    class Bulk():
        def __init__(self, mgr):
            self._queries = [] #do not touch
            self.mgr = mgr
            self.bulk_update_size = mgr.bulk_update_size

        def get_or_create(self, defaults={}, **kwargs):
            self.validate_params(kwargs, 'get')

            self._queries.append({
                'search':kwargs,
                'defaults':defaults,
                'operation':'get'
            })

        def update_or_create(self, defaults={}, **kwargs):
            self.validate_params(kwargs, 'update')

            self._queries.append({
                'search':kwargs,
                'defaults':defaults,
                'operation':'update'
            })

        def validate_params(self, paramdict, operation):
            params = paramdict.keys()

            if not self._queries: #empty. anything goes
                return len(params)

            if operation != self._queries[0]['operation']:
                raise Exception('You cannot mix updates and gets')

            if not len(self._queries[0]['search']) == len(params): #check each entry against first one
                raise Exception('You introduced a mismatched parameter set into your batch.')

            if not len(set(params)) == len(params):
                raise Exception('Duplicate field names were detected in this entry')

            return len(params)


        def find_from_batch(self, batch_size=5000):
            """
            Goal is to find rows that match any of the queries we created in a safe, performant way.
            Returns:
                qset of matching rows
            """
            colmap = {f.get_attname_column()[0]:f.get_attname_column()[1].replace("'", "") #super paranoid escape of col name
                      for f in self.mgr.model._meta.fields
                      }

            fields = self.get_fields()
            results = []
            batch = 0
            total_batches = math.ceil(len(self._queries)/float(batch_size))
            """
            run the query in batches based on how many queries your server can handle
            more memory = larger batch size
            """
            while batch < total_batches:
                vals = []
                wherestr = " where "

                for q in self._queries[batch*batch_size:batch*batch_size+batch_size]:
                    search = q['search']
                    group = '('
                    for f in fields:
                        vals.append(search[f])
                        group += ' ' + colmap[f] + ' = %s and '

                    group = group.rstrip('and ') + ') or '
                    wherestr += group

                wherestr = wherestr.rstrip('or ')
                sql = 'select * from ' + self.mgr.model._meta.db_table + wherestr

                qset = self.mgr.model.objects.raw(
                    sql,
                    vals
                )

                logging.debug(qset.query)

                results.extend([r for r in qset])
                batch += 1


            return results

            """
            #This is possible and so much cleaner, but Q objects are too slow on large queries
            #if someone makes Q operations faster, this block will replace the code above

            filters = Q(**self._queries[0]['search'])

            for q in self._queries[1:]:
                q = q['search']
                filters = filters | Q(**q)
            return self.mgr.model.objects.filter(filters)
            """

        def run(self, batch_size=5000):
            if len(self._queries) == 0:
                raise Exception('Empty batch')

            operation = self._queries[0]['operation']

            logging.debug('generating queries')
            found = self.find_from_batch(batch_size=batch_size)
            matches = []
            new = []
            match_hash = self.match_hash()

            logging.debug('processing found')
            for f in found:
                match_string = self.match_orm(f)
                if match_string in match_hash:
                    matches.append(
                        self.make_model(match_hash[match_string], f)
                    )
                    del match_hash[match_string]

            logging.debug( 'processing leftovers, creating new recs' )
            for key,model in match_hash.iteritems():
                new.append(self.make_model(model))

            logging.debug("%s %s %s %s" % (len(new),'new',len(matches),'matches'))

            with transaction.atomic():
                if new:
                    logging.debug('bulk create')
                    self.mgr.model.objects.bulk_create(new)

                if matches and operation == 'update':
                    logging.debug('bulk update')
                    self.mgr.model.objects.bulk_update(matches, batch_size=self.bulk_update_size, update_fields=self.fields_to_update())
                else:
                    logging.debug('not performing update')

            if operation == 'get':
                return self.find_from_batch()
            else:
                #if you want to return results from an update, just call *find_from_batch()* manually
                return []

        def to_unicode(self, val):
            if type(val) == str:
                return unicode(val, 'utf-8').encode('utf-8')

            return unicode(val).decode('utf-8').encode('utf-8')

        def match_hash(self):
            """
            We use hashes here to avoid massive slowdown when performing lookups on large datasets
            Returns:
                dict of hashes in a simple querystring format
            """
            matches = {}
            for query in self._queries:
                q = query['search']
                key = ''
                for k in sorted(q.keys()):
                    sval = self.to_unicode(q[k])
                    escaped_val = hashlib.sha1(sval).hexdigest()
                    key += k + ':' + escaped_val + '&'

                matches[key[:-1]] = query

            return matches

        def match_orm(self, record):
            """
            We use hashes here to avoid massive slowdown when performing lookups on large datasets
            Returns:
                true or false if the orm record is already in the match hash
            """
            ormkey = ''

            for k in sorted(self.get_fields()):
                sval = self.to_unicode(getattr(record, k))
                escaped_val = hashlib.sha1(sval).hexdigest()
                ormkey += k + ':' + escaped_val + '&'

            ormkey = ormkey[:-1]
            return ormkey

        def get_fields(self):
            return self._queries[0]['search'].keys()

        def get_default_fields(self):
            return self._queries[0].get('defaults', {}).keys()

        def fields_to_update(self):
            rv = []
            operation = self._queries[0]['operation']
            if operation == 'update':
                rv=self.get_fields()
                rv.extend(self.get_default_fields())

            elif operation == 'get':
                rv = self.get_fields()

            return rv

        def make_model(self, mod_dict, new_model=None):
            """
            Make a model from a dict
            Args:
                mod_dict:
                 array of fields/values

            Returns:
                a new orm record
            """
            if not new_model:
                new_model = self.mgr.model()

            for key in self.fields_to_update():
                if key in mod_dict['defaults']:
                    setattr(new_model,key,mod_dict['defaults'][key])
                else:
                    setattr(new_model,key,mod_dict['search'][key])

            return new_model

    def bulk_operation(self):
        return self.Bulk(self)

