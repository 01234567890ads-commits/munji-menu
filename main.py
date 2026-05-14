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


def get_kst_today() -> str:
    utc_now = datetime.datetime.utcnow()
    kst_now = utc_now + datetime.timedelta(hours=9)
    return kst_now.strftime("%Y-%m-%d")


def send_discord_message(content: str) -> bool:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL 환경변수가 없습니다.")
        return False

    if len(content) > DISCORD_MAX_LENGTH:
        content = content[:DISCORD_MAX_LENGTH - 3] + "..."

    try:
        response = requests.post(
            webhook_url,
            json={"content": content},
            timeout=10,
        )
        if response.status_code in (200, 204):
            print("✅ Discord 전송 성공")
            return True
        else:
            print(f"❌ Discord 전송 실패: HTTP {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ 네트워크 오류: {e}")
        return False


def extract_cell_text(cell) -> str:
    for br in cell.find_all("br"):
        br.replace_with("\n")
    lines = [line.strip() for line in cell.get_text().splitlines() if line.strip()]
    return "\n".join(lines)


def get_menu(today: str) -> str:
    url = f"{BASE_URL}?dvs_cd={CAFETERIA_CODE}&stt_dt={today}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

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
            return (
                f"🚫 **{today} 식단표를 찾을 수 없습니다.**\n"
                f"직접 확인: <{url}>"
            )

        today_row = next(
            (row for row in target_table.find_all("tr") if len(row.find_all("td")) >= 3),
            None,
        )
        if not today_row:
            return f"🚫 **{today} 식단 데이터를 찾을 수 없습니다.**\n직접 확인: <{url}>"

        cells = today_row.find_all("td")
        meal_slots = [
            ("🍳", "아침"),
            ("☀️", "점심"),
            ("🌙", "저녁"),
        ]

        lines = [
            f"🍚 **{today} 문지캠퍼스 식단** 🍚",
            f"바로가기: <{url}>",
            "",
        ]

        for i, (emoji, name) in enumerate(meal_slots):
            try:
                text = extract_cell_text(cells[i])
                content = text if text else "운영 안함 / 정보 없음"
            except IndexError:
                content = "정보 없음"
            lines.append(f"{emoji} **[{name}]**")
            lines.append(content)
            lines.append("")

        return "\n".join(lines).strip()

    except requests.HTTPError as e:
        return f"⚠️ HTTP 오류: {e}"
    except requests.RequestException as e:
        return f"⚠️ 네트워크 오류: {e}"
    except Exception as e:
        return f"⚠️ 알 수 없는 오류: {e}"


if __name__ == "__main__":
    today = get_kst_today()
    print(f"📅 조회 날짜: {today}")
    msg = get_menu(today)
    print(msg)
    success = send_discord_message(msg)
    sys.exit(0 if success else 1)
