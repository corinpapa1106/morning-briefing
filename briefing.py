import anthropic
import requests
import os
import re
import json
import subprocess
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

def get_new_kakao_token():
    refresh_token = os.environ.get("KAKAO_REFRESH_TOKEN")
    rest_api_key = os.environ.get("KAKAO_REST_API_KEY")
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": rest_api_key,
        "refresh_token": refresh_token
    }
    response = requests.post(url, data=data)
    result = response.json()
    return result.get("access_token")

def send_kakao_message(summary, detail_url):
    access_token = get_new_kakao_token()
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
    }
    template = {
        "object_type": "text",
        "text": summary,
        "link": {
            "web_url": detail_url,
            "mobile_web_url": detail_url
        }
    }
    template_str = json.dumps(template, ensure_ascii=False)
    print(f"전송할 URL: {detail_url}")
    print(f"템플릿: {template_str}")
    body = urlencode({"template_object": template_str})
    response = requests.post(url, headers=headers, data=body.encode("utf-8"))
    print(f"카카오 전송 결과: {response.status_code}")
    print(f"카카오 응답: {response.text}")

def save_html(full_briefing, today_kst):
    content = full_briefing.replace('\n', '<br>')
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)

    html = "<!DOCTYPE html>\n"
    html += "<html lang='ko'>\n"
    html += "<head>\n"
    html += "<meta charset='UTF-8'>\n"
    html += "<meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
    html += "<title>모닝 브리핑 " + today_kst + "</title>\n"
    html += "<style>\n"
    html += "body { font-family: -apple-system, sans-serif; max-width: 720px; margin: 0 auto; padding: 20px; background: #f5f5f5; color: #333; }\n"
    html += ".header { background: #1a1a2e; color: white; border-radius: 12px; padding: 20px 24px; margin-bottom: 16px; }\n"
    html += ".header h1 { margin: 0; font-size: 20px; }\n"
    html += ".date { margin: 4px 0 0; font-size: 13px; color: #aaa; }\n"
    html += ".card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); line-height: 1.8; font-size: 15px; }\n"
    html += "strong { color: #1a1a2e; }\n"
    html += "</style>\n"
    html += "</head>\n"
    html += "<body>\n"
    html += "<div class='header'>\n"
    html += "<h1>📊 모닝 브리핑</h1>\n"
    html += "<p class='date'>" + today_kst + " (한국시간 기준)</p>\n"
    html += "</div>\n"
    html += "<div class='card'>\n"
    html += content + "\n"
    html += "</div>\n"
    html += "</body>\n"
    html += "</html>"

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html 저장 완료")

    # git push
    try:
        subprocess.run(["git", "config", "--global", "user.email", "action@github.com"], check=True)
        subprocess.run(["git", "config", "--global", "user.name", "GitHub Action"], check=True)
        subprocess.run(["git", "add", "index.html"], check=True)
        result = subprocess.run(["git", "diff", "--staged", "--quiet"])
        if result.returncode != 0:
            subprocess.run(["git", "commit", "-m", "브리핑 업데이트 " + today_kst], check=True)
            subprocess.run(["git", "push"], check=True)
            print("GitHub 페이지 업데이트 완료")
        else:
            print("변경사항 없음")
    except Exception as e:
        print(f"git push 오류: {e}")

def get_briefing(today_kst, yesterday_us):
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = f"""오늘 한국시간은 {today_kst}입니다. 미국 주식시장 기준 어제는 {yesterday_us}입니다.

아래 내용을 검색해서 한국어로 브리핑해주세요.

1. 미국 주식시장 {yesterday_us} 마감 시황
   - S&P500, 나스닥, 다우존스 수치와 등락률
   - 주요 뉴스 3가지

2. Canton Network CC코인 최신 동향
   - 현재 가격과 24시간 변동
   - 주요 이슈

3. LayerZero ZRO코인 최신 동향
   - 현재 가격과 24시간 변동
   - 주요 이슈

4. 오늘의 유튜브 주제 추천
   - 30~50대 남성 투자자 대상
   - 제목과 간단한 기획 방향

---
📌 오늘의 핵심 요약 (3줄로 작성)

---
[카카오톡 요약 시작]
아래 형식을 정확히 지켜서 카카오톡 요약 메시지를 작성해주세요.
반드시 **[카카오톡 요약 시작]** 과 **[카카오톡 요약 끝]** 사이에 작성하세요.

📊 {today_kst} 모닝브리핑

📈 미국장 ({yesterday_us} 마감)
S&P500 (수치) (등락률) | 나스닥 (수치) (등락률) | 다우 (수치) (등락률)
▶ (주요 뉴스 1줄 요약)

🔵 Canton CC코인
(가격) | (24시간 등락률) | (주요 이슈 1줄)

🟡 LayerZero ZRO
(가격) | (24시간 등락률) | (주요 이슈 1줄)

📌 핵심 요약
① (첫번째 핵심)
② (두번째 핵심)
③ (세번째 핵심)
[카카오톡 요약 끝]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )

    full_text = ""
    for block in message.content:
        if hasattr(block, "text"):
            full_text += block.text

    return full_text

def main():
    now_kst = datetime.now(timezone.utc) + timedelta(hours=9)
    today_kst = now_kst.strftime("%Y년 %m월 %d일")
    yesterday_us = (now_kst - timedelta(days=1)).strftime("%Y년 %m월 %d일")

    print(f"한국시간: {today_kst}")
    print(f"미국장 기준일: {yesterday_us}")
    print("브리핑 생성 시작...")

    full_briefing = get_briefing(today_kst, yesterday_us)
    print("브리핑 생성 완료!")

    save_html(full_briefing, today_kst)

    summary = extract_summary(full_briefing)
    summary += f"\n\n📅 {today_kst} 모닝브리핑\n👇 전체 내용 보기"

    detail_url = "https://corinpapa1106.github.io/morning-briefing/"
    send_kakao_message(summary, detail_url)
    print("카카오톡 전송 완료!")

if __name__ == "__main__":
    main()
