# --- 필수 라이브러리 임포트 ---
import sys  # 시스템 종료 등에 사용
import mysql.connector  # MySQL DB와 연결하기 위한 라이브러리
import matplotlib  # 폰트 설정 등
import matplotlib.pyplot as plt  # 그래프 그리기 도구
import matplotlib.dates as mdates

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout  # GUI 구성 요소들
from PyQt5.QtCore import QTimer  # 타이머: 주기적으로 작업 수행할 때 사용
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas  # PyQt 위에 matplotlib 그래프 출력용
from test1 import Ui_MainWindow  # Qt Designer로 만든 UI를 파이썬으로 변환한 모듈 (test.ui → test.py)

matplotlib.rc('font', family='Malgun Gothic')  # 한글 깨짐 방지 (Windows용)
matplotlib.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지


# --- 메인 윈도우 클래스 정의 ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # UI 설정: test.ui에서 만든 위젯 연결
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.load_title()

        # --- 그래프 위젯 설정 ---
        # matplotlib 캔버스 생성
        self.canvas = FigureCanvas(plt.figure())

        # 그래프를 올릴 레이아웃 설정 (Qt 디자이너에서 만든 graphWidget 위젯에 적용)
        layout = QVBoxLayout()
        self.ui.graphWidget.setLayout(layout)
        layout.addWidget(self.canvas)  # 캔버스를 레이아웃에 추가

        # --- MySQL 데이터베이스 연결 ---
        self.db = mysql.connector.connect(
            host="10.10.10.113",     # DB 서버 IP 주소 (라즈베리파이 등)
            user="root",             # 사용자명
            password="1234",         # 비밀번호
            database="tp_dht11_db",        # 사용할 데이터베이스 이름
            autocommit=True          # INSERT 후 자동 커밋
        )
        self.cursor = self.db.cursor(buffered=True)  # 커서 생성 (buffered=True → fetch 전 재실행 가능)

        # --- 그래프에 사용할 데이터 리스트 ---
        self.x_data = []      # 시간 정보
        self.temp_data = []   # 온도 값
        self.hum_data = []    # 습도 값

        # --- 타이머 설정: 1초마다 그래프 갱신 ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)  # 타이머가 만료될 때 update_graph 함수 실행
        # self.timer.start(1000)  # 1000ms = 1초 주기

        # --- 버튼 연결: 실시간 그래프가기 ---
        self.ui.btnGraph.clicked.connect(self.go_to_graph)
        # --- 버튼 연결: 프로그램 종료 ---
        self.ui.btnExit.clicked.connect(self.close)
        # --- 버튼 연결: 뒤로 가기 기능 ---
        self.ui.btnBackGraph.clicked.connect(self.go_to_main)

    # --- 그래프 갱신 함수 ---
    def update_graph(self):
        print("--- 새 데이터 ---")

        try:
            # 1. 최신 데이터 10개 조회 (recorded_at 기준 정렬)
            self.cursor.execute("""
                SELECT time, temperature, humidity 
                FROM measured_value
                ORDER BY time DESC
                LIMIT 10
            """)
            rows = self.cursor.fetchall()
            rows.reverse()  # 최근 → 과거 순서로 정렬 (x축이 자연스럽게 보이도록)

            # 2. 데이터 분리 저장
            self.x_data = [row[0] for row in rows]  # time: datetime 객체
            self.temp_data = [row[1] for row in rows]  # 온도 값
            self.hum_data = [row[2] for row in rows]   # 습도 값

            # 3. 그래프 초기화
            self.canvas.figure.clear()
            fig = self.canvas.figure


            # --- (1) 온도 그래프 ---
            ax1 = fig.add_subplot(211)  # 2행 1열 중 첫 번째 subplot
            ax1.plot(self.x_data, self.temp_data, color='red', marker='o', label="온도(℃)")  # 온도 선 그래프

            # 각 지점 위에 숫자 표시
            for i, v in enumerate(self.temp_data):
                ax1.text(self.x_data[i], v + 0.3, f"{v:.1f}℃", ha='center', fontsize=8, color='red')

            ax1.set_ylabel("온도(℃)")  # y축 라벨
            ax1.grid(True)  # 격자 추가

            # --- (2) 습도 그래프 ---
            ax2 = fig.add_subplot(212)  # 2행 1열 중 두 번째 subplot
            ax2.plot(self.x_data, self.hum_data, color='blue', marker='o', label="습도(%)")  # 습도 선 그래프

            # 각 지점 위에 숫자 표시
            for i, v in enumerate(self.hum_data):
                ax2.text(self.x_data[i], v + 0.5, f"{v:.1f}%", ha='center', fontsize=8, color='blue')

            ax2.set_ylabel("습도(%)")
            ax2.set_xlabel("시간")  # x축 라벨
            ax2.grid(True)

            # x축 시간 포맷 통일 (두 번째 그래프에만 적용)

            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            ax2.figure.autofmt_xdate()  # x축 라벨 겹침 방지 회전

            # 4. 그래프 다시 그리기
            self.canvas.draw()

        except Exception as e:
            print("DB 조회 에러:", e)

    # --- 뒤로가기 버튼 이벤트 처리 함수 ---
    def go_to_main(self):
        # stackedWidget의 첫 번째 페이지(main 화면)로 전환
        self.timer.stop()  # ✅ 그래프 꺼졌으면 타이머도 멈춤
        self.ui.stackedWidget.setCurrentIndex(0)

    # --- 그래프가기 버튼 이벤트 처리 함수 ---
    def go_to_graph(self):
        self.ui.stackedWidget.setCurrentIndex(1)
        self.update_graph()  # ✅ 첫 데이터 즉시 갱신
        self.timer.start(1000)  # ✅ 이후부터 주기적 갱신 시작

    # --- 창닫힐 때 타이틀 저장 함수 ---
    def closeEvent(self, event):
        # 창 닫힐 때 실행됨
        current_title = self.ui.titleEdit.text()
        with open("title.txt", "w", encoding="utf-8") as f:
            f.write(current_title)
        event.accept()  # 닫기 계속 진행

    # --- 저장된 타이틀로 변경하는 함수 ---
    def load_title(self):
        try:
            with open("title.txt", "r", encoding="utf-8") as f:
                saved_title = f.read().strip()
                self.ui.titleEdit.setText(saved_title)
        except FileNotFoundError:
            # 파일이 처음 실행되었거나 없으면 기본값 그대로
            pass


# --- 애플리케이션 실행 부분 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)     # PyQt 앱 초기화
    window = MainWindow()            # 메인 윈도우 인스턴스 생성
    window.show()                    # GUI 창 띄우기
    sys.exit(app.exec_())            # 이벤트 루프 실행 (종료될 때까지 대기)