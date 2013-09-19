import subprocess

class VirusSignatureError(StandardError):
    def __init__(self, message):
        self.message = message


class ScannedFile(object):

    def __init__(self, file_path):
        self.file_path = file_path
        self._virus_signature = False

    @property
    def has_virus_signature(self):
        self._virus_signature = (self._virus_signature or bool(subprocess.call(["clamscan", self.file_path])))
        return self._virus_signature
        
    #def __init__(self, file_object):
        #self.file_object = file_object
        #self._virus_signature = False

    #@property
    #def has_virus_signature(self):
        #save_file_to_disk
        #scan_file_and_clean_up
        #return self._virus_signature
