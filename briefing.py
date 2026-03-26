import anthropic
import requests
import os
from datetime import datetime

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

def send_kakao_message(message):
    access_token = get_new_kakao_token()
    print(f"사용할 토큰: {access_token[:20]}...")
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
    }
    import json
    template = {
        "object_type": "text",
        "text": message[:400],
        "link": {
            "web_url": "https://www.google.com",
            "mobile_web_url": "https://www.google.com"
        }
    }
    template_str = json.dumps(template, ensure_ascii=False)
    from urllib.parse import urlencode
    body = urlencode({"template_object": template_str})
    response = requests.post(url, headers=headers, data=body.encode("utf-8"))
    print(f"카카오 전송 결과: {response.status_code}")
    print(f"카카오 응답 상세: {response.text}")

def get_briefing():
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    today = datetime.now().strftime("%Y년 %m월 %d일")
    
    prompt = f"""오늘은 {today}입니다. 
아래 내용을 검색해서 한국어로 간결하게 브리핑해주세요.

1. 미국 주식시장 어제 마감 시황 (S&P500, 나스닥, 다우존스 수치 및 주요 뉴스 3개)
2. Canton Network CC코인 24시간 이내 새로운 소식 (가격, 주요 이슈)
3. LayerZero ZRO코인 24시간 이내 새로운 소식 (가격, 주요 이슈)
4. 오늘의 유튜브 주제 추천 1개 (30~50대 남성 투자자 대상)

각 섹션을 명확히 구분해서 작성해주세요.
전체 길이는 카카오톡 메시지로 읽기 좋게 1500자 이내로 작성해주세요."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )
    
    result_text = ""
    for block in message.content:
        if hasattr(block, "text"):
            result_text += block.text
    
    return result_text

def main():
    print("브리핑 생성 시작...")
    briefing = get_briefing()
    print("브리핑 생성 완료!")
    print(briefing)
    send_kakao_message(briefing)
    print("카카오톡 전송 완료!")

if __name__ == "__main__":
    main()
