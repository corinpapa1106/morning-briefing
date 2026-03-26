import anthropic
import requests
import os
import json
from datetime import datetime
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
    body = urlencode({"template_object": template_str})
    response = requests.post(url, headers=headers, data=body.encode("utf-8"))
    print(f"카카오 전송 결과: {response.status_code}")
    print(f"카카오 응답: {response.text}")

def save_html(full_briefing, today):
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>모닝 브리핑 {today}</title>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 720px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
  .card {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
  h1 {{ color: #333; font-size: 20px; border-bottom: 2px solid #f0f0f0; padding-bottom: 12px; }}
  pre {{ white-space: pre-wrap; word-wrap: break-word; font-family: inherit; font-size: 15px; line-height: 1.8; color: #444; }}
  .date {{ color: #888; font-size: 13px; margin-bottom: 8px; }}
</style>
</head>
<body>
<div class="card">
  <div class="date">{today}</div>
  <h1>📊 모닝 브리핑</h1>
  <pre>{full_briefing}</pre>
</div>
</body>
</html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML 파일 저장 완료")

def get_briefing():
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    today = datetime.now().strftime("%Y년 %m월 %d일")
    
    prompt = f"""오늘은 {today}입니다.
아래 내용을 검색해서 한국어로 브리핑해주세요.

1. 미국 주식시장 어제 마감 시황 (S&P500, 나스닥, 다우존스 수치 및 주요 뉴스 3개)
2. Canton Network CC코인 24시간 이내 새로운 소식 (가격, 주요 이슈)
3. LayerZero ZRO코인 24시간 이내 새로운 소식 (가격, 주요 이슈)
4. 오늘의 유튜브 주제 추천 1개 (30~50대 남성 투자자 대상)

마지막에 전체 내용을 3줄로 요약한 "📌 오늘의 핵심 요약"을 추가해주세요.
각 섹션을 명확히 구분해서 작성해주세요."""

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
        if '핵심 요약' in line or '오늘의 핵심' in line:
            in_summary = True
        if in_summary and line.strip():
            summary_lines.append(line)
        if len(summary_lines) >= 6:
            break
    
    if summary_lines:
        return '\n'.join(summary_lines)
    else:
        # 요약이 없으면 앞부분 400자
        return full_briefing[:400] + "\n\n👉 자세히 보기를 눌러 전체 내용을 확인하세요!"

def main():
    today = datetime.now().strftime("%Y년 %m월 %d일")
    print("브리핑 생성 시작...")
    
    full_briefing = get_briefing()
    print("브리핑 생성 완료!")
    
    # HTML 저장
    save_html(full_briefing, today)
    
    # 카카오 요약 메시지
    summary = extract_summary(full_briefing)
    summary += f"\n\n📅 {today} 모닝브리핑\n👇 전체 내용 보기"
    
    detail_url = "https://corinpapa1106.github.io/morning-briefing/"
    send_kakao_message(summary, detail_url)
    print("카카오톡 전송 완료!")

if __name__ == "__main__":
    main()
