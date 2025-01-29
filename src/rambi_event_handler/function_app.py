import azure.functions as func
import logging

app = func.FunctionApp()

#curl https://rambi-events-handler.lemonground-ce949a08.francecentral.azurecontainerapps.io/api/hello   
@app.function_name(name="HttpTrigger1")
@app.route(route="hello", auth_level=func.AuthLevel.ANONYMOUS)
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    return func.HttpResponse(
        "This HTTP triggered function executed successfully.",
        status_code=200
        )