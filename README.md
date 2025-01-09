[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/bmoussaud/azure-rambi)

# Azure Rambi

Welcome to the Azure Rambi project! This repository contains code and resources for managing and deploying the Rambi Application using Azure services.

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Introduction

Azure Rambi is a project designed to simplify the management and deployment of Azure resources. It provides a set of tools and scripts to automate common tasks.

## Getting Started

To get started with Azure Rambi, follow these steps:

1. Clone the repository:
    ```bash
    git clone https://github.com/bmoussaud/azure-rambi.git
    ```
2. Navigate to the project directory:
    ```bash
    cd azure-rambi
    ```

## Installation

Install the required dependencies by running:
```bash
pip install -r requirements.txt
```

## Usage

To use Azure Rambi, execute the following command:
```bash
python src/azurerambi/app.py
```


## Azure Resources

### AZD

```
azd auth login
azd up
````

### Azure Infrastructue

The [infra/main.bicep](infra/main.bicep)
* CognitiveServices 
    *  Open AI gpt-4
    * Open AI dall-e-3
* Application Service Plan
* Web-App
* API Management


### GitHub Credentials

edit the file [infra/authenticate_with_Azure_App_Service_for_GitHub.sh](infra/authenticate_with_Azure_App_Service_for_GitHub.sh) with your context and run it to grant a contributor to the resource group and to generate the secrets used by the GitHub action pipeline to deploy the differents components.
* `AZURE_CREDENTIALS` 
* `AZURE_SUBSCRIPTION_ID`

### Front GUI

* Service: Azure Application Service using the python runtime on linux
* CI/CD Pipeline: [.github/workflows/main_azure-rambi.yml](.github/workflows/main_azure-rambi.yml)



### API Management

Note: The bicep files come from: https://github.com/microsoft/AzureOpenAI-with-APIM/

#### TMDB

The OpenAPI json file is available here: https://developer.themoviedb.org/openapi. You'll find the file for [v3](https://developer.themoviedb.org/openapi/64542913e1f86100738e227f) and [v4](https://developer.themoviedb.org/openapi/6453cc549c91cf004cd2a015) version
## Contributing

We welcome contributions! Please read our [contributing guidelines](CONTRIBUTING.md) for more details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

```
  - name: Build the image in the Azure Containe Registry
    id: acr
    uses: azure/acr-build@v1
    with:
      service_principal: ${{ secrets.AZURE_SERVICE_PRINCIPAL_ID }}
      service_principal_password: ${{ secrets.AZURE_SERVICE_PRINCIPAL_PASSWORD }}
      tenant: ${{ secrets.AZURE_TENANT_ID }}
      registry: ${{ env.ACR_NAME }}
      repository: azure-rambi
      image: movie_poster_svc
      tag: ${{ github.sha }}
      folder: src/movie_poster_svc
      git_access_token: ${{ secrets.GITHUB_TOKEN }}
      branch: main
```      
