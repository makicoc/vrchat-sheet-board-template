# MAKIスプレッド掲示板 GitHubテンプレート

Google Sheetsの公開CSVを読み込み、VRChat向けの `board.json` としてGitHub Pagesに公開するテンプレートです。

## 使い方

1. このリポジトリを自分のGitHubアカウントへ複製します。
2. Google Sheetsに `title`, `body`, `date`, `color` の列を作ります。
3. Google Sheetsを「ウェブに公開」し、CSV URLをコピーします。
4. `config.json` の `sheet_csv_url` にCSV URLを貼ります。
5. GitHub Pagesを有効にします。
6. Actionsの「お知らせを同期して公開」を実行します。
7. 表示された `https://ユーザー名.github.io/リポジトリ名` をUnityの「公開掲示板URL」に貼ります。

`max_items` は0なら制限なしです。件数や本文が多いほど、VRChat内での読み込み・表示が重くなります。
