def queryset_chunker(queryset, chunk_size=5000, order_by='-pk', limit=None):
    """
    Takes lazy queryset and chunks it by given chunk_size.

    :param queryset: type of queryset. This is a lazy queryset to
        split into chunks
    :type queryset: QuerySet
    :param chunk_size: size of smaller pieces
    :type chunk_size: int
    """
    if queryset.query.distinct:
        order_by = queryset.query.distinct_fields[0]
    if not queryset.query.order_by:
        queryset = queryset.order_by(order_by)
    for pivot in xrange(0, queryset.count(), chunk_size):
        if limit and pivot > limit:
            break
        yield queryset[pivot:pivot + chunk_size]
