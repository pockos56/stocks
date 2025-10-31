import requests
import numpy as np
from bs4 import BeautifulSoup
import pandas as pd
import time
import math
from datetime import datetime
import re
import os
import tqdm
import random
import argparse
from IPython.display import HTML

# Import mode
parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["fast", "full"], default="fast")
args = parser.parse_args()
mode = args.mode

NO_ANALYSTS_IN_MARKETBEAT = 2691
manual_list = np.unique(np.array(["Gerard Cassidy", "Tom O Malley", "Patrick R. Trucchio", "Vamil Divan", "Mark Lipacis", "Jason Seidl","Quinn Bolton", "Dan Payne", "Scot Ciccarelli", "Rick Schafer", "Ross Seymore", "Patrick Brown", "Colin Rusch", "Shaul Eyal", "Jesse Sobelson", "Tore Svanberg", "James Lee", "Matthew Sheerin", "Matthew Cost", "Adam Borg", "Nicholas Jones", "Christopher Stathoulopoulos", "Trey Grooms", "Clark Lampen", "Bill Peterson", "Chris Kotowski", "Ebrahim Poonawala", "Mark Palmer", "Mark Mahaney", "Brent Thielman", "Christopher Allen", "Daniel Fannon", "Mike Mayo", "Michael Grondahl", "William Appicelli"]))

def analyst_ranks(end_number=NO_ANALYSTS_IN_MARKETBEAT, manual_list=manual_list, mode=mode, top_no = 100, acceptance_percentage = 0.9, max_iterations = 1000):

    # Links
    marketbeat_analyst_url = 'https://www.marketbeat.com/all-access/analyst-rankings/'
    ANALYST_URL = "https://stockanalysis.com/analysts/"

    # Step 1: Collect all analyst names
    def retrieve_analyst_names(start=1, end=end_number):
        # Recover file
        df = pd.DataFrame([])
        try:
            df = pd.read_csv(os.path.join('data', 'analysts_names.csv'))
        except:
            print('CSV file not found. Searching the web to retrieve analyst names.')
            pass

        # If a new analysts_name list needs to be created:
        if (len(df) < 0.8*(end-start)):
    
            auto_list = np.array([])
            for number_i in tqdm.tqdm(range(start,end), desc='Finding analyst names'):

                #Retrieve text from URL
                response = requests.get(marketbeat_analyst_url + f'{number_i}/', headers={"User-Agent": "Mozilla/5.0"})
                text = BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True)
                time.sleep(random.uniform(2, 3))

                #Retrieve name 
                match = re.search(r'(\b\w+\b)\s+(\b\w+\b)\s+is a stock analyst', text)
                if match:
                    name_i = f"{match.group(1)} {match.group(2)}"
                    auto_list = np.append(auto_list, name_i)
            # Save, print, return
            df = pd.DataFrame(data = {'Names':auto_list})
            df.to_csv(os.path.join('data','analysts_names.csv'), index=False)
            print(f"Found {len(df)} analyst pages and saved as 'data/analysts_names.csv'.")
        else:

            print(f"Retrieved {len(df)} analyst names from 'data/analysts_names.csv'.")
        
        return np.array(df['Names'])

    auto_list = retrieve_analyst_names()

    # Step 2: Visit each analyst page and extract rank

    # If available, sort and save the analysts_name based on previous data so as to focus on promising analysts and reduce computation time
    if (len(np.array(os.listdir('from-Stocks/'))[['top_analysts' in i for i in os.listdir('from-Stocks/')]]) > 0) & (mode == 'fast'):
        latest_file = np.sort(np.array(os.listdir('from-Stocks/'))[['full_top_analysts.csv' in i for i in os.listdir('from-Stocks/')]])[-1]
        latest_file_csv = pd.read_csv(os.path.join('from-Stocks', f'{latest_file}'))
        list = latest_file_csv[latest_file_csv['Ranking'] > 0]['Analyst name'].reset_index(drop=True)
    elif mode == 'full':
        list = np.unique(np.append(auto_list, manual_list))
    else:
        print(f"Error: {TypeError('Define mode as fast or full')}. Please try again!")
        time.sleep(600)

    analyst_data = pd.DataFrame(data = {'Analyst name': list,
                                        'Ranking': random.randint(9900,9999),
                                        'URL': 'empty',
                                        'Last update': 'Not found'})

    for i in tqdm.tqdm(range(0, len(analyst_data))):
        if mode == "fast":
            rankings_so_far = np.unique(analyst_data["Ranking"])
            top = top_no + 1
            success_ratio = (sum([i in rankings_so_far for i in np.array(range(1,top))])) / top
            if (success_ratio == 1):
                print(f"Top{top_no} analysts list complete! Stopping the process!")
                break
            elif (success_ratio > acceptance_percentage) and (i > 2*top):
                print(f"{(round((100*success_ratio), ndigits=1))}% out of top{top_no} analysts found. Stopping the process!")
                break
            elif (i >= max_iterations):
                print(f"Max iterations ({max_iterations}) reached. Stopping the process!")
                break
      
        # Create URL for analyst's name
        analyst_i_url = ANALYST_URL
        for subname_i in analyst_data['Analyst name'][i].strip().split(" "):
            analyst_i_url = analyst_i_url + f"{subname_i}-"
        analyst_i_url = analyst_i_url[0:-1] + "/"


        # Try to retrieve info from URL
        try:
            # Request URL
            res = requests.get(analyst_i_url, headers={"User-Agent": "Mozilla/5.0"})
            s = BeautifulSoup(res.text, "html.parser")

            # Insert humanized name and URL to DataFrame
            #analyst_data.loc[i,"Analyst name (humanized)"] = s.find("h1").get_text(strip=True)
            analyst_data.loc[i,"URL"] = analyst_i_url

            # Insert last recommendation to DataFrame
            pattern = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (?:0?[1-9]|[12][0-9]|3[01]), (?:199\d|20[0-5]\d)\b'
            match = re.search(pattern, s.text)
            if match:
                analyst_data.loc[i,"Last update"] = str(datetime.strptime(match.group(), "%b %d, %Y").strftime("%d %b %Y"))

            # Retrieve ranking
            match = re.search(r'rank:\s*#?(\d+)', s.find(string=lambda t:'rank:' in t).lower())
            rank_number = None
            if match:
                rank_number = int(match.group(1))
            analyst_data.loc[i,"Ranking"] = rank_number

        except Exception as e:
            time.sleep(10)
            print(f"\nError reading {analyst_data['Analyst name'][i]}: {e}")
            pass

        # Sleep to avoid hitting the server too fast
        if ((i % 50) == 0) & (i != 0):
            time.sleep(random.uniform(20, 25))
        else:
            time.sleep(random.uniform(2, 3))

    # Step 3: Sort by rank and show the top ones
    analyst_data = analyst_data.dropna(subset=["Ranking"]).sort_values("Ranking")
    
    # Create local folder
    folder = "from-Stocks"
    os.makedirs(folder, exist_ok=True)

    # Save results
    file_dir_timestamp = os.path.join(folder, f"{datetime.now().strftime('%Y%m%d')}_{mode}_top_analysts")
    analyst_data.to_csv(f'{file_dir_timestamp}.csv', index=False)
    file_dir_latest = os.path.join(folder, 'latest_top_analysts')
    analyst_data.to_csv(f'{file_dir_latest}.csv', index=False)

    # Create latest HTML
    # --- Styling functions ---

    def color_by_date(date_str):
        try:
            days_diff = (datetime.now() - datetime.strptime(date_str, "%d %b %Y")).days
        except Exception:
            return ""  # Skip invalid dates
        
        # 0 days = fully opaque, 60+ days = very transparent
        alpha = max(0.2, 1 - math.log(max(days_diff, 2)) / 3)
        return f"background-color: rgba(0, 180, 0, {alpha}); color: white;"

    def make_clickable(val):
        return f'<a target="_blank" href="{val}">{val}</a>' if isinstance(val, str) and val.startswith("http") else val

    # --- Apply styles ---
    styled = (
        analyst_data.style
        .format({'URL': make_clickable})
        .apply(lambda s: [color_by_date(d) if s.name == "Last update" else "" for d in s], axis=0)
    )    

    # Save using to_html() while prepending timestamp text
    timestamp = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    with open(file_dir_latest, "w", encoding="utf-8") as f:
        f.write(f"<p style='font-family:Arial; font-size:14px; color:gray;'>Generated on: {timestamp}</p>\n")
        styled.to_html(f, render_links=True, escape=False)

    # Print snapshot    
    print(analyst_data.loc[analyst_data['Ranking']>0,:].head(10))
    return analyst_data

results = analyst_ranks()

