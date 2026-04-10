import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from jinja2 import Environment, FileSystemLoader

# Github Secretsから環境変数として渡される認証情報
CREDENTIALS_JSON = os.environ.get('GOOGLE_CREDENTIALS_JSON')

# ======== ここを編集してください ========
# スプレッドシートID（URLの /d/ と /edit の間の文字列）
SPREADSHEET_ID = '12rdMwtFwLZj8vnxBxMzEVJ8_hcYw6Is8dLom8JL2c1Q'
# 取得するシート名と範囲
RANGE_NAME = 'フォームの回答 1!A:Z' 
# ======================================

def get_sheet_data():
    # 認証情報がセットされていない場合は、ローカルテスト用のダミーデータを返す
    if not CREDENTIALS_JSON:
        print("[注意] GOOGLE_CREDENTIALS_JSON が設定されていません。構築テスト用のダミーデータで HTML を生成します。")
        return [
            {
                '氏名': '山田 太郎', 'ニックネーム': 'ヤマちゃん', '役職': '部長', '会社名': '山田建設(株)', 
                '画像URL': 'https://placehold.co/400x500/00205b/c5a059?text=Yamada', 
                '事業内容': '建築一式、およびそれに付随するサービス全般。\n地域密着で頑張っています。\nよろしくお願いします。\nここは長文なのでモーダルで展開されます。', 
                '一言メッセージ': '青年部を盛り上げていきましょう！'
            },
            {
                '氏名': '鈴木 花子', 'ニックネーム': 'ハナ', '役職': '副部長', '会社名': '鈴木デザイン', 
                '画像URL': 'https://placehold.co/400x500/00205b/c5a059?text=Suzuki', 
                '事業内容': 'ウェブデザイン、グラフィックデザイン。', 
                '一言メッセージ': '短文の場合はもっと見るボタンが出ません。'
            }
        ]

    # Google Sheets APIの認証処理
    creds_dict = json.loads(CREDENTIALS_JSON)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    
    if not values:
        print("シートにデータが見つかりませんでした。")
        return []
    
    # 1行目をヘッダー（キー）として扱う
    headers = values[0]
    members = []
    
    # キャッシュバスティング用のタイムスタンプ
    timestamp_str = datetime.now().strftime('%Y%m%d%H%M')
    
    # 2行目以降のデータをJSON化
    for row in values[1:]:
        member = {}
        for i, header in enumerate(headers):
            # 行のデータが途中で途切れている場合は空文字を入れる
            val = row[i] if i < len(row) else ''
            member[header] = val
            
        # 画像URLの変換処理 (Google Driveの open?id= を表示用の uc?id= に置換)
        img_url = member.get('画像URL', '')
        if img_url and 'open?id=' in img_url:
            img_url = img_url.replace('open?id=', 'uc?id=')
            img_url += f"&v={timestamp_str}" # キャッシュ化回避用クエリ追記
            member['画像URL'] = img_url
            
        # UIからタイムスタンプ列を除外したい為、データ自体から削除してしまう（任意）
        if 'タイムスタンプ' in member:
            del member['タイムスタンプ']
            
        members.append(member)
        
    return members

def main():
    print("データ取得を開始します...")
    members = get_sheet_data()
    
    print(f"{len(members)}名分のデータを取得しました。HTMLをビルドします...")
    
    # Jinja2でテンプレートエンジン設定
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    
    # members配列を渡してHTMLを生成
    html_out = template.render(members=members)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_out)
        
    print("index.html のビルドが成功しました。")

if __name__ == '__main__':
    main()
