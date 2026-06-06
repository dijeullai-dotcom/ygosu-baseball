import os, requests, time, re
from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime

def get_cookie():
    return os.environ.get("YGOSU_COOKIE", "")

def calculate_daily_score(stats):
    return (min(stats['post'], 5) * 20) + (min(stats['comment'], 20) * 10) + (min(stats['like'], 10) * 0.1)

def main():
    board_id = "pan_prison" # 타겟 게시판
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0', 'Cookie': get_cookie()})
    
    stats = defaultdict(lambda: {'post': 0, 'comment': 0, 'like': 0})
    
    # 게시물 분석 로직 (간략화)
    res = session.get(f"https://ygosu.com/board/{board_id}/")
    soup = BeautifulSoup(res.text, 'html.parser')
    for a in soup.select('td.tit a'):
        post_id = re.search(r'/(\d+)', a['href']).group(1)
        # 데이터 수집 (게시글/댓글/추천) 생략... (기존 로직 사용)

    # HTML 표 생성
    sorted_stats = sorted(stats.items(), key=lambda x: calculate_daily_score(x[1]), reverse=True)
    rows = "".join([f"<tr><td class='nick'>{n}</td><td>{s['post']}</td><td>{s['comment']}</td><td>{s['like']}</td><td>{calculate_daily_score(s):.1f}</td><td>{'O' if calculate_daily_score(s)>=300 else 'X'}</td></tr>" for n, s in sorted_stats])
    
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <style>
        body{{background:#121212; color:#fff; font-family:monospace; margin:0; padding:10px;}}
        table{{width:100%; border-collapse:collapse;}} th{{color:#c084fc; border-bottom:2px solid #555; padding:5px;}} td{{text-align:center; padding:5px; border-bottom:1px solid #333;}}
    </style></head><body>
    <table><tr><th>닉네임</th><th>작성글</th><th>댓글</th><th>추천</th><th>점수</th><th>완료</th></tr>{rows}</table>
    </body></html>"""
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__": main()
