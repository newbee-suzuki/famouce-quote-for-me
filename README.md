# Famous Quote Manager

英語の名言をJSONL形式で保存し、PythonのCUIから登録・削除・検索できます。
外部パッケージは不要です（Python 3.9以上）。

## データ形式

`data/quotes.jsonl` の1行が1件のJSONです。

```json
{"id":"a1b2c3d4e5f6","type":"quote","text":"Stay hungry, stay foolish.","author":"Steve Jobs","tag":["life","motivation"]}
```

- `id`: 登録時に自動生成される一意なID
- `type`: 現在は `quote`。将来ほかの種類を追加可能
- `text`: 英語の名言本文
- `author`: 著者
- `tag`: タグの配列（0件以上）

## 使い方

引数なしで対話メニューを起動します。

```powershell
python quote_manager.py
```

コマンドを直接指定することもできます。

```powershell
python quote_manager.py add --text "Stay hungry, stay foolish." --author "Steve Jobs" --tag life --tag motivation
python quote_manager.py list
python quote_manager.py search hungry
python quote_manager.py search --author "Steve Jobs"
python quote_manager.py search --tag motivation
python quote_manager.py delete a1b2c3d4e5f6
```

別のJSONLファイルを使う場合は、サブコマンドより前に `--file` を指定します。

```powershell
python quote_manager.py --file my_quotes.jsonl list
```

## テスト

```powershell
python -m unittest discover -s tests -v
```
