import requests
from bs4 import BeautifulSoup
import os
import datetime

# 1. 오늘 날짜 확인
today = datetime.datetime.now().strftime("%Y-%m-%d")
weekday = datetime.datetime.now().weekday() # 0:월 ~ 6:일

# 2. 문지캠퍼스 식단 주소 (오늘 날짜 기준)
url = f"https://www.kaist.ac.kr/kr/html/campus/053001.html?dvs_cd=icc&stt_dt={today}"

def send_discord_message(content):
    # 깃허브에 저장된 비밀 주소를 가져옵니다
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("디스코드 주소(Secret)가 설정되지 않았습니다.")
        return
    
    data = {"content": content}
    requests.post(webhook_url, json=data)

def get_menu():
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 식단표 테이블 찾기
        table = soup.find('table', {'class': 'table_t1'})
        
        if not table:
            return f"🚫 {today} 식단표를 찾을 수 없습니다."

        menu_text = f"🍚 **{today} 문지캠퍼스 식단** 🍚\n"
        menu_text += f"바로가기: <{url}>\n\n"
        
        rows = table.find_all('tr')
        
        # 점심 (보통 두 번째 줄에 위치)
        try:
            lunch = rows[1].find_all('td')[1].get_text(separator="\n").strip()
            menu_text += f"☀️ **[점심]**\n{lunch}\n\n"
        except:
            menu_text += "☀️ **[점심]** 정보 없음\n\n"

        # 저녁 (보통 세 번째 칸)
        try:
            dinner = rows[1].find_all('td')[2].get_text(separator="\n").strip()
            menu_text += f"🌙 **[저녁]**\n{dinner}\n"
        except:
            menu_text += "🌙 **[저녁]** 정보 없음\n"
            
        return menu_text

    except Exception as e:
        return f"⚠️ 에러 발생: {str(e)}"

# 실행
if __name__ == "__main__":
    msg = get_menu()
    send_discord_message(msg)
