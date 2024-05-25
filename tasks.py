from robocorp.tasks import task
import re
import requests
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from RPA.Robocorp.WorkItems import WorkItems
from robocorp import workitems
from RPA.HTTP import HTTP as http
from RPA.FileSystem import FileSystem as file_system
import os
import json
import urllib.request
import shutil
import time

from RPA.Robocorp.Process import Process
# Initialize libraries
browser = Selenium()
excel = Files()
work_items = WorkItems()
#items = Items()
# Define the file paths for input and output work items
input_file_path = 'input_work_item.json'
output_file_path = 'output_work_item.json'
output_img_path = './output/news_images/'
def download_image(url, filename):
    try:
        urllib.request.urlretrieve(url, filename)
        
    except Exception as e:
        print(f"An error occurred while downloading the image: {e}")
def search_phrase_count(title,description, phrase):
    count_title = title.lower().count(phrase.lower())
    count_description = description.lower().count(phrase.lower())

    return count_title + count_description

def contains_money(text):
    patterns = [r'\$\d+(?:,\d{3})*(?:\.\d{2})?', r'\d+\s+dollars', r'\d+\s+USD']
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False

def load_work_item():
    
    # with open('input_work_item.json', 'r') as file:
    #     input_data = json.load(file)
    
    # workitems.set_work_item_payload(payload=input_data['payload'])
    # work_items.create_output_work_item(variables=input_data["payload"],save=True)
    
    input_data = work_items.get_input_work_item()
    print("Work Items Loaded Successfully")
    # work_items.set_work_item_payload(payload=input_data)
    # workitems.save()
    # workitems = workitems.get_input_work_item()
    # workitems.create_output(payload=input_data["payload"])
    
    # workitems.load()
    # work_item = workitems.get_input_work_item()

    search_phrase = input_data.payload["search_phrase"]
    months = input_data.payload["months"]
    news_category = input_data.payload["news_category"]
    
    return search_phrase, news_category, months

def open_browser_and_search_news(search_phrase):
    browser.open_available_browser("https://www.latimes.com/")
    browser.maximize_browser_window()
    browser.wait_until_element_is_visible("xpath://button[@data-element='search-button']",timeout=40)
    browser.click_element_when_visible("xpath://button[@data-element='search-button']")
    browser.input_text_when_element_is_visible('xpath://input[@data-element="search-form-input"]', search_phrase)
    browser.click_element_when_visible('xpath://button[@data-element="search-submit-button"]')

def should_process_article(date, months):
    try:
        try:
            article_date = datetime.strptime(date, "%b %d, %Y")
        except ValueError:
            article_date = datetime.strptime(date, "%b. %d, %Y")
        
        # Calculate the start of the period to include articles
        if months > 0:
            cutoff_date = (datetime.now() - relativedelta(months=months-1)).replace(day=1)
        else:
            cutoff_date = datetime.now().replace(day=1)
        
        if article_date < cutoff_date:
            return "Break"
    except Exception as e:
        print(e)
        pass

    return "Continue"
    
def extract_page_data(articles,search_phrase,news_data,months):
    for index,article in enumerate(articles): 
        article_xpath='xpath:(//ul[@class="search-results-module-results-menu"]//li'
        browser.wait_until_element_is_visible('{}//h3)[{}]'.format(article_xpath,index+1))
        title = browser.get_text('{}//h3)[{}]'.format(article_xpath,index+1))
        print(title)
        date = browser.get_text('{}//p[@class="promo-timestamp"])[{}]'.format(article_xpath,index+1))
        # Check date range
        try:
            try:
                article_date = datetime.strptime(date, "%b %d, %Y")
            except ValueError:
                article_date = datetime.strptime(date, "%b. %d, %Y")
            
            # Calculate the start of the period to include articles
            if months > 0:
                cutoff_date = (datetime.now() - relativedelta(months=months-1)).replace(day=1)
            else:
                cutoff_date = datetime.now().replace(day=1)
            
            if article_date < cutoff_date:
                return "Break"
        except Exception as e:
            print(e)
            pass

        
        description = browser.get_text('{}//p[@class="promo-description"])[{}]'.format(article_xpath,index+1))
        image_filename= ''
        try:
            image_url = str(browser.get_element_attribute('{}//source[@type="image/webp"])[{}]'.format(article_xpath,index+1), "srcset")).split(',')[0].split(' ')[0]
            # Download image
            img_name = image_url.split('%')[-1]
            if '.jpg' not in img_name:
                img_name=img_name+'.jpg'
            image_filename = output_img_path+f"{img_name}"

            download_image(image_url, image_filename)
        except Exception:
            image_filename= "No image"

        
        # Analyze text
        search_count = search_phrase_count(title,description, search_phrase)
        contains_money_flag = contains_money(description)

        news_entry = [title, date, description, image_filename, search_count, contains_money_flag]
        news_data.append(news_entry)
def run_keyword_and_return_status(keyword, *args):
    try:
        result = keyword(*args)
        return True, result
    except Exception as e:
        print(f"Keyword failed: {e}")
        return False, None
def select_news_category(news_category):
    # Check If Category is mentioned
    if news_category is not None:
        # Find News Category on Page
        browser.click_element_when_visible('//span[@class="see-all-text"]')
        try:
            browser.click_button_when_visible('(//ul[@class="search-filter-menu"])[1]//span[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"),"{}")]/../input'.format(news_category.lower()))
        except Exception as e:
            print("The Search Phrase category not found on page")
    
def extract_news_data(search_phrase=None,news_category=None, months=0):
    browser.wait_until_element_is_visible('xpath:(//ul[@class="search-results-module-results-menu"]//li)[1]',timeout=20)
    time.sleep(10)
    articles = browser.get_webelements('xpath://ul[@class="search-results-module-results-menu"]//li')
    news_data = []
    pages = None
    try:
        page_num= int(str(browser.get_text('xpath://div[@class="search-results-module-page-counts"]').split(' ')[-1]).replace(',',''))
    except:
        print('Invalid Page number')
    # Selecting the latest News
    browser.select_from_list_by_label('xpath://select[@class="select-input"]', 'Newest')
    run_keyword_and_return_status(select_news_category,news_category)
    for i in range(1,page_num):
        status,result= run_keyword_and_return_status(extract_page_data,articles,search_phrase,news_data,months)
        if result == 'Break':
            break
        #Clicking on Next page
        #browser.scroll_element_into_view('xpath://div[@class="search-results-module-next-page"]/a')
        next_page_link= browser.get_element_attribute('xpath://div[@class="search-results-module-next-page"]/a' , 'href')
        browser.go_to(next_page_link)
        
    
    return news_data

def save_news_data_to_excel(news_data):
    output_file = os.path.join("output", "news_data.xlsx")
    excel.create_workbook(output_file)
    header = ["Title", "Date", "Description", "Image filename", "Search count", "Contains money flag"]
    excel.append_rows_to_worksheet([header], header=False)
    
    for data in news_data:
        excel.append_rows_to_worksheet([data], header=False)
    
    excel.save_workbook()
    excel.close_workbook()

def load_payload_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data["payload"]

def process_user_input():
    # Assuming the input work item contains a payload with keys: search_phrase, months, news_category
    item = workitems.inputs.current
    search_phrase = item.payload.get("search_phrase")
    months = item.payload.get("months")
    news_category = item.payload.get("news_category")
    
    # Process the input here (e.g., perform a search operation based on the inputs)
    # This is a placeholder for the actual processing logic
    print(f"Processing: {search_phrase}, {months}, {news_category}")
    
    # Create an output work item with the results of the processing
    # For demonstration, we're just echoing the input
    results_payload = {
        "search_phrase": search_phrase,
        "months": months,
        "news_category": news_category,
        "results": "Sample results based on the input parameters"
    }
    workitems.outputs.create(payload=results_payload)
def process_work_items():
    # Load input work item from file
    with open(input_file_path, 'r') as f:
        input_data = json.load(f)
    # Create a new input work item from the loaded JSON payload
    workitems.create_input_work_item(payload=input_data["payload"])
    work_items.create_output_work_item(variables=input_data["payload"],save=True)
    #workitems.create_output_work_item(variables=input_data["payload"], save=True)
    work_items.get_input_work_item()
    # Get the payload from the work item
    payload = workitems.get_work_item_payload()
    # Set the input work item payload
    work_items.set_work_item_payload(input_data)
    item = workitems.inputs.current
    search_phrase = item.payload.get("search_phrase")
    months = item.payload.get("month")
    news_category = item.payload.get("news_category")
    
    payload = item.payload
    # Extract data from the payload
    search_phrase = payload['search_phrase']
    month = payload['month']
    news_category = payload['news_category']
    
    print(f"Search Phrase: {search_phrase}, Month: {month}, News Category: {news_category}")

@task
def main():
    #process_work_items()
    search_phrase, news_category, months = load_work_item()
    open_browser_and_search_news(search_phrase)
    news_data = extract_news_data(search_phrase,news_category, months)
    save_news_data_to_excel(news_data)
    # browser.close_browser()

if __name__ == "__main__":
    main()