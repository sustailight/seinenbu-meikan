import os
import json
import requests
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from jinja2 import Environment, FileSystemLoader

# Github Secretsから環境変数として渡される認証情報
CREDENTIALS_JSON = os.environ.get('GOOGLE_CREDENTIALS_JSON')

# ======== ここを編集してください ========
# スプレッドシートID
SPREADSHEET_ID = '1tZVv9lTnvjS3vtP7GKLdu9sYwSWjgQCSkZikxruPkYI'
# 取得するシート名と範囲
RANGE_NAME = 'フォームの回答 1!A:Z' 
# ======================================

def get_sheet_data():
    creds = None
    if CREDENTIALS_JSON:
        creds_dict = json.loads(CREDENTIALS_JSON)
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
    else:
        # ローカル確認用
        local_json_path = r'C:\Users\suzuk\.antigravity\seinenbu-meikn\stone-citizen-492915-a0-36bd2df513d6.json'
        if os.path.exists(local_json_path):
            with open(local_json_path, 'r', encoding='utf-8') as f:
                creds_dict = json.load(f)
            creds = service_account.Credentials.from_service_account_info(
                creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )

    if not creds:
        print("[注意] 認証情報が見つかりません。")
        return []

    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    
    if not values:
        print("シートにデータが見つかりませんでした。")
        return []
    
    headers = values[0]
    members = []
    timestamp_str = datetime.now().strftime('%Y%m%d%H%M')
    
    for row in values[1:]:
        member = {}
        for i, header in enumerate(headers):
            val = row[i] if i < len(row) else ''
            member[header] = val
            
        # ニックネームを取得するための正規化（あらゆる表記揺れを吸収）
        member['display_nickname'] = member.get('ニックネーム') or member.get('①お名前（＆呼ばれたいニックネーム）') or member.get('呼ばれたいニックネーム') or '名称未設定'

        # 画像URLの処理
        img_url = ''
        # 画像列のキーワードを探す
        for k in member.keys():
            if 'ベストショット' in k or '写真' in k or 'ショット' in k:
                img_url = member.get(k, '')
                break

        if img_url:
            file_id = None
            if 'open?id=' in img_url:
                file_id = img_url.split('open?id=')[1].split('&')[0]
            elif '/file/d/' in img_url:
                file_id = img_url.split('/file/d/')[1].split('/')[0]

            if file_id:
                img_dir = 'images'
                if not os.path.exists(img_dir):
                    os.makedirs(img_dir)
                local_path = f"{img_dir}/{file_id}.jpg"
                
                if not os.path.exists(local_path):
                    dl_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                    try:
                        r = requests.get(dl_url, allow_redirects=True, timeout=10)
                        if r.status_code == 200 and 'image' in r.headers.get('Content-Type', ''):
                            with open(local_path, 'wb') as f:
                                f.write(r.content)
                    except Exception as e:
                        print(f"画像ダウンロードエラー: {e}")
                
                if os.path.exists(local_path):
                    member['photo_url'] = f"./{local_path}?v={timestamp_str}"
                else:
                    member['photo_url'] = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
            
        # 不要なタイムスタンプ列の削除（文字化け回避のため慎重に）
        keys_to_del = [k for k in member.keys() if 'タイムスタンプ' in k]
        for k in keys_to_del:
            del member[k]
            
        members.append(member)
        
    return members

def main():
    print("データ取得を開始します...")
    members = get_sheet_data()
    print(f"{len(members)}名分のデータを取得。HTMLビルド中...")
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    html_out = template.render(members=members)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_out)
    print("成功しました。")

if __name__ == '__main__':
    main()
