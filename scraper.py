import time
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
import schedule


SPREADSHEET_ID = '1pCpjOGxi8mEc2QYa8ETW-_niD7VEa8XIC0OP9mWHi3E'
SERVICE_ACCOUNT_FILE = 'service.json'
SCRAPE_INTERVAL = 300
RANGE_NAME = 'Sheet1!A:Z'


def scrape():
    url = "https://vmc.gov.in/waterlevelsensor/WaterLevel.aspx"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    scrape_data = []
    table = soup.find('table', id='GridView1')
    rows = table.find_all('tr')[2:]  # Skip the header rows
    for row in rows[0::2]:
        cols = row.find_all('td')
        location = cols[0].text.strip()
        water_level = cols[2].text.strip()
        date_time = cols[3].text.strip()
        scrape_data.append([location, water_level, date_time])
    return scrape_data


def prep_data(scraped_data):
    prepared_data = [''] * 20
    
    # Map of location names to column indices
    location_map = {
        'AJWA DAM': 0,
        'AKOTA BRIDGE': 2,
        'ASOJ FEEDER': 4,
        'BAHUCHARAJI BRIDGE': 6,
        'KALA GHODA': 8,
        'MANGAL PANDEY BRIDGE': 10,
        'MUJMAUDA BRIDGE': 12,
        'PRATAPPURA DAM': 14,
        'SAMA HARNI BRIDGE': 16,
        'VADSAR BRIDGE': 18
    }
    
    for location, level, timestamp in scraped_data:
        if location in location_map:
            index = location_map[location]
            prepared_data[index] = level
            prepared_data[index + 1] = timestamp
    
    return [prepared_data]


def update_sheet(data):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets']
    )

    try:
        service = build('sheets', 'v4', credentials=credentials)
        body = {'values': data}
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
            valueInputOption='USER_ENTERED', body=body).execute()
        print(f"{result.get('updates').get('updatedCells')} cells updated.")
    except HttpError as error:
        print(f"An error occurred: {error}")


def job():
    scraped_data = scrape()
    prepared_data = prep_data(scraped_data)
    update_sheet(prepared_data)


schedule.every(5).minutes.do(job)
    
if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(1)
