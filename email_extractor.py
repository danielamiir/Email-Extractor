# REGEX BASED - Working example of retrieving emails from one page on a website

import re
import os
import requests
from urllib.parse import urlsplit
from collections import deque
from bs4 import BeautifulSoup
import pandas as pd
from googlesearch import search as google_search

def find_emails(text, website_ending):
    # Set for all emais
    emails = set()

    website_endings = ["se", "com", "net", "nu"]
    website_endings.append(website_ending) # Add the current ending
    website_endings = list(set(website_endings)) # Remove duplicates

    # Loop through all endpoints and extract emails
    for ending in website_endings:
        new_emails = set(re.findall(rf"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.{ending}", text, re.I))
        emails.update(new_emails)

    # Make all emails to lower case and return as list
    return list({email.casefold() for email in emails})

# Google Search
search_queries = ["webbyrå stockholm", "webbyrå göteborg"] # Search queries
num_search_limit = 100 # Number of results to retrieve from Google search per search query

urls_to_scrape = []

for search_query in search_queries:
    url_index = 0
    for url_result in google_search(search_query, tld="se", num=num_search_limit, stop=num_search_limit, pause=2):
        
        # Extract the base url
        parts = urlsplit(url_result)
        base_url = "{0.scheme}://{0.netloc}".format(parts)
        
        # Check if the url has already been handled. If it has but the new ranking is higher (lower number) delete and replace
        run_continue = False
        list_len = len(urls_to_scrape)
        for i in range(0, list_len):
            if urls_to_scrape[i]['base_url'] == base_url:
                if urls_to_scrape[i]['search_ranking'] > url_index: # If the new ranking is higher (lower number) - delete the old one
                    del urls_to_scrape[i]
                else: # If the old ranking is higher (lower number) run continue / Skip this one
                    run_continue = True
                break # Break when found

        if run_continue:
            continue # Skip if the base url has already been added to the list to scrape

        url_index += 1 # Add 1 to url index to know the search rank

        # Obj with all relevant url search info
        url_obj = {
            'base_url': base_url,
            'search_query': search_query,
            'search_ranking': url_index
        }
        urls_to_scrape.append(url_obj) # Add base url to list or urls to scrape

df = pd.DataFrame(columns = ['Company', 'Description', 'Emails', 'Search Ranking', 'Search Query']) # Create empty df for all data

for url_obj in urls_to_scrape:

    print("Crawling URL %s" % url_obj['base_url'])
    try:
        response = requests.get(url_obj['base_url'])
    except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
        continue
    
    # Find emails
    website_ending = base_url.split(".")[-1] # Extract the websites ending
    emails = find_emails(response.text, website_ending)
    
    if len(emails) == 0:
        print("No emails found.")

    soup = BeautifulSoup(response.text, 'lxml')

    # Find SEO Meta Description
    meta_tag = soup.find('meta', attrs={'name': 'description'})
    if meta_tag:
        try:
            meta_description = str(meta_tag).split('content="')[1]
        except:
            print("Error wit  meta tag. Setting variable to empty string.")
            meta_description = ""
    else:
        print("No meta tag found. Setting variable to empty string.")
        meta_description = ""

    # Create temp df with data from this company
    temp_df = pd.DataFrame({"Company":[url_obj['base_url']], "Description":[meta_description], "Emails": [", ".join(emails)], "Search Ranking": [url_obj['search_ranking']], "Search Query": [url_obj['search_query']]})

    # Append temp_df to main df
    df = df.append(temp_df, ignore_index=True)

desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') # Extract desktop path
df.to_excel(desktop_path + "/Email Extractor.xlsx", index=False) # Save df to Excel on Desktop
print("Saved DF with all data to Excel on Desktop")