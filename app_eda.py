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
# 인구 분석 클래스
# ---------------------
class PopulationEDA:
    def __init__(self):
        st.title("📈 Population Analysis")
        uploaded_file = st.file_uploader("Upload population_trends.csv", type=["csv"])
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)

            # 세종 지역 '-' -> 0
            df.loc[df['지역'] == '세종'] = df[df['지역'] == '세종'].replace('-', 0)

            # 숫자형으로 변환
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce')
            df['출생아수(명)'] = pd.to_numeric(df['출생아수(명)'], errors='coerce')
            df['사망자수(명)'] = pd.to_numeric(df['사망자수(명)'], errors='coerce')

            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Basic Stats", "Trend", "Region Comparison", "Top Changes", "Heatmap"
            ])

            with tab1:
                st.subheader("Summary Statistics")
                buffer = io.StringIO()
                df.info(buf=buffer)
                st.text(buffer.getvalue())
                st.dataframe(df.describe())

            with tab2:
                st.subheader("Total Population Trend")
                national = df[df['지역'] == '전국']
                fig, ax = plt.subplots()
                sns.lineplot(data=national, x='연도', y='인구', ax=ax)
                ax.set_title("National Population Trend")
                st.pyplot(fig)

            with tab3:
                st.subheader("Recent 5-year Change by Region")
                pivot = df.pivot(index='연도', columns='지역', values='인구')
                recent = pivot.tail(5)
                delta = recent.iloc[-1] - recent.iloc[0]
                delta = delta.drop('전국', errors='ignore')
                delta_sorted = delta.sort_values(ascending=False)
                fig, ax = plt.subplots()
                sns.barplot(x=delta_sorted.values / 1000, y=delta_sorted.index, ax=ax)
                ax.set_xlabel("Change (thousands)")
                ax.set_title("5-Year Population Change")
                st.pyplot(fig)

                rate_change = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] * 100
                rate_change = rate_change.drop('전국', errors='ignore').sort_values(ascending=False)
                fig2, ax2 = plt.subplots()
                sns.barplot(x=rate_change.values, y=rate_change.index, ax=ax2)
                ax2.set_xlabel("Rate Change (%)")
                ax2.set_title("5-Year Population Rate Change")
                st.pyplot(fig2)

            with tab4:
                st.subheader("Top 100 Changes")
                df_sorted = df[df['지역'] != '전국'].sort_values(['지역', '연도'])
                df_sorted['증감'] = df_sorted.groupby('지역')['인구'].diff()
                top_100 = df_sorted.sort_values('증감', ascending=False).head(100)
                styled = top_100.style.background_gradient(
                    subset=['증감'], cmap='bwr', axis=0
                ).format({'증감': ","})
                st.dataframe(styled)

            with tab5:
                st.subheader("Population Heatmap")
                pivot_heat = df.pivot(index='지역', columns='연도', values='인구')
                fig3, ax3 = plt.subplots(figsize=(12, 8))
                sns.heatmap(pivot_heat, cmap='viridis', annot=False, fmt=".0f")
                ax3.set_title("Population by Region and Year")
                st.pyplot(fig3)

# ---------------------
# 기존 페이지 정의는 그대로 유지
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")
Page_Pop      = st.Page(PopulationEDA, title="Population", icon="📈", url_path="population")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA, Page_Pop]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
