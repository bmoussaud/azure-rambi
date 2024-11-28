
### Deployment using Azure Appservice

To deploy your Python application to Azure App Service, you need to create both an Azure App Service Plan and an Azure App Service:

* Azure App Service Plan: Defines the compute resources (CPU, memory, and scaling options) for your app. It's essentially the hosting infrastructure for your application.
* Azure App Service / WebApp : The web app where your application code runs.

Change WebApp configuration with
* the startup commands with ```gunicorn azurerambi.app:app --bind=0.0.0.0 --chdir src ```
* using a push trigger on a GitHub Action to update the content
* Operating System : `linux` 
* Runtime Stack: Select `Python 3.12` (as specified in your `runtime.txt`)
