from robocorp.tasks import task
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from RPA.Robocorp.WorkItems import WorkItems
import os
import json
import urllib.request
import time


class NewsScraper:
    """
    A class to scrape news articles from a website and save the data to an Excel file.
    """

    def __init__(self):
        """
        Initialize the NewsScraper with required libraries and file paths.
        """
        self.browser = Selenium()
        self.excel = Files()
        self.work_items = WorkItems()
        self.input_file_path = 'input_work_item.json'
        self.output_file_path = 'output_work_item.json'
        self.output_img_path = './output/'

    def download_image(self, url, filename):
        """
        Download an image from a given URL.

        Args:
            url (str): The URL of the image to download.
            filename (str): The local filename to save the image as.
        """
        try:
            urllib.request.urlretrieve(url, filename)
        except Exception as e:
            print(f"An error occurred while downloading the image: {e}")

    def search_phrase_count(self, title, description, phrase):
        """
        Count the occurrences of a search phrase in the title and description.

        Args:
            title (str): The title of the news article.
            description (str): The description of the news article.
            phrase (str): The search phrase to count.

        Returns:
            int: The total count of the search phrase in the title and description.
        """
        count_title = title.lower().count(phrase.lower())
        count_description = description.lower().count(phrase.lower())
        return count_title + count_description

    def contains_money(self, text):
        """
        Check if the text contains any monetary values.

        Args:
            text (str): The text to check for monetary values.

        Returns:
            bool: True if the text contains monetary values, False otherwise.
        """
        patterns = [r'\$\d+(?:,\d{3})*(?:\.\d{2})?', r'\d+\s+dollars', r'\d+\s+USD']
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False

    def load_work_item(self):
        """
        Load the input work item containing the search parameters.

        Returns:
            tuple: Contains the search phrase, news category, and number of months.
        """
        input_data = self.work_items.get_input_work_item()
        print("Work Items Loaded Successfully")

        try:
            # If running on Control room Cloud
            search_phrase = input_data.payload['payload']["search_phrase"]
            months = input_data.payload['payload']["months"]
            news_category = input_data.payload['payload']["news_category"]
        except KeyError:
            # If running on Local Environment
            search_phrase = input_data.payload["search_phrase"]
            months = input_data.payload["months"]
            news_category = input_data.payload["news_category"]

        return search_phrase, news_category, months

    def open_browser_and_search_news(self, search_phrase):
        """
        Open the browser, navigate to the news website, and perform a search.

        Args:
            search_phrase (str): The phrase to search for.
        """
        self.browser.open_available_browser("https://www.latimes.com/")
        self.browser.maximize_browser_window()
        self.browser.wait_until_element_is_visible(
            "xpath://button[@data-element='search-button']", timeout=40)
        self.browser.click_element_when_visible("xpath://button[@data-element='search-button']")
        self.browser.input_text_when_element_is_visible(
            'xpath://input[@data-element="search-form-input"]', search_phrase)
        self.browser.click_element_when_visible('xpath://button[@data-element="search-submit-button"]')

    def should_process_article(self, date, months):
        """
        Determine if an article should be processed based on its date.

        Args:
            date (str): The date of the news article.
            months (int): The number of months to look back.

        Returns:
            str: "Break" if the article should not be processed, "Continue" otherwise.
        """
        try:
            try:
                article_date = datetime.strptime(date, "%b %d, %Y")
            except ValueError:
                article_date = datetime.strptime(date, "%b. %d, %Y")

            # Calculate the start of the period to include articles
            if months > 0:
                cutoff_date = (datetime.now() - relativedelta(months=months - 1)).replace(day=1)
            else:
                cutoff_date = datetime.now().replace(day=1)

            if article_date < cutoff_date:
                return "Break"
        except Exception:
            pass

        return "Continue"

    def extract_page_data(self, articles, search_phrase, news_data, months):
        """
        Extract data from the list of articles.

        Args:
            articles (list): List of article elements to extract data from.
            search_phrase (str): The phrase to search for.
            news_data (list): List to store the extracted news data.
            months (int): The number of months to look back for news articles.
        """
        for index, article in enumerate(articles):
            article_xpath = 'xpath:(//ul[@class="search-results-module-results-menu"]//li'
            self.browser.wait_until_element_is_enabled(
                '{}//h3)[{}]'.format(article_xpath, index + 1))
            time.sleep(2)
            title = self.browser.get_text(
                '{}//h3)[{}]'.format(article_xpath, index + 1))
            print(title)
            date = self.browser.get_text(
                '{}//p[@class="promo-timestamp"])[{}]'.format(article_xpath, index + 1))

            # Check date range
            try:
                try:
                    article_date = datetime.strptime(date, "%b %d, %Y")
                except ValueError:
                    article_date = datetime.strptime(date, "%b. %d, %Y")

                # Calculate the start of the period to include articles
                if months > 0:
                    cutoff_date = (datetime.now() - relativedelta(months=months - 1)).replace(day=1)
                else:
                    cutoff_date = datetime.now().replace(day=1)

                if article_date < cutoff_date:
                    return "Break"
            except Exception:
                pass

            description = self.browser.get_text(
                '{}//p[@class="promo-description"])[{}]'.format(article_xpath, index + 1))
            image_filename = ''
            try:
                image_url = str(self.browser.get_element_attribute(
                    '{}//source[@type="image/webp"])[{}]'.format(article_xpath, index + 1), "srcset")).split(',')[0].split(' ')[0]

                # Download image
                img_name = image_url.split('%')[-1]
                if '.jpg' not in img_name:
                    img_name = img_name + '.jpg'
                image_filename = self.output_img_path + f"{img_name}"

                self.download_image(image_url, image_filename)
            except Exception:
                image_filename = "No image"

            # Analyze text
            search_count = self.search_phrase_count(title, description, search_phrase)
            contains_money_flag = self.contains_money(description)

            news_entry = [title, date, description, image_filename, search_count, contains_money_flag]
            news_data.append(news_entry)

    def run_keyword_and_return_status(self, keyword, *args):
        """
        Run a keyword function and return its status.

        Args:
            keyword (function): The keyword function to run.
            *args: Arguments to pass to the keyword function.

        Returns:
            tuple: (status, result) where status is a boolean indicating success,
                   and result is the result of the keyword function.
        """
        try:
            result = keyword(*args)
            return True, result
        except Exception as e:
            print(f"Keyword failed: {e}")
            return False, None

    def select_news_category(self, news_category):
        """
        Select the news category on the website if specified.

        Args:
            news_category (str): The category of news to filter by.
        """
        if news_category is not None:
            self.browser.click_element_when_visible('//span[@class="see-all-text"]')
            try:
                self.browser.click_button_when_visible(
                    '(//ul[@class="search-filter-menu"])[1]//span[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{}")]/../input'.format(news_category.lower()))
            except Exception as e:
                print("The Search Phrase category not found on page")

    def extract_news_data(self, search_phrase=None, news_category=None, months=0):
        """
        Extract news data from the website based on the search phrase and category.

        Args:
            search_phrase (str): The phrase to search for.
            news_category (str): The category of news to filter by.
            months (int): The number of months to look back for news articles.

        Returns:
            list: A list of extracted news data entries.
        """
        self.browser.wait_until_element_is_visible(
            'xpath:(//ul[@class="search-results-module-results-menu"]//li)[1]', timeout=20)
        articles = self.browser.get_webelements('xpath://ul[@class="search-results-module-results-menu"]//li')
        news_data = []
        pages = None
        try:
            page_num = int(str(self.browser.get_text(
                'xpath://div[@class="search-results-module-page-counts"]').split(' ')[-1]).replace(',', ''))
        except:
            print('Invalid Page number')

        # Selecting the latest News
        self.browser.select_from_list_by_label('xpath://select[@class="select-input"]', 'Newest')
        self.run_keyword_and_return_status(self.select_news_category, news_category)
        for i in range(1, page_num):
            status, result = self.run_keyword_and_return_status(
                self.extract_page_data, articles, search_phrase, news_data, months)
            if result == 'Break':
                break
            # Clicking on Next page
            next_page_link = self.browser.get_element_attribute(
                'xpath://div[@class="search-results-module-next-page"]/a', 'href')
            self.browser.go_to(next_page_link)

        return news_data

    def save_news_data_to_excel(self, news_data):
        """
        Save the extracted news data to an Excel file.

        Args:
            news_data (list): The list of news data entries to save.
        """
        output_file = os.path.join("output", "news_data.xlsx")
        self.excel.create_workbook(output_file)
        header = ["Title", "Date", "Description", "Image filename", "Search count", "Contains money flag"]
        self.excel.append_rows_to_worksheet([header], header=False)

        for data in news_data:
            self.excel.append_rows_to_worksheet([data], header=False)

        self.excel.save_workbook()
        self.excel.close_workbook()

    def load_payload_from_json(self, file_path):
        """
        Load payload data from a JSON file.

        Args:
            file_path (str): The path to the JSON file.

        Returns:
            dict: The payload data.
        """
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data["payload"]

    def main(self):
        """
        Main function to run the news scraper.
        """
        search_phrase, news_category, months = self.load_work_item()
        self.open_browser_and_search_news(search_phrase)
        news_data = self.extract_news_data(search_phrase, news_category, months)
        self.save_news_data_to_excel(news_data)
        # self.browser.close_browser()


@task
def run_main():
    """
    Task to run the news scraper.
    """
    scraper = NewsScraper()
    scraper.main()


if __name__ == "__main__":
    run_main()
