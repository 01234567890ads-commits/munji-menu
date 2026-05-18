import requests
from bs4 import BeautifulSoup
import os
import datetime
import urllib3
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DISCORD_MAX_LENGTH = 2000
BASE_URL = "https://www.kaist.ac.kr/kr/html/campus/053001.html"
CAFETERIA_CODE = "icc"

WEEKDAY_KR = ["월", "화", "수", "목", "금"]


def get_kst_now() -> datetime.datetime:
    return datetime.datetime.utcnow() + datetime.timedelta(hours=9)


def date_to_str(dt: datetime.date) -> str:
    return dt.strftime("%Y-%m-%d")


def send_discord_message(content: str) -> bool:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL 환경변수가 없습니다.")
        return False

    chunks = [content[i:i+DISCORD_MAX_LENGTH] for i in range(0, len(content), DISCORD_MAX_LENGTH)]
    for chunk in chunks:
        try:
            response = requests.post(
                webhook_url,
                json={"content": chunk},
                timeout=10,
            )
            if response.status_code not in (200, 204):
                print(f"❌ Discord 전송 실패: HTTP {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ 네트워크 오류: {e}")
            return False

    print("✅ Discord 전송 성공")
    return True


def extract_cell_text(cell) -> str:
    for br in cell.find_all("br"):
        br.replace_with("\n")
    lines = [line.strip() for line in cell.get_text().splitlines() if line.strip()]
    return "\n".join(lines)


def get_menu_for_date(target_date: datetime.date) -> str:
    date_str = date_to_str(target_date)
    url = f"{BASE_URL}?dvs_cd={CAFETERIA_CODE}&stt_dt={date_str}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

    weekday_label = WEEKDAY_KR[target_date.weekday()]

    try:
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        response.raise_for_status()
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        target_table = next(
            (t for t in soup.find_all("table") if "중식" in t.get_text()),
            None,
        )
        if not target_table:
            return f"**{date_str} ({weekday_label}요일)** 식단 정보 없음\n"

        today_row = next(
            (row for row in target_table.find_all("tr") if len(row.find_all("td")) >= 3),
            None,
        )
        if not today_row:
            return f"**{date_str} ({weekday_label}요일)** 식단 데이터 없음\n"

        cells = today_row.find_all("td")
        meal_slots = [
            ("🍳", "아침"),
            ("☀️", "점심"),
            ("🌙", "저녁"),
        ]

        lines = [f"📅 **{date_str} ({weekday_label}요일)**"]
        for i, (emoji, name) in enumerate(meal_slots):
            try:
                text = extract_cell_text(cells[i])
                content = text if text else "운영 안함"
            except IndexError:
                content = "정보 없음"
            # 이모지와 식사 종류를 헤더로, 내용은 다음 줄에
            lines.append(f"{emoji} **[{name}]**")
            lines.append(content)
            lines.append("")  # 아침/점심/저녁 사이 빈 줄

        lines.append("─────────────────")  # 날짜 구분선
        lines.append("")

        return "\n".join(lines)

    except Exception as e:
        return f"**{date_str} ({weekday_label}요일)** 오류: {e}\n"


def build_message(today: datetime.date) -> str:
    weekday = today.weekday()  # 0=월, 1=화, 2=수, 3=목, 4=금

    if weekday == 0:  # 월요일: 이번주 월~금
        dates = [today + datetime.timedelta(days=i) for i in range(5)]
        header = "🗓️ **이번 주 문지캠퍼스 식단** 🗓️"
    elif weekday in (1, 2, 3):  # 화~목: 오늘 + 내일
        dates = [today, today + datetime.timedelta(days=1)]
        header = "🍚 **오늘 & 내일 문지캠퍼스 식단** 🍚"
    else:  # 금요일: 오늘만
        dates = [today]
        header = "🍚 **오늘 문지캠퍼스 식단** 🍚"

    url = f"{BASE_URL}?dvs_cd={CAFETERIA_CODE}&stt_dt={date_to_str(today)}"
    lines = [header, f"바로가기: <{url}>", ""]

    for d in dates:
        lines.append(get_menu_for_date(d))

    return "\n".join(lines).strip()


if __name__ == "__main__":
    kst_now = get_kst_now()
    today = kst_now.date()
    weekday = today.weekday()

    print(f"📅 오늘: {date_to_str(today)} ({WEEKDAY_KR[weekday]}요일)")

    if weekday > 4:
        print("주말입니다. 종료합니다.")
        sys.exit(0)

    msg = build_message(today)
    print(msg)

    success = send_discord_message(msg)
    sys.exit(0 if success else 1)
