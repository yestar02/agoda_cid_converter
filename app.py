from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = 'aktmsxmfkrk_aksemsms_wnddlek'
excel_path = '아고다 잡스킬.xlsx'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    url = request.form.get('url')

    # URL 유효성 검사
    if not url or url.strip() == "":
        flash("주소를 입력해주세요.")
        return redirect(url_for('index'))
    elif "agoda.com" not in url:
        flash("아고다 주소가 아닌 것 같아요.")
        return redirect(url_for('index'))
    elif "agoda.com/ko-kr/search" in url:
        flash("검색 페이지 URL은 사용할 수 없어요.")
        return redirect(url_for('index'))
    elif "cid=" not in url:
        flash("주소에서 cid 값을 찾을 수 없어요. \n올바른 주소인지 확인해주세요.")
        return redirect(url_for('index'))

    try:
        # 원래 HTML 페이지 요청 (헤더 설정 추가)
        headers = {
            "Accept-Language": "ko,ko-KR;q=0.9,en-US;q=0.8,en;q=0.7",
            "ag-language-locale": "ko-kr"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # API URL 추출
        script_tag = soup.find("script", {"data-selenium": "script-initparam"})
        api_url_match = re.search(r'apiUrl\s*=\s*"(.+?)"', script_tag.string)

        if api_url_match:
            api_url = "https://www.agoda.com" + api_url_match.group(1).replace("&amp;", "&")

            # API 요청을 보내 JSON 응답 받기 (헤더 설정 포함)
            api_response = requests.get(api_url, headers=headers)
            api_data = api_response.json()

            # hotelInfo.name 값 추출
            hotel_name = api_data.get("hotelInfo", {}).get("name", "호텔 이름을 찾을 수 없습니다.")
        else:
            hotel_name = "호텔 정보를 찾을 수 없습니다."

    except Exception as e:
        hotel_name = f"호텔 이름을 찾는 중 오류 발생: {e}"

    # '처리용' 시트 데이터 불러오기 및 나머지 코드 유지
    process_data = pd.read_excel(excel_path, sheet_name='처리용', header=None)
    replacements = process_data.iloc[4:24, 1].tolist()
    table_headers = process_data.iloc[3, 0:2].tolist()
    table_rows_left = process_data.iloc[4:24, 0].tolist()

    # URL 수정하여 새 URL 목록 생성
    modified_urls = []
    for replacement in replacements:
        modified_url = re.sub(r'(?<=cid=)\d{7}', str(replacement), url)
        modified_urls.append(modified_url)

    table_rows = list(zip(table_rows_left, modified_urls))
    sheet1_data = pd.read_excel(excel_path, sheet_name='Sheet1', header=None)
    sheet1_rows = sheet1_data.values.tolist()

    session['search_data'] = {
        'original_url': url,
        'hotel_name': hotel_name,
        'table_headers': table_headers,
        'table_rows': table_rows,
        'sheet1_rows': sheet1_rows
    }

    return redirect(url_for('result'))

@app.route('/result')
def result():
    search_data = session.get('search_data')
    if search_data is None:
        flash("검색 결과가 없습니다. 다시 검색해주세요.")
        return redirect(url_for('index'))

    return render_template('result.html',
                           original_url=search_data['original_url'],
                           hotel_name=search_data['hotel_name'],
                           table_headers=search_data['table_headers'],
                           table_rows=search_data['table_rows'],
                           sheet1_rows=search_data['sheet1_rows'])

if __name__ == '__main__':
    app.run(debug=True)
