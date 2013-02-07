from licensing.data import licence_application
from licensing.data.location import Locations
import json

def application_to_dict(application):
    return {
        'licence': application.licence,
        'body': application.body,
        'interaction': application.interaction,
        'location': application.location    
    }

if __name__ == '__main__':
    locations = Locations()

    applications = licence_application.from_google_data(locations.results)
    
    print json.dumps([application_to_dict(application) for application in applications])
