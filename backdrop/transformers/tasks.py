from worker import app


@app.task(ignore_result=True)
def dispatch(dataset_id, earliest, latest):
    """
    For the given parameters, query stagecraft for transformations
    to run, and dispatch tasks to the appropriate workers.
    """

    # TODO: query stagecraft with dataset_id and run transforms
    pass
