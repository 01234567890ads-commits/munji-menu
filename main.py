import requests
from bs4 import BeautifulSoup
import os
import datetime

# 1. 한국 시간(KST) 설정 (중요! 서버는 외국에 있어서 시간 보정이 필요함)
# UTC 시간에 9시간을 더해줍니다.
utc_now = datetime.datetime.utcnow()
kst_now = utc_now + datetime.timedelta(hours=9)
today = kst_now.strftime("%Y-%m-%d")
weekday = kst_now.weekday() # 0:월 ~ 6:일

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
    # 3. 헤더 추가 (나는 로봇이 아니라 사람입니다~ 라고 속이는 부분)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8' # 한글 깨짐 방지
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 테이블 찾기
        table = soup.find('table', {'class': 'table_t1'})
        
        if not table:
            # 테이블이 없으면 페이지 전체 텍스트에서 힌트 찾기 (디버깅용)
            return f"🚫 **{today} 식단표를 가져오지 못했습니다.**\n혹시 주말이거나 휴일인가요? 직접 확인해 보세요: <{url}>"

        menu_text = f"🍚 **{today} 문지캠퍼스 식단** 🍚\n"
        menu_text += f"바로가기: <{url}>\n\n"
        
        rows = table.find_all('tr')
        
        # 점심 (Lunch)
        try:
            # 줄바꿈 태그(<br>)를 실제 줄바꿈으로 변경
            lunch_td = rows[1].find_all('td')[1]
            for br in lunch_td.find_all("br"):
                br.replace_with("\n")
            lunch = lunch_td.get_text().strip()
            menu_text += f"☀️ **[점심]**\n{lunch}\n\n"
        except:
            menu_text += "☀️ **[점심]** 정보 없음\n\n"

        # 저녁 (Dinner)
        try:
            dinner_td = rows[1].find_all('td')[2]
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
