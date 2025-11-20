import requests
from bs4 import BeautifulSoup
import os
import datetime
import urllib3

# 보안 경고 무시 설정 (학교 사이트 접속 시 인증서 문제 해결)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. 한국 시간(KST) 설정
utc_now = datetime.datetime.utcnow()
kst_now = utc_now + datetime.timedelta(hours=9)
today = kst_now.strftime("%Y-%m-%d")

# 2. 문지캠퍼스 식단 주소
url = f"https://www.kaist.ac.kr/kr/html/campus/053001.html?dvs_cd=icc&stt_dt={today}"

def send_discord_message(content):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("디스코드 주소가 없습니다.")
        return
    
    data = {"content": content}
    requests.post(webhook_url, json=data)

def get_menu():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # verify=False 옵션 추가 (SSL 인증서 오류 무시)
        response = requests.get(url, headers=headers, verify=False)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # [수정된 부분] 특정 이름(class)이 아니라, '중식'이라는 단어가 있는 표를 찾습니다.
        target_table = None
        tables = soup.find_all('table')
        
        for table in tables:
            if "중식" in table.get_text():
                target_table = table
                break
        
        if not target_table:
            # 디버깅용: 페이지 제목이라도 가져와 봅니다.
            page_title = soup.title.get_text().strip() if soup.title else "제목 없음"
            return f"🚫 **{today} 식단표를 못 찾았습니다.**\n접속한 페이지 제목: {page_title}\n직접 링크 확인: <{url}>"

        menu_text = f"🍚 **{today} 문지캠퍼스 식단** 🍚\n"
        menu_text += f"바로가기: <{url}>\n\n"
        
        rows = target_table.find_all('tr')
        
        # 보통 첫 번째 줄(인덱스 0)은 헤더, 두 번째 줄(인덱스 1)이 오늘의 메뉴입니다.
        # 하지만 문지캠퍼스 테이블 구조가 날짜별로 다를 수 있어 '오늘 날짜'가 있는 행을 찾거나
        # 단순히 가장 첫 번째 데이터 행을 가져옵니다.
        
        today_row = None
        for row in rows:
            # 만약 행 안에 오늘 날짜(MM/DD)가 있거나, 그냥 데이터가 있는 첫 행을 씁니다.
            cells = row.find_all('td')
            if len(cells) >= 3: # 조식/중식/석식 칸이 다 있는 경우
                today_row = row
                break
        
        if not today_row:
             # 날짜 행을 못 찾으면 그냥 두 번째 행(rows[1])을 시도
             today_row = rows[1]

        cells = today_row.find_all('td')

        # 점심 (Lunch) - 보통 두 번째 칸 (인덱스 1)
        try:
            lunch_td = cells[1]
            for br in lunch_td.find_all("br"):
                br.replace_with("\n")
            lunch = lunch_td.get_text().strip()
            menu_text += f"☀️ **[점심]**\n{lunch}\n\n"
        except:
            menu_text += "☀️ **[점심]** 정보 없음\n\n"

        # 저녁 (Dinner) - 보통 세 번째 칸 (인덱스 2)
        try:
            dinner_td = cells[2]
            for br in dinner_td.find_all("br"):
                br.replace_with("\n")
            dinner = dinner_td.get_text().strip()
            menu_text += f"🌙 **[저녁]**\n{dinner}\n"
        except:
            menu_text += "🌙 **[저녁]** 정보 없음\n"
            
        return menu_text

    except Exception as e:
        return f"⚠️ 에러 발생: {str(e)}"

if __name__ == "__main__":
    msg = get_menu()
    send_discord_message(msg)
