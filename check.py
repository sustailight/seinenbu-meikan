import sys
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build

sys.stdout.reconfigure(encoding='utf-8')

creds_json_path = r'd:\ドキュメント\msr\ダウンロード2\stone-citizen-492915-a0-36bd2df513d6.json'
SPREADSHEET_ID = '12rdMwtFwLZj8vnxBxMzEVJ8_hcYw6Is8dLom8JL2c1Q'

try:
    with open(creds_json_path, 'r', encoding='utf-8') as f:
        creds_dict = json.load(f)

    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    service = build('sheets', 'v4', credentials=creds)

    sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheets = sheet_metadata.get('sheets', '')
    title = sheets[0].get('properties', {}).get('title', '')
    print('Target Sheet:', title)

    # rangeを f'{title}!A:Z' にする
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=f'{title}!A:Z').execute()
    values = result.get('values', [])
    if values:
        print('Headers:', json.dumps(values[0], ensure_ascii=False))
        if len(values) > 1:
            print('Row1:', json.dumps(values[1], ensure_ascii=False))
    else:
        print('No data found.')
except Exception as e:
    print('ERROR:', e)
