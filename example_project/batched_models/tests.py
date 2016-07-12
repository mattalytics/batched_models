from django.test import TestCase
from batched_models.models import *
from django.core.management.base import BaseCommand
import time
bigtext1 = """
hi
this is a story
asdfkj34k5j3k4mkf::& &x:&
"""

bigtext2 = bigtext1 + bigtext1

bs=5000 #lower this value if you crash...

class TestArch(TestCase):

    def test_basic_bulk(self):
        """simple single-field update should work - CAPTURE BENCHMARKS TOO"""
        bulk_create_time = time.time()
        b = bulker.objects.bulk_operation()
        for i in range(0,100000):
            b.update_or_create(x=unicode(i),defaults={'y':1})
        b.run(batch_size=bs)
        bulk_create_time_complete = time.time()
        
        """ we should have 100000 recs """
        cnt = bulker.objects.all().count()
        print cnt,'objects created'
        assert(cnt == 100000)

        """let's test the updating feature with BENCHMARKS"""
        b = bulker.objects.bulk_operation()
        bulk_update_time = time.time()
        for i in range(0,100000):
            b.update_or_create(x=unicode(i),defaults={'y':2})
        b.run(batch_size=bs)
        bulk_update_time_complete = time.time()

        """ we should still have 100000 recs"""
        assert(bulker.objects.all().count()==100000) 
        """ none of them should have y=1 anymore, though """
        assert(bulker.objects.filter(y=2).count()==100000)

        """ check for a big update that shouldnt actually find anything to update... """
        bulk_update_time = time.time()
        b = bulker.objects.bulk_operation()
        for i in range(0,100000):
            b.get_or_create(x=unicode(i+1000000),y='1')
        ret = b.run(batch_size=bs)
        assert(len(ret) == 0)


        """multiple field update should work"""
        b = bulker.objects.bulk_operation()
        for i in range(333333,334444):
            b.update_or_create(x=unicode(i),y=unicode(i))
        b.run()

        """check that get returns proper num of objects"""
        b = bulker.objects.bulk_operation()
        for i in range(333333,334444):
            b.get_or_create(x=unicode(i),y=unicode(i))
        results = b.run()
        if len(results) != 1111:
            raise Exception('get return proper value')
        assert(results[0].pk)

        #can it handle complex text?
        b = bulker.objects.bulk_operation()
        b.update_or_create(x=bigtext2,y=bigtext1)
        b.update_or_create(y=bigtext2,x=bigtext1)
        b.run()

        #does it error when doing something stupid?
        try:
            b = bulker.objects.bulk_operation()
            b.update_or_create(x=bigtext2,y=bigtext1)
            b.update_or_create(x=bigtext2,y=bigtext1,defaults={'x':1})
            raise Exception('fields for defaults must alway match')
        except:
            pass

        try:
            b = bulker.objects.bulk_operation()
            b.update_or_create(x=bigtext2,y=bigtext1,defaults={'x':1})
            b.update_or_create(x=bigtext2,y=bigtext1)
            raise Exception('fields for defaults must alway match')
        except:
            pass

        try:
            b = bulker.objects.bulk_operation()
            b.update_or_create(x=bigtext2,y=bigtext1)
            b.update_or_create(x=bigtext2)
            raise Exception('selection of fields must always match')
        except:
            pass

        try:
            b = bulker.objects.bulk_operation()
            b.update_or_create(x=bigtext2)
            b.update_or_create(x=bigtext2,y=bigtext1)
            raise Exception('selection of fields must always match')
        except:
            pass

        try:
            b = bulker.objects.bulk_operation()
            b.run()
            raise Exception('Should not be able to run an empty batch')
        except:
            pass

        """ benchmark time """
        print 'starting bench 1'
        create_time = time.time()
        for i in range(0,10000):
            bulker.objects.get_or_create(x=i+100001, defaults={'y':1})
        create_time_complete = time.time()

        print 'starting bench 2'
        update_time = time.time()
        for i in range(0,10000):
            bulker.objects.update_or_create(x=i+100001, defaults={'y':2})
        update_time_complete = time.time()

        print 'bulk update',bulk_update_time_complete-bulk_update_time
        print 'bulk insert',bulk_create_time_complete-bulk_create_time
        print 'update (1/10 of data because get_or_create is slow)', update_time_complete-update_time, (update_time_complete-update_time)*10, 'estimated comparison'
        print 'insert (1/10 of data because get_or_create is slow)',create_time_complete-create_time, (create_time_complete-create_time)*10, 'estimated comparison'

        print 'Success'



