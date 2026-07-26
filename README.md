# MAKIスプレッド掲示板 GitHubテンプレート

Google Sheetsの公開CSVを読み込み、VRChat向けの `board.json` としてGitHub Pagesに公開するテンプレートです。

## 使い方

1. このリポジトリを自分のGitHubアカウントへ複製します。
2. 商品に同梱されている `MAKISheetBoard_SheetTemplate.xlsx` をGoogle Sheetsへインポートします。
3. Google Sheets上で、お知らせ内容を書き換えます。
4. Google Sheetsを「ウェブに公開」し、CSV URLをコピーします。
5. `config.json` の `sheet_csv_url` にCSV URLを貼ります。
6. GitHub Pagesを有効にします。
7. Actionsの「お知らせを同期して公開」を実行します。
8. 表示された `https://ユーザー名.github.io/リポジトリ名` をUnityの「公開掲示板URL」に貼ります。

この商品は最大8件まで表示します。`max_items` は8のまま変更しないでください。新しいお知らせを追加する時は、不要な古いお知らせをGoogle Sheetsから削除してください。

## CSVの列

- `title`: お知らせタイトル
- `body`: 本文
- `date`: 日付や補足表示
- `color`: 色名。`青`, `ピンク`, `緑`, `黄`, `紫`, `オレンジ`, `グレー` が使えます。

上級者向けに、`#AFCBFF` のような `#RRGGBB` 形式も使えます。
