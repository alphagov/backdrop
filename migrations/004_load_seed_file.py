"""
Load initial user and bucket data from seed files.
"""
import logging
import os
import subprocess
import sys

log = logging.getLogger(__name__)


def up(db):
    names = db.collection_names()

    if "users" in names and "buckets" in names:
        log.info("both users and buckets collections already exist")
        return

    invoke = os.path.join(os.path.dirname(sys.executable), "invoke")
    subprocess.call([invoke, "load_seed"])
