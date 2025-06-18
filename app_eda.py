import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
            ---
            ## Population & Bike Demand EDA System

            이 웹앱은 두 가지 주요 데이터셋을 대상으로 탐색적 데이터 분석(EDA)을 수행합니다:

            1. **Bike Sharing Demand (자전거 수요)**
                - [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)
                - 2011~2012년 시간대별 자전거 대여 데이터
                - 다양한 날씨, 시간, 사용자 유형에 따른 대여량 분석

            2. **Population Trends (인구 동향)**
                - 대한민국 지역별 인구 변화 추이 데이터
                - 연도별, 지역별 인구 변화 시각화 및 증감률 분석

            로그인 후 'EDA' 탭에서 데이터셋을 업로드하고 다양한 분석 기능을 사용해보세요.  
        """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload population_trends.csv file.")
            return

        # Safe parsing
        df_preview = pd.read_csv(uploaded, nrows=5)
        uploaded.seek(0)
        if 'datetime' in df_preview.columns:
            df = pd.read_csv(uploaded, parse_dates=['datetime'])
        else:
            df = pd.read_csv(uploaded)

        # 세종 지역 처리 및 형변환
        df.loc[df['지역'] == '세종', ['인구', '출생아수(명)', '사망자수(명)']] = (
            df.loc[df['지역'] == '세종', ['인구', '출생아수(명)', '사망자수(명)']].replace('-', 0)
        )
        df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구', '출생아수(명)', '사망자수(명)']].apply(pd.to_numeric, errors='coerce')

        region_english = {
            '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
            '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
            '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
            '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
            '제주': 'Jeju'
        }
        df['지역영문'] = df['지역'].map(region_english)

        tabs = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

        with tabs[0]:
            st.subheader("📌 Basic Statistics")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())
            st.dataframe(df.describe())

            st.subheader("🧪 Null & Duplicate Check")
            st.write("결측치 개수:")
            st.write(df.isnull().sum())

            st.write(f"중복된 행 수: {df.duplicated().sum()}개")

        with tabs[1]:
            st.subheader("📈 Yearly Population Trend")
            national = df[df['지역'] == '전국']
            recent = national[national['연도'] >= national['연도'].max() - 2]
            net = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
            forecast = national.iloc[-1]['인구'] + net * (2035 - national.iloc[-1]['연도'])
            fig, ax = plt.subplots()
            ax.plot(national['연도'], national['인구'], label='Actual')
            ax.scatter(2035, forecast, color='red', label='Forecast')
            ax.set_title("National Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()
            st.pyplot(fig)
            st.caption(f"Forecasted population for 2035: {int(forecast):,}")

        with tabs[2]:
            st.subheader("📊 Regional 5-Year Change")
            recent = df[df['지역'] != '전국']
            max_y, min_y = recent['연도'].max(), recent['연도'].max() - 5
            pivot = recent.pivot(index='지역영문', columns='연도', values='인구')
            pivot['Change'] = (pivot[max_y] - pivot[min_y]) / 1000
            pivot['Rate'] = ((pivot[max_y] - pivot[min_y]) / pivot[min_y]) * 100
            pivot = pivot.sort_values(by='Change', ascending=False).reset_index()

            fig1, ax1 = plt.subplots()
            sns.barplot(y='지역영문', x='Change', data=pivot, ax=ax1)
            for i, v in enumerate(pivot['Change']):
                ax1.text(v, i, f"{v:.1f}", va='center')
            ax1.set_title("Population Change (thousands)")
            st.pyplot(fig1)

            fig2, ax2 = plt.subplots()
            sns.barplot(y='지역영문', x='Rate', data=pivot, ax=ax2)
            for i, v in enumerate(pivot['Rate']):
                ax2.text(v, i, f"{v:.1f}%", va='center')
            ax2.set_title("Population Change Rate (%)")
            st.pyplot(fig2)

        with tabs[3]:
            st.subheader("🔍 Top 100 Regional-Year Changes")
            local = df[df['지역'] != '전국'].copy()
            local.sort_values(by=['지역영문', '연도'], inplace=True)
            local['증감'] = local.groupby('지역영문')['인구'].diff()
            top = local.sort_values(by='증감', key=abs, ascending=False).head(100)

            # 스타일 적용은 숫자형으로 하고, 포맷만 시각적으로 처리
            styled_df = top[['연도', '지역영문', '인구', '증감']].copy()

            st.dataframe(
                styled_df.style
                    .format({'인구': '{:,.0f}', '증감': '{:,.0f}'})
                    .background_gradient(subset='증감', cmap='RdBu_r')
            )
    

        with tabs[4]:
            st.subheader("🌈 Stacked Area Plot by Region")
            df_area = df[df['지역'] != '전국']
            pivot_area = df_area.pivot(index='연도', columns='지역영문', values='인구')
            fig, ax = plt.subplots(figsize=(12, 6))
            pivot_area.plot.area(ax=ax, colormap='tab20')
            ax.set_title("Population by Region over Time")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(title="Region", bbox_to_anchor=(1.02, 1), loc='upper left')
            st.pyplot(fig)
            st.caption("Each region's contribution to population over time.")


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()