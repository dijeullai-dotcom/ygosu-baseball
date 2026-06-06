import os
import sys
import time
import re
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime

def get_cookie():
    """깃허브의 비밀 메모장(Secrets) 또는 로컬 환경변수에서 쿠키를 읽어옵니다."""
    cookie_val = os.environ.get("YGOSU_COOKIE")
    if not cookie_val:
        # 로컬 테스트용(혹시 컴퓨터에서 테스트할 때를 대비)
        try:
            with open('cookie.txt', 'r', encoding='utf-8') as f:
                cookie_val = f.read().strip()
        except FileNotFoundError:
            print("오류: 환경변수 또는 cookie.txt가 없습니다.")
            sys.exit()
            
    if "YGOSU_SESSION_ID=" not in cookie_val:
        return f"YGOSU_SESSION_ID={cookie_val}"
    return cookie_val

my_cookies = get_cookie()
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 
    'Cookie': my_cookies
})

def calculate_daily_score(count_dict):
    capped_posts = min(count_dict['post'], 5)
    capped_comments = min(count_dict['comment'], 20)
    capped_likes = min(count_dict['like'], 10)
    return (capped_posts * 20) + (capped_comments * 10) + (capped_likes * 0.1)

def get_todays_post_ids(board_id):
    todays_ids = []
    page = 1
    print("🔍 오늘 작성된 게시물 목록 스캔 중...")
    
    while True:
        try:
            res = session.get(f"https://ygosu.com/board/{board_id}/?page={page}", timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            trs = soup.select('tbody tr')
            
            if not trs: break
            
            found_past_post = False
            for tr in trs:
                if tr.select_one('td.num span.notice_icon') or tr.select_one('td.num b'):
                    continue
                
                date_td = tr.select_one('td.date')
                if not date_td: continue
                date_text = date_td.get_text(strip=True)
                
                if ':' in date_text:
                    tit_a = tr.select_one('td.tit a')
                    if tit_a and 'href' in tit_a.attrs:
                        href = tit_a['href']
                        match = re.search(rf'/board/{board_id}/(\d+)', href)
                        if match:
                            todays_ids.append(int(match.group(1)))
                else:
                    found_past_post = True
            
            if found_past_post: break
            page += 1
            time.sleep(0.3)
        except Exception:
            break
            
    return sorted(list(set(todays_ids)))

def generate_baseball_dashboard(stats, update_time):
    top_posts = sorted(stats.items(), key=lambda x: x[1]['post'], reverse=True)[:5]
    top_comments = sorted(stats.items(), key=lambda x: x[1]['comment'], reverse=True)[:5]
    top_likes = sorted(stats.items(), key=lambda x: x[1]['like'], reverse=True)[:5]
    top_scores = sorted(stats.items(), key=lambda x: calculate_daily_score(x[1]), reverse=True)[:5]

    def make_list_html(data_list, key_type, color_class):
        html = ""
        for i, (nick, count) in enumerate(data_list):
            if key_type == 'score':
                val = f"{calculate_daily_score(count):.1f}"
            else:
                val = f"{count[key_type]:,}"
            if float(val.replace(',','')) == 0: continue
            html += f"""
            <div class="list-item">
                <div class="rank-badge">{i+1}</div>
                <div class="nick">{nick}</div>
                <div class="score">
                    {val}
                    <div class="progress-bar {color_class}"></div>
                </div>
            </div>
            """
        return html or "<div class='nick' style='margin-top:10px; color:#64748b;'>기록 없음</div>"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>아리송(야구) 실시간 MVP 랭킹</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
            body {{ background-color: #0b1320; background-image: radial-gradient(circle at 50% 0%, #162a45 0%, #0b1320 70%); color: #f8fafc; font-family: 'Noto Sans KR', sans-serif; margin: 0; padding: 40px; min-height: 100vh; }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px dashed #334155; padding-bottom: 20px; position: relative; }}
            .header h1 {{ margin: 0; font-size: 36px; color: #ffffff; font-weight: 900; letter-spacing: 2px; text-shadow: 0 4px 6px rgba(0,0,0,0.5); }}
            .header p {{ color: #94a3b8; font-size: 16px; margin-top: 10px; }}
            .update-time {{ position: absolute; right: 0; bottom: 20px; font-size: 14px; color: #10b981; font-weight: bold; background: rgba(16,185,129,0.1); padding: 5px 10px; border-radius: 20px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
            .card {{ background-color: rgba(30, 41, 59, 0.8); backdrop-filter: blur(10px); border-radius: 12px; padding: 24px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5); }}
            .card-green {{ border-top: 5px solid #10b981; }}
            .card-blue {{ border-top: 5px solid #3b82f6; }}
            .card-orange {{ border-top: 5px solid #f59e0b; }}
            .card-red {{ border-top: 5px solid #ef4444; }}
            .card-title {{ font-size: 20px; font-weight: 900; margin-bottom: 20px; color: #fff; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #334155; padding-bottom: 12px; }}
            .list-item {{ display: flex; align-items: center; margin-bottom: 16px; }}
            .rank-badge {{ background-color: #0f172a; border: 1px solid #334155; color: #fbbf24; font-weight: 900; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 50%; margin-right: 15px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.5); }}
            .nick {{ flex: 1; font-size: 17px; font-weight: 700; color: #e2e8f0; }}
            .score {{ text-align: right; font-size: 20px; font-weight: 900; color: #fff; }}
            .progress-bar {{ height: 5px; border-radius: 3px; margin-top: 6px; width: 100%; }}
            .bg-green {{ background-color: #10b981; box-shadow: 0 0 8px #10b981; }}
            .bg-blue {{ background-color: #3b82f6; box-shadow: 0 0 8px #3b82f6; }}
            .bg-orange {{ background-color: #f59e0b; box-shadow: 0 0 8px #f59e0b; }}
            .bg-red {{ background-color: #ef4444; box-shadow: 0 0 8px #ef4444; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏟️ 아리송(야구) 실시간 MVP 랭킹</h1>
                <p>오늘 하루 페넌트레이스 현황입니다. (24시간 자동 업데이트)</p>
                <div class="update-time">⏳ 마지막 업데이트: {update_time} KST</div>
            </div>
            <div class="grid">
                <div class="card card-green">
                    <div class="card-title">⚾ 홈런 타자 (게시글 작성)</div>
                    {make_list_html(top_posts, 'post', 'bg-green')}
                </div>
                <div class="card card-blue">
                    <div class="card-title">📣 응원 단장 (댓글 작성)</div>
                    {make_list_html(top_comments, 'comment', 'bg-blue')}
                </div>
                <div class="card card-orange">
                    <div class="card-title">🧤 골든 글러브 (추천 활동)</div>
                    {make_list_html(top_likes, 'like', 'bg-orange')}
                </div>
                <div class="card card-red">
                    <div class="card-title">🏆 시즌 MVP (종합 활동 점수)</div>
                    {make_list_html(top_scores, 'score', 'bg-red')}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 깃허브 블로그(Pages)로 서비스하기 위해 파일 이름을 무조건 'index.html'로 고정합니다.
    with open("index.html", 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    board_id = "pan_ahrisong"
    post_ids = get_todays_post_ids(board_id)
    
    if not post_ids:
        print("오늘 작성된 게시물이 없습니다.")
        return

    print(f"✔️ 오늘 작성된 게시물 {len(post_ids)}개 분석 시작...")
    stats = defaultdict(lambda: {'post': 0, 'comment': 0, 'like': 0})
    
    for i, post_id in enumerate(post_ids):
        try:
            res = session.get(f"https://ygosu.com/board/{board_id}/{post_id}", timeout=5)
            if res.status_code != 200: continue
            soup = BeautifulSoup(res.text, 'html.parser')
            
            board_top = soup.select_one('div.board_top')
            if board_top:
                writer_tag = board_top.select_one('div.nickname a')
                if writer_tag: stats[writer_tag.get_text(strip=True)]['post'] += 1
            
            reply_layer = soup.find('ul', id='reply_list_layer')
            if reply_layer:
                for nick_a in reply_layer.select('div.nick > a'): stats[nick_a.get_text(strip=True)]['comment'] += 1
            
            payload = {'path': 'board/get_vote_list', 'bid': board_id, 'idx': post_id}
            headers = {'Referer': f"https://ygosu.com/board/{board_id}/{post_id}"}
            res_like = session.post("https://ygosu.com/action.yg", data=payload, headers=headers, timeout=5)
            if res_like.status_code == 200 and 'html' in res_like.json():
                for nick_a in BeautifulSoup(res_like.json()['html'], 'html.parser').select('td.nick > a'):
                    stats[nick_a.get_text(strip=True)]['like'] += 1
            
            print(f"[{i+1}/{len(post_ids)}] 완료")
            time.sleep(0.2) 
        except Exception:
            pass

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    generate_baseball_dashboard(stats, current_time)
    print(f"✔️ 대시보드 업데이트 완료! ({current_time})")

if __name__ == "__main__":
    main()