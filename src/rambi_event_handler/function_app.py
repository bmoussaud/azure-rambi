import azure.functions as func
import logging
import requests
import json
from opencensus.extension.azure.functions import OpenCensusExtension
from opencensus.trace import config_integration

config_integration.trace_integrations(['requests'])
OpenCensusExtension.configure()

app = func.FunctionApp()

logging.info('Azure Rambu Event Handler Function App started.')

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


@app.function_name("OnNewGeneratedMovie")
@app.queue_trigger(arg_name="msg", queue_name="generatedmovies",connection="RambiQueueStorageConnection")
def generated_movie_queue_trigger(msg: func.QueueMessage) -> None:
    """This function will be invoked whenever a message is added to the queue."""
    logging.info('Python Queue trigger processed a message: %s',
                msg.get_body().decode('utf-8'))
    logging.debug('D Python Queue trigger processed a message: %s',
                msg.get_body().decode('utf-8'))
    logging.warning('W Python Queue trigger processed a message: %s',
                msg.get_body().decode('utf-8'))
    logging.error('E Python Queue trigger processed a message: %s',        
                msg.get_body().decode('utf-8'))
