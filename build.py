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
    
    for row in values[1:]:
        # 行の長さを見出しに合わせる
        row_data = row + [''] * (len(headers) - len(row))
        member = dict(zip(headers, row_data))
        
        # --- 表示用データのマッピング（新シートの正確な見出し名に準拠） ---
        
        # 1. ニックネーム（写真の上に表示）
        member['display_nickname'] = member.get('①呼ばれたいニックネーム') or member.get('ニックネーム') or '名称未設定'
        
        # 2. 氏名（カード中央）
        member['display_name'] = member.get('氏名') or '氏名未登録'
        
        # 3. 会社名 / 業種
        member['display_company'] = member.get('②会社名') or ''
        member['display_industry'] = member.get('③業種（カテゴリ）') or ''
        
        # 4. 詳細項目
        member['pr_text'] = member.get('④「わが社」をひとことで自慢してください！') or ''
        member['hobby_text'] = member.get('⑤今、これに熱中しています！（趣味・推し）') or ''
        member['gourmet_text'] = member.get('⑥おすすめ「激うまグルメ」は？  ') or ''
        member['consult_text'] = member.get('⑦こんな相談、のれます！（あなたの得意・ギブ）') or ''

        # 5. 写真 (⑨あなたらしさが伝わるベストショット📷)
        img_url = member.get('⑨あなたらしさが伝わるベストショット📷') or ''
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
                
                # 自動ダウンロード試行
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
                    member['photo_url'] = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
            
        members.append(member)
        
    return members

def main():
    members = get_sheet_data()
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    html_out = template.render(members=members)
    # BOM付きUTF-8で保存して文字化けをより確実に防ぐ
    with open('index.html', 'w', encoding='utf-8-sig') as f:
        f.write(html_out)
    print("Build Success.")

if __name__ == '__main__':
    main()
