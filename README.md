# SOLVIA CAE Visualization

FEA/CFD resultファイルを読み込み、形状、単位付き数値、グラフ、所見、判定を、受領者が追加環境なしで開ける成果物にまとめるデスクトップ優先・オフライン既定の製品です。

製品仕様の正本は [`specs/`](specs/README.md) です。日本語の全体像は [`README.ja.md`](README.ja.md)、根拠と出典は [`evidence/`](evidence/sources.md) を参照してください。

## 構成

- `specs/`: 要求、契約、不変条件、機能仕様、検証計画
- `evidence/`: Fixed値の出典と調査記録
- `src/`: 現在のwalking-skeleton実装
- `tests/`: 実装と開発環境ゲートのテスト
- `mockups/ui/`: 新仕様の全画面状態を切り替えて確認するNext.js UIモックアップ
- `validate/`: 仕様、境界、重複、依存バージョン、コンテキスト予算、ゲート配線の検査
- `spike/`: 技術判断のための測定コードと記録
- `archive/`: 旧ルート実装と非公開ローカル資料（Git対象外）

## セットアップ

Python 3.12環境を新規作成し、依存関係をインストールします。持ち運んだ仮想環境は使いません。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## 検証

```powershell
.\.venv\Scripts\python.exe validate\check_specs.py --report
.\.venv\Scripts\python.exe validate\check_boundaries.py
.\.venv\Scripts\python.exe validate\check_commands.py
.\.venv\Scripts\python.exe validate\check_constant_duplication.py
.\.venv\Scripts\python.exe validate\check_context_budget.py
.\.venv\Scripts\python.exe validate\check_dependency_pins.py
.\.venv\Scripts\python.exe validate\check_gates_wired.py
.\.venv\Scripts\python.exe -m pytest tests
```

同じ7つのゲートとテストが `.github/workflows/ci.yml` で走ります。VTKが入っていない環境では
readerテストはスキップされ、その理由を表示します。CIは `SIM_VIEWER_REQUIRE_VTK=1` を設定するため、
そこではスキップが失敗になります — 走らなかったテストを成功として数えないためです。

UIモックアップは次のコマンドで起動します。

```powershell
cd mockups\ui
npm.cmd ci --offline
npm.cmd run dev
```
