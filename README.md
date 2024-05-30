# RpaChallenge-FreshNews


This project is a web scraping tool designed to extract news articles from the LA Times website and save the data into an Excel file. The tool uses the RPA (Robotic Process Automation) framework with Selenium to automate the browsing and data extraction process.

## Features

- Open the LA Times website and search for news articles based on a given search phrase.
- Filter news articles by category and time range (number of months).
- Extract key information from each news article including the title, date, description, image, search phrase count, and monetary content.
- Save the extracted data into an Excel file for further analysis.

## Requirements

- Python 3.x
- RPA Framework
- Selenium WebDriver

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/yourusername/news-scraper.git
    cd news-scraper
    ```
2. **Configure Dependencies**:
    - Ensure your `conda.yaml` or `robot.yaml` file includes all necessary dependencies. Example:

      ```yaml
      channels:
        - conda-forge
      dependencies:
        - python=3.8
        - pip
        - pip:
            - rpaframework
      ```

### Setting Up in Robocorp Cloud

1. **Create a New Robot**:
    - Log in to Robocorp Cloud.
    - Create a new robot in your workspace.

2. **Upload the Code**:
    - Zip the contents of your project directory.
    - Upload the zip file to your robot in Robocorp Cloud.

3. **Configure Dependencies**:
    - In the robot settings, specify the required dependencies similar to the `conda.yaml` configuration above.

## Usage

### Running the Scraper

To run the scraper, execute the following command:

### Logging 
In this script, the RotatingFileHandler is used to write logs to a file named news_scraper.log. The maxBytes parameter is set to 5 MB, and backupCount is set to 2, meaning that when the log file reaches 5 MB, it will be backed up and a new log file will be created. This helps in managing log files by rotating them when they reach a certain size. The handlers parameter in logging.basicConfig includes both the file handler and the console handler to ensure logs are output to both the console and the log file.


```sh
C:; cd 'path\to\your\project'; & 'path\to\your\run_env.bat' 'path\to\your\rcc.exe' 'task' 'run' '--robot' 'path\to\your\robot.yaml' '--space' 'vscode-03' '--task' 'Run Task' '--controller' 'RobocorpCode'
