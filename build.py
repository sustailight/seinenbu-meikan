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
    creds = None
    # もし環境変数があれば（GitHub上なら）それを使う
    if CREDENTIALS_JSON:
        creds_dict = json.loads(CREDENTIALS_JSON)
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
    else:
        # ローカル確認用：パスから直でJSONを読む
        local_json_path = r'D:\ドキュメント\msr\ダウンロード2\stone-citizen-492915-a0-36bd2df513d6.json'
        if os.path.exists(local_json_path):
            with open(local_json_path, 'r', encoding='utf-8') as f:
                creds_dict = json.load(f)
            creds = service_account.Credentials.from_service_account_info(
                creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )

    if not creds:
        print("[注意] 認証情報が見つかりません。ダミーデータを使用します。")
        dummy_data = []
        for i in range(1, 51):
            has_image = (i % 3 != 0) # 3人に1人は画像なし
            dummy_data.append({
                '①お名前（＆呼ばれたいニックネーム）': f'テスト 会員{i} (ニック{i})',
                '③業種（カテゴリ）': f'業種パターン{i % 4 + 1}',
                '②会社名': f'テストカンパニー{i}株式会社',
                '⑧あなたらしさが伝わるベストショット📷': f'https://placehold.co/400x500/00205b/c5a059?text=Member+{i}' if has_image else '',
                '④「わが社」をひとことで自慢してください！': f'地域密着で頑張っています！\nテストデータですが、{i}番目の会社は特にここがスゴイ！\n（ちなみに長文になると自動で文字が省略されてもっと見るボタンが出ます）' if i % 2 == 0 else '一言自慢です！',
                '⑤今、これに熱中しています！（趣味・推し）': 'サウナとゴルフ' if i % 2 == 0 else '',
                '⑥おすすめ「激うまグルメ」は？  ': '駅前の焼肉屋、絶対行くべき！' if i % 3 == 0 else '',
                '⑦こんな相談、のれます！（あなたの得意・ギブ）': '法律相談や資金繰りなど、なんでも頼ってください！'
            })
        return dummy_data

    
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
        img_url = member.get('⑧あなたらしさが伝わるベストショット📷', '')
        if img_url and 'open?id=' in img_url:
            img_url = img_url.replace('open?id=', 'uc?id=')
            img_url += f"&v={timestamp_str}" # キャッシュ化回避用クエリ追記
            member['⑧あなたらしさが伝わるベストショット📷'] = img_url
            
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
