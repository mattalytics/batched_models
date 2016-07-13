# -*- coding: UTF-8 -*-
from django.test import TestCase
from batched.models import *
from django.core.management.base import BaseCommand
import time


bigtext1 = """
hi
this is a story
asdfkj34k5j3k4mkf::& &x:&j∆∆˚ß∆µß˚øˆ¨ˆ∆
"""

bigtext2 = bigtext1 + bigtext1
reallybigtext = ''
for i in range(0,1000):
    reallybigtext += bigtext1


bs=5000 #lower this value if you crash...
test_size = 5000

class TestArch(TestCase):

    def test_basic_bulk(self):
        """simple single-field update should work - CAPTURE BENCHMARKS TOO"""

        bulk_create_time = time.time()
        b = bulker.objects.bulk_operation()
        for i in range(0,test_size):
            b.update_or_create(x=unicode(i),defaults={'y':1})
        b.run(batch_size=bs)
        bulk_create_time_complete = time.time()
        
        """ we should have `test_size` recs """
        cnt = bulker.objects.all().count()
        print cnt,'objects created'
        assert(cnt == test_size)

        """let's test the updating feature with BENCHMARKS"""
        b = bulker.objects.bulk_operation()
        bulk_update_time = time.time()
        for i in range(0,test_size):
            b.update_or_create(x=unicode(i),defaults={'y':2})
        b.run(batch_size=bs)
        bulk_update_time_complete = time.time()

        """ we should still have 100000 recs"""
        assert(bulker.objects.all().count()==test_size)
        """ none of them should have y=1 anymore, though """
        assert(bulker.objects.filter(y=2).count()==test_size)

        """ check for a big update that shouldnt actually find anything to update... """
        b = bulker.objects.bulk_operation()
        for i in range(0,test_size):
            b.get_or_create(x=unicode(i+test_size),y='1')
        ret = b.run(batch_size=bs)
        assert(len(ret) == test_size)


        """multiple field update should work"""
        b = bulker.objects.bulk_operation()
        for i in range(test_size+333333,test_size+334444):
            b.update_or_create(x=unicode(i),y=unicode(i))
        b.run()

        """check that get returns proper num of objects"""
        b = bulker.objects.bulk_operation()
        for i in range(test_size+333333, test_size+334444):
            b.get_or_create(x=unicode(i),y=unicode(i))
        results = b.run()
        if len(results) != 1111:
            raise Exception('get return proper value')
        assert(results[0].pk)
        """check that the values are actually correct"""
        found = bulker.objects.filter(x__in=[unicode(i) for i in range(test_size+333333, test_size+334444)])
        assert(found.count() == 1111)
        for f in found:
            if f.y != f.x:
                assert(False)

        #can it handle complex text?
        b = bulker.objects.bulk_operation()
        b.update_or_create(x=bigtext2,y=bigtext1)
        b.update_or_create(y=bigtext1,x=bigtext2)
        b.update_or_create(x=reallybigtext+reallybigtext, y=reallybigtext)
        b.run()

        found = bulker.objects.filter(x__exact=reallybigtext+reallybigtext)
        assert(found.count()==1)

        #deals with numbers, right?
        b = bulker.objects.bulk_operation()
        for i in range(100000,101000):
            b.update_or_create(x='test1' + str(i),
                               y='test2'+str(i),
                               num=i
                               )
        b.run()
        found = bulker.objects.filter(num__gte=100000)
        assert(found.count() == 1000)
        for f in found:
            assert(f.x=='test1'+str(f.num))
            assert(f.y=='test2'+str(f.num))

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
        for i in range(0,test_size/10):
            bulker.objects.get_or_create(x=i+100001, defaults={'y':1})
        create_time_complete = time.time()

        print 'starting bench 2'
        update_time = time.time()
        for i in range(0,test_size/10):
            bulker.objects.update_or_create(x=i+100001, defaults={'y':2})
        update_time_complete = time.time()

        print 'bulk update',bulk_update_time_complete - bulk_update_time
        print 'bulk insert',bulk_create_time_complete - bulk_create_time
        print 'update (1/10 of data because get_or_create is slow)', update_time_complete-update_time, (update_time_complete-update_time)*10, 'estimated comparison'
        print 'insert (1/10 of data because get_or_create is slow)',create_time_complete-create_time, (create_time_complete-create_time)*10, 'estimated comparison'

        print 'Success'



