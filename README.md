# ElectionViz

## Introduction

ElectionViz is a Python-based web application designed to provide insightful visualizations of election data. The application uses interactive maps and plots to represent election results, making it easier to analyze and understand electoral trends and outcomes across different constituencies/years.

The application is cross-platform as it does not rely on any OS-specific APIs. However, the installation and execution commands provided here are for a Linux-based environment.

## Features

- **Interactive Maps**: Analyze constituency-level results or aggregate trends over the years.
- **Multiple Data Views**: Explore election data through a rich set of visualizations.
- **Performance Optimized**: Pre-rendered maps ensure a smooth and responsive user experience.

## Setup and Installation

Follow these steps to set up the project on your local machine.

1. Clone the repository

    This project uses a submodule to manage its data. Clone the repository and initialize the submodule with the following command:

    ```bash
    git clone --recurse-submodules https://github.com/NRG-IITB/electionviz
    cd electionviz
    ```

    If you have already cloned the repository without the submodules, you can initialize them by running:

    ```bash
    git submodule update --init --recursive
    ```

2. Install dependencies

    ```bash
    pip install plotly dash pandas geopandas
    ```

## Running the Application

Once the setup is complete, you can run the application. Set `DEBUG_MODE=false` for general use to reduce logging and improve startup time.

- General Use:
    ```bash
    DEBUG_MODE=false python3 app.py
    ```
- Development:
    ```bash
    DEBUG_MODE=true python3 app.py
    ```

The application will start, and you can access it by navigating to `http://127.0.0.1:8050` in your web browser.

## Acknowledgements/Disclaimer

GenAI tools (Google Gemini Pro and GitHub Copilot) were used to generate the CSS styling of the web app. Official documentation and online forums were extensively consulted during development.

The raw data used for the visualization in this app can be found [here](https://github.com/NRG-IITB/scripts) on GitHub. The data was parsed/processed using scripts in [this](https://github.com/NRG-IITB/scripts) repo on GitHub.