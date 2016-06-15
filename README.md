# batched_models

*Not for production use. This is an initial commit*

A cute little model manager for batching expensive Django update_or_create/get_or_create operations

Django's get_or_create/update_or_create functions are useful, but slow. This model manager provides a means to speed things up a bit.

*Usage*

create a model like this:
```
class bulker(models.Model):
    id=models.AutoField(primary_key=True)
    x=models.TextField(unique=True)
    y=models.TextField()

    objects = BulkManager()
```

Now, you can do this:

```
batch = bulker.objects.bulk_operation()
batch.update_or_create(x='199999', defaults={'y':2})
batch.update_or_create(x='19998', defaults={'y':1})
"""
Add thousands more operations here...
"""
batch.run()
```


