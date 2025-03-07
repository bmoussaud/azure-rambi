import azure.functions as func
import logging

app = func.FunctionApp()

#curl https://rambi-events-handler.lemonground-ce949a08.francecentral.azurecontainerapps.io/api/hello   
#
@app.function_name(name="HttpTrigger1")
@app.route(route="hello", auth_level=func.AuthLevel.ANONYMOUS)
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    """ HTTP trigger function that returns a sample response. """
    logging.info('Benoit Python HTTP trigger function processed a request.')
    return func.HttpResponse(
        "Benoit This HTTP triggered function executed successfully.",
        status_code=200
        )


@app.queue_trigger(arg_name="azqueue", queue_name="generatedmovies",connection="AzureWebJobsStorage")
def generatedmovieQueueTrigger(azqueue: func.QueueMessage):
    """This function will be invoked whenever a message is added to the queue."""
    logging.info('Python Queue trigger processed a message: %s',
                azqueue.get_body().decode('utf-8'))
