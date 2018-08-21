class PostgresStorageEngine(object):

    def __init__(self):
        pass

    def alive(self):
        # TODO
        pass

    def data_set_exists(self, data_set_id):
        # TODO
        pass

    def create_data_set(self, data_set_id, size):
        # TODO
        pass

    def delete_data_set(self, data_set_id):
        # TODO
        pass

    def get_last_updated(self, data_set_id):
        # TODO
        pass

    def batch_last_updated(self, data_sets):
        # TODO
        pass

    def empty_data_set(self, data_set_id):
        # TODO
        pass

    def save_record(self, data_set_id, record):
        # TODO
        pass

    def find_record(self, data_set_id, record_id):
        # TODO
        pass

    def update_record(self, data_set_id, record_id, record):
        # TODO
        pass

    def delete_record(self, data_set_id, record_id):
        # TODO
        pass

    def execute_query(self, data_set_id, query):
        # TODO
        pass
