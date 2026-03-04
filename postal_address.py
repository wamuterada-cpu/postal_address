"""
■Pythonの課題
以下の使用のプログラムを作成する

【処理概要】
pythonプログラムを郵便番号をパラメータとして指定し、コマンドラインから実行するとパラメータに指定した郵便番号に紐づく住所データがDBに取り込まれる処理を実装する

【仕様】
機能要件：
・下記のAPIの利用を前提とする
　https://zip.cgis.biz/
・DBに取り込むAPIレスポンスのデータ以下とする(NULLを許容)
　郵便番号、
　都道府県、
　都道府県カナ、
　市区町村、
　市区町村カナ、
　住所、
　住所カナ、
　事業所名、
　事業所名カナ
・DB側のデータ格納先に関しては指定なし
非機能要件：
・コーディング規約はPEP8に準拠するものとする(努力目標)
　https://pep8-ja.readthedocs.io/ja/latest/
"""

#3/2 作成開始

import sys
import psycopg2 #PostgreSQLとのパイプ
import requests #APIを取得する
import xml.etree.cElementTree as ET #xmlの中身を取り出したりする
import os
from dotenv import load_dotenv

load_dotenv()

def db_connection():
    try:
        conn=psycopg2.connect(#接続の定義
            host="localhost",
            dbname="Database",
            user="postgres",
            password=os.getenv("DB_PASSWORD")
        )
        print("成功")
        return conn
    except Exception as e:
        print(f"失敗{e}")

def fetch_address_xml(zip_code): #APIからxmlデータを取得する
    # 魔法の呪文（パス）を全部繋げるにゃ！
    url = f"https://zip.cgis.biz/xml/zip.php?zn={zip_code}"#fにより値を埋め込めるようにする。リクエストの組み立て
    try:
        #print(f"--- 突撃するURL: {url} ---") 
        response=requests.get(url) #先ほどのurlのリクエストの取得
        response.raise_for_status()#エラーのチェック
        return response.content #xmlを返す
    except Exception as e:
        print(f"API取得失敗{e}")

def parse_address_xml(zip_code,xml_content): #取得したxmlの解析
    root=ET.fromstring(xml_content) #中身を探す
    values=root.findall('.//value')
    if not values:
        return None
    data={"郵便番号":zip_code}
    for val in root.findall('.//value'): #属性を取り出す
        data.update(val.attrib)
    return{
        "郵便番号":zip_code,
        "都道府県":data.get('state'),
        "都道府県カナ":data.get('state_kana'),
        "市区町村":data.get('city'),
        "市区町村カナ":data.get('city_kana'),
        "住所":data.get('address'),
        "住所カナ":data.get('address_kana'),
        "事業所名":data.get('company'),
        "事業所名カナ":data.get('company_kana')
    }


def save_to_db(conn,data): #解析したxmlをpostgresqlに反映#郵便番号が重複した場合は更新する
    sql="""insert into dev.postal_addresses(
        "郵便番号","都道府県","都道府県カナ","市区町村","市区町村カナ",
        "住所","住所カナ","事業所名","事業所名カナ")
        values(
        %(郵便番号)s,%(都道府県)s,%(都道府県カナ)s,%(市区町村)s,%(市区町村カナ)s,
        %(住所)s,%(住所カナ)s,%(事業所名)s,%(事業所名カナ)s)
        on conflict ("郵便番号")
        do update set 
        "都道府県"=excluded."都道府県",
        "都道府県カナ"=excluded."都道府県カナ",
        "市区町村"=excluded."市区町村",
        "市区町村カナ"=excluded."市区町村カナ",
        "住所"=excluded."住所",
        "住所カナ"=excluded."住所カナ",
        "事業所名"=excluded."事業所名",
        "事業所名カナ"=excluded."事業所名カナ";
        """
    try: #カーソルをオープン
        with conn.cursor() as cur:
            cur.execute(sql,data) #sqlにdataをはめ込む
            conn.commit() #実行
    except Exception as e:
        conn.rollback()
        print(f"失敗{e}")

def display_stored_address(conn):
    try:
        with conn.cursor() as cur:
            cur.execute('select * from dev.postal_addresses order by "郵便番号" asc;') #番号順に並べる
            rows=cur.fetchall()
            for row in rows:
                print(row)
    except Exception as e:
        print(f"失敗{e}")

def main():
    if len(sys.argv)<2: #リスト内にいくつの要素があるか数える
        print("="*30)
        print("エラー：郵便番号を入力してください")
        print("="*30)
        return
    
    zip_code=sys.argv[1] #リストの1番目に入ってる郵便番号をzip_codeに入れる
    if not zip_code.isdigit() or len(zip_code)!=7: #数字あるいは7桁でない場合はエラー
        print("="*30)
        print("エラー:郵便番号は7桁の数字で入力してください")
        print("="*30)
        return
        
    xml_content=fetch_address_xml(zip_code)#APIからxmlを取得
    if xml_content is None:
        print("="*30)
        print(f"エラー:郵便番号{zip_code}に対応する住所は見つかりませんでした")
        print("="*30)
        return
    
    address_data=parse_address_xml(zip_code,xml_content) #xmlを解析する
    if address_data is None:
        print("="*30)
        print(f"エラー:郵便番号{zip_code}に対応する住所は見つかりませんでした")
        print("="*30)
        return
    
    conn=db_connection() #DBに接続
    if conn:
        save_to_db(conn,address_data)
        conn.close()
        print(f"郵便番号{zip_code}をデータベースに保存しました")
        

if __name__=="__main__":
    main()