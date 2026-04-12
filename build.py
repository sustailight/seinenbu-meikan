import os
import json
import requests
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from jinja2 import Environment, FileSystemLoader

# Github Secretsから環境変数として渡される認証情報
CREDENTIALS_JSON = os.environ.get('GOOGLE_CREDENTIALS_JSON')

# ======== 設定項目 ========
SPREADSHEET_ID = '1tZVv9lTnvjS3vtP7GKLdu9sYwSWjgQCSkZikxruPkYI'
RANGE_NAME = 'フォームの回答 1!A:Z' 
# ========================

def get_sheet_data():
    creds = None
    if CREDENTIALS_JSON:
        creds_dict = json.loads(CREDENTIALS_JSON)
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
    else:
        local_json_path = r'C:\Users\suzuk\.antigravity\seinenbu-meikn\stone-citizen-492915-a0-36bd2df513d6.json'
        if os.path.exists(local_json_path):
            with open(local_json_path, 'r', encoding='utf-8') as f:
                creds_dict = json.load(f)
            creds = service_account.Credentials.from_service_account_info(
                creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )

    if not creds:
        print("Error: No Credentials found.")
        return []

    service = build('sheets', 'v4', credentials=creds)
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    
    if not values:
        return []
    
    headers = values[0]
    members = []
    timestamp_str = datetime.now().strftime('%Y%m%d%H%M')

    # デバッグ用に取得したヘッダーを表示
    print(f"Headers found: {headers}")
    
    for row in values[1:]:
        row_data = row + [''] * (len(headers) - len(row))
        member_raw = dict(zip(headers, row_data))
        member = {}
        
        # --- 超堅牢なマッピング（キーワード部分一致で探す） ---
        
        # 1. ニックネーム
        for k, v in member_raw.items():
            if 'ニックネーム' in k:
                member['display_nickname'] = v
                break
        if not member.get('display_nickname'): member['display_nickname'] = '名称未設定'

        # 2. 氏名
        for k, v in member_raw.items():
            if k == '氏名' or 'お名前' in k:
                member['display_name'] = v
                break
        if not member.get('display_name'): member['display_name'] = '氏名未登録'

        # 3. 会社名 / 業種
        for k, v in member_raw.items():
            if '会社名' in k: member['display_company'] = v
            if '業種' in k: member['display_industry'] = v
        
        # 4. 詳細項目
        for k, v in member_raw.items():
            if '自慢' in k: member['pr_text'] = v
            if '熱中' in k: member['hobby_text'] = v
            if 'グルメ' in k: member['gourmet_text'] = v
            if '相談' in k: member['consult_text'] = v

        # 5. 写真 (キーワード「ベストショット」か「写真」が含まれる列)
        img_url = ''
        for k, v in member_raw.items():
            if 'ベストショット' in k or '写真' in k:
                img_url = v
                break
        
        member['photo_url'] = ''
        if img_url:
            file_id = None
            if 'open?id=' in img_url:
                file_id = img_url.split('open?id=')[1].split('&')[0]
            elif '/file/d/' in img_url:
                file_id = img_url.split('/file/d/')[1].split('/')[0]

            if file_id:
                img_dir = 'images'
                if not os.path.exists(img_dir): os.makedirs(img_dir)
                local_path = f"{img_dir}/{file_id}.jpg"
                
                if not os.path.exists(local_path):
                    dl_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                    try:
                        r = requests.get(dl_url, allow_redirects=True, timeout=10)
                        if r.status_code == 200 and 'image' in r.headers.get('Content-Type', ''):
                            with open(local_path, 'wb') as f: f.write(r.content)
                    except: pass
                
                if os.path.exists(local_path):
                    member['photo_url'] = f"./{local_path}?v={timestamp_str}"
                else:
                    # ダウンロード不可時のフォールバック
                    member['photo_url'] = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
            
        members.append(member)
        
    return members

def main():
    members = get_sheet_data()
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    html_out = template.render(members=members)
    with open('index.html', 'w', encoding='utf-8-sig') as f:
        f.write(html_out)
    print("Build Success.")

if __name__ == '__main__':
    main()
