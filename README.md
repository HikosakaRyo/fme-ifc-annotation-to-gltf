# fme-ifc-annotation-to-gltf

[プログマのプログラマ日記](https://rhikos-prgm.hatenablog.com/)の記事の

[ifcの注記もglTFに変換しようとして、うまくいったけどうまくいかなかった話](https://rhikos-prgm.hatenablog.com/entry/2023/02/10/091526)

関連のソースコードを共有するためのリポジトリです。

FMEを利用してifc(Industry Foundation Class)ファイルからIfcAnnotationを抽出し、annotationに含まれるテキスト情報をglTFに変換するプロジェクトです。  
glTFはテキストのバウンディングボックスの座標でいたポリゴンを生成して、テキストを画像化したテクスチャを貼り付けることで生成します。  

## 動作確認バージョン

このプロジェクトは以下の環境で動作確認済みです。

- Windows11
- FME Desktop 2022.2
- Python: 3.8.2

## 環境構築

以下の手順で環境構築してください。
コマンドで依存ライブラリをインストールしてください。

### 仮想環境作成（必要に応じて）

以下のコマンドで仮想環境を作成してactivateします。  

```terminal
python -m venv .venv
./venv/Scripts/activate
```

### 依存ライブラリのインストール

```terminal
pip -r requirements.txt
```

## プロジェクトの実行方法

### FME Workflowの実行

FME workbenchでfme_workflow/ifc_to_gltf_annotation_json.fmwを開いて実行します。  
成功すると以下の結果が得られます：

- fme_workflow/ifc配下にAC20-FZK-Haus.ifcファイルがダウンロードされる
- fme_workflow/gltf配下にIfcAnnotationの引き出し線形状(glTF)が出力される
- fme_workflow/json配下にIfcAnnotationのテキスト情報が出力される

### Pythonスクリプトの実行

annotation_json_to_gltf.pyを実行します。  

成功すると以下の結果が得られます：

- output/annotations.glbが出力される
