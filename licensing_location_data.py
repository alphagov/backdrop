from licensing.data import licence_application
from licensing.data.location import Locations
import json

def application_to_dict(application):
    return {
        'licence': application.licence,
        'authority': application.authority,
        'interaction': application.interaction,
        'location': application.location,
        'visits': application.visits,
        'start_at': application.start_at,
        'end_at': application.end_at
    }

if __name__ == '__main__':
    locations = Locations()

    applications = licence_application.from_google_data(locations.results, locations.start_date, locations.end_date)
    
    print json.dumps([application_to_dict(application) for application in applications])
