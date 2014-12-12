def calculate_rating(datum):
    # See
    # https://github.com/alphagov/spotlight/blob/ca291ffcc86a5397003be340ec263a2466b72cfe/app/common/collections/user-satisfaction.js
    if not datum['total:sum']:
        return None
    # Copy datum before we mutate it.
    datum = dict(datum)
    min_score = 1
    max_score = 5
    score = 0
    for rating in range(min_score, max_score + 1):
        rating_key = 'rating_{0}:sum'.format(rating)
        score += datum[rating_key] * rating
        # Set rating key that spotlight expects.
        datum['rating_{0}'.format(rating)] = datum[rating_key]
    mean = score / (datum['total:sum'])
    return (mean - min_score) / (max_score - min_score)


def compute(data):
    # Calculate rating and set keys that spotlight expects.
    computed = []
    for datum in data:
        datum['number_of_responses'] = datum['total:sum']
        datum['days_with_responses'] = datum['_count']
        datum['rating'] = calculate_rating(datum)
        computed.append(datum)
    return computed
