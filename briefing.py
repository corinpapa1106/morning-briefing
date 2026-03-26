import anthropic
import requests
import os
import json
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

# 한국시간 설정
KST = timezone(timedelta(hours=9))

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
    body = urlencode({"template_object": template_str})
    response = requests.post(url, headers=headers, data=body.encode("utf-8"))
    print(f"카카오 전송 결과: {response.status_code}")
    print(f"카카오 응답: {response.text}")

def save_html(full_briefing, today_kst):
    # 마크다운 굵게(**텍스트**) 를 HTML로 변환
    import re
    content = full_briefing.replace('\n', '<br>')
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>모닝 브리핑 {today_kst}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 720px; margin: 0 auto; padding: 20px; background: #f5f5f5; color: #333; }}
  .header {{ background: #1a1a2e; color: white; border-radius: 12px; padding: 20px 24px; margin-bottom: 16px; }}
  .header h1 {{ margin: 0; font-size: 20px; }}
  .header .date {{ margin: 4px 0 0; font-size: 13px; color: #aaa; }}
  .card {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); line-height: 1.8; font-size: 15px; }}
  strong {{ color: #1a1a2e; }}
</style>
</head>
<body>
<div class="header">
  <h1>📊 모닝 브리핑</h1>
  <p class="date">{today_kst} (한국시간 기준)</p>
</div>
<div class="card">
  {content}
</div>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html 저장 완료")

def get_briefing(today_kst, yesterday_us):
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = f"""오늘 한국시간은 {today_kst}입니다. 미국 주식시장 기준 어제는 {yesterday_us}입니다.

아래 내용을 검색해서 한국어로 브리핑해주세요.

1. 📈 미국 주식시장 {yesterday_us} 마감 시황
   - S&P500, 나스닥, 다우존스 수치와 등락률
   - 주요 뉴스 3가지

2. 🔵 Canton Network (CC코인) 최신 동향
   - 현재 가격과 24시간 변동
   - 주요 이슈 (새로운 소식 위주)

3. 🟡 LayerZero (ZRO코인) 최신 동향
   - 현재 가격과 24시간 변동
   - 주요 이슈 (새로운 소식 위주)

4. 🎬 오늘의 유튜브 주제 추천
   - 30~50대 남성 투자자 대상
   - 제목 + 간단한 기획 방향

---
📌 오늘의 핵심 요약 (3줄)
위 내용을 3줄로 요약해주세요."""

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

def extract_summary(full_briefing):
    lines = full_briefing.strip().split('\n')
    summary_lines = []
    in_summary = False

    for line in lines:
        if '핵심 요약' in line:
            in_summary = True
        if in_summary and line.strip():
            summary_lines.append(line)
        if len(summary_lines) >= 6:
            break

    if summary_lines:
        return '\n'.join(summary_lines)
    else:
        return full_briefing[:400] + "\n\n👉 전체 내용은 자세히 보기를 눌러주세요!"

def main():
    now_kst = datetime.now(KST)
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
