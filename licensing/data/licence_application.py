import collections

_LicenceApplication = collections.namedtuple('LicenceApplication', 'licence authority interaction location visits start_at end_at')

class LicenceApplication(_LicenceApplication):
    @classmethod
    def from_google_row(cls, path, location, visits, start_at, end_at):
        split_url = path.rsplit('/')
        
        return cls(split_url[2], split_url[3], split_url[4].partition('-')[0], location, visits, start_at, end_at)


def from_google_data(data, start_date, end_date):
    for path, country, num_visits in data:
        yield LicenceApplication.from_google_row(path, country, num_visits, start_date, end_date)
