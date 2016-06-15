from django.core.management.base import BaseCommand
from leaf.models import *
bigtext1 = """
hi
this is a story
asdfkj34k5j3k4mkf::& &x:&
"""
bigtext2 = bigtext1 + bigtext1

class Command(BaseCommand):

    def handle(self, *args, **options):
        """simple single-field update should work"""
        b = bulker.objects.bulk_operation()
        b.update_or_create(defaults={'y':2},x='199999')
        b.update_or_create(x='19998',defaults={'y':1})
        for i in range(199999,215000):
            b.update_or_create(x=unicode(i),defaults={'y':1})
        b.run()

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

        print 'Success'



