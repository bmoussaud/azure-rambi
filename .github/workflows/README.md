
### Deployment using Azure Appservice

Define the following resources
* Azure App Service Plan
* Web App

Change the startup commands with

```
gunicorn azurerambi.app:app --bind=0.0.0.0 --chdir src
```