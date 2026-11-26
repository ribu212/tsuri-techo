"""気象庁の潮位表を取ってきて tide/ フォルダを最新にするスクリプト。

やること
  1. 気象庁の「潮位表地点一覧」ページから、全国の地点名と緯度経度を読み取り tide/stations.json に保存
  2. 今年と来年の潮位表（地点ごとのテキストファイル）をダウンロードして tide/<年>/<地点記号>.txt に保存
     - 来年分がまだ公開されていなければ（ファイルが無ければ）そのまま飛ばす
     - 中身が変わっていないファイルは書き換えない
  3. tide/last_checked.txt に確認した日時を書く

使い方
  python scripts/update_tide.py            # 全地点を更新
  python scripts/update_tide.py --limit 3  # 試しに3地点だけ
GitHub Actions（.github/workflows/update-tide.yml）から毎月自動で実行されます。
"""
import argparse
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

TIDE_DIR = Path(__file__).resolve().parent.parent / "tide"
STATION_PAGE = "https://www.data.jma.go.jp/kaiyou/db/tide/suisan/station.php"
TXT_URL = "https://www.data.jma.go.jp/kaiyou/data/db/tide/suisan/txt/{year}/{code}.txt"
UA = {"User-Agent": "tsuri-techo-tide-updater"}
JST = dt.timezone(dt.timedelta(hours=9))


def get(url):
    """URL の中身を取ってくる。ファイルが無い（404）なら None を返す。"""
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(3):  # 通信エラーは3回まで再挑戦
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            err = e
        except Exception as e:  # noqa: BLE001
            err = e
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"取得に失敗しました: {url} ({err})")


def update_stations():
    """地点一覧ページを読み取り、[{code, name, lat, lng}, ...] を作る。"""
    html = get(STATION_PAGE).decode("utf-8")
    rows = re.findall(
        r"<td>([A-Z0-9]{2})</td><td><a [^>]*>([^<]+)</a></td>\s*"
        r"<td>(\d+)゜(\d+)'</td>\s*<td>(\d+)゜(\d+)'</td>",
        html,
    )
    stations, seen = [], set()
    for code, name, la, lm, lo, om in rows:
        if code in seen:
            continue
        seen.add(code)
        stations.append({"code": code, "name": name,
                         "lat": round(int(la) + int(lm) / 60, 4),
                         "lng": round(int(lo) + int(om) / 60, 4)})
    # ページの作りが変わって読み取れなかった時に、空の一覧で上書きしないための安全装置
    if len(stations) < 100:
        sys.exit(f"地点一覧の読み取りに失敗しました（{len(stations)}地点しか見つからない）。ページの形式が変わった可能性があります。")
    path = TIDE_DIR / "stations.json"
    path.write_text(json.dumps(stations, ensure_ascii=False), encoding="utf-8")
    return stations


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="試し用：先頭から何地点だけ処理するか")
    args = ap.parse_args()

    TIDE_DIR.mkdir(exist_ok=True)
    stations = update_stations()
    if args.limit:
        stations = stations[: args.limit]

    this_year = dt.datetime.now(JST).year
    summary = {}
    for year in (this_year, this_year + 1):
        ydir = TIDE_DIR / str(year)
        new = changed = same = missing = 0
        for s in stations:
            body = get(TXT_URL.format(year=year, code=s["code"]))
            time.sleep(0.15)  # 気象庁のサーバーに負担をかけないよう少し待つ
            if body is None:
                missing += 1
                continue
            ydir.mkdir(exist_ok=True)
            f = ydir / f"{s['code']}.txt"
            if f.exists() and f.read_bytes() == body:
                same += 1
                continue
            if f.exists():
                changed += 1
            else:
                new += 1
            f.write_bytes(body)
        summary[year] = dict(new=new, changed=changed, same=same, missing=missing)
        print(f"{year}年: 新規 {new} / 更新 {changed} / 変化なし {same} / 未公開 {missing}")

    # 確認した日時を記録（GitHub は長く動きのないリポジトリの自動実行を止めるため、毎回ここを書き換える）
    (TIDE_DIR / "last_checked.txt").write_text(
        dt.datetime.now(JST).strftime("%Y-%m-%d %H:%M JST") + "\n" + json.dumps(summary) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
