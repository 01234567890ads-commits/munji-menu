import requests
from bs4 import BeautifulSoup
import os
import datetime
import urllib3

# 보안 경고 무시 설정
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
        response = requests.get(url, headers=headers, verify=False)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # '중식'이라는 단어가 있는 표 찾기
        target_table = None
        tables = soup.find_all('table')
        for table in tables:
            if "중식" in table.get_text():
                target_table = table
                break
        
        if not target_table:
            return f"🚫 **{today} 식단표를 못 찾았습니다.**\n링크 확인: <{url}>"

        menu_text = f"🍚 **{today} 문지캠퍼스 식단** 🍚\n"
        menu_text += f"바로가기: <{url}>\n\n"
        
        rows = target_table.find_all('tr')
        
        # 오늘 날짜 행 찾기
        today_row = None
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                today_row = row
                break
        
        if not today_row:
             today_row = rows[1]

        cells = today_row.find_all('td')

        # --- 여기부터 아침/점심/저녁 추출 ---
        
        # 1. 아침 (Breakfast) - 첫 번째 칸 (인덱스 0)
        try:
            breakfast_td = cells[0]
            for br in breakfast_td.find_all("br"):
                br.replace_with("\n")
            breakfast = breakfast_td.get_text().strip()
            # 내용이 없으면 빈칸 처리
            if breakfast:
                menu_text += f"🍳 **[아침]**\n{breakfast}\n\n"
            else:
                menu_text += f"🍳 **[아침]** 운영 안함/정보 없음\n\n"
        except:
            menu_text += "🍳 **[아침]** 정보 없음\n\n"

        # 2. 점심 (Lunch) - 두 번째 칸 (인덱스 1)
        try:
            lunch_td = cells[1]
            for br in lunch_td.find_all("br"):
                br.replace_with("\n")
            lunch = lunch_td.get_text().strip()
            menu_text += f"☀️ **[점심]**\n{lunch}\n\n"
        except:
            menu_text += "☀️ **[점심]** 정보 없음\n\n"

        # 3. 저녁 (Dinner) - 세 번째 칸 (인덱스 2)
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
