import cv2
import time
import random
import sys
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading

# --- 관상 데이터 (한글) ---
# MZ 세대가 흥미를 느낄 만한 재미있는 관상 데이터입니다.
PHYSIOGNOMY_DATA = [
    {"title": "강력한 리더 관상 👑", "description": "매우 강인하고 확고한 의지를 가진 관상입니다. 타고난 리더십과 추진력으로 주변 사람들을 이끌어 성공을 쟁취할 운명입니다. 이마가 넓고 눈빛이 깊어 통찰력이 뛰어납니다."},
    {"title": "친화력 만렙 관상 ✨", "description": "온화하고 사람들에게 인기가 많으며, 어디서든 분위기를 좋게 만드는 재주가 있습니다. 입꼬리가 살짝 올라가 있어 항상 긍정적인 에너지를 발산하며 재물운이 따릅니다."},
    {"title": "천재 예술가 관상 🎨", "description": "창의적이고 예술적 감각이 매우 뛰어난 관상입니다. 남들과 다른 독특한 시각을 가졌으며, 눈썹과 눈 사이가 넓어 지혜롭고 섬세한 분야에서 큰 성공을 거둡니다."},
    {"title": "재물 복 터진 관상 💰", "description": "볼과 턱 부분이 탄탄하고 귀가 커서 재물 복이 넘쳐나는 관상입니다. 안정적인 성격으로 투자에서도 성공을 거두며, 만년에는 부와 명예를 모두 얻을 것입니다."}
]

class FaceAnalyzerApp(tk.Tk):
    """
    Tkinter를 사용하여 웹캠 피드 및 관상 분석 결과를 표시하는 GUI 애플리케이션 클래스입니다.
    """
    def __init__(self):
        super().__init__()
        self.title("🔮 MZ 스타일 관상 분석기")
        # GUI 크기를 충분히 늘려서 모든 요소가 보이도록 조정
        self.geometry("900x900") 
        self.resizable(False, False)
        
        # 웹캠 관련 변수
        self.video_capture = None
        self.video_thread = None
        self.stop_event = threading.Event()
        self.is_analyzing = False
        # 웹캠 피드 크기 설정
        self.webcam_width = 640 
        self.webcam_height = 480
        
        # Tkinter의 grid 레이아웃 설정
        self.grid_columnconfigure(0, weight=1)
        self.setup_ui()

    def setup_ui(self):
        """GUI 구성 요소를 설정합니다."""
        
        # 1. 웹캠 피드 영역을 담을 프레임 (크기 고정)
        self.webcam_frame = tk.Frame(self, width=self.webcam_width, height=self.webcam_height, bg="#2c3e50")
        self.webcam_frame.grid(row=0, column=0, pady=20, padx=20)
        self.webcam_frame.grid_propagate(False)  # 프레임 크기 고정
        
        # 웹캠 라벨 (프레임 내부에 배치)
        self.webcam_label = tk.Label(self.webcam_frame, text="[웹캠 대기 중]", 
                                     bg="#2c3e50", fg="white", font=("Helvetica", 16))
        self.webcam_label.place(relx=0.5, rely=0.5, anchor='center')

        # 2. 상태/결과 메시지 영역 (웹캠 아래)
        self.status_label = tk.Label(self, text="카메라 시작 버튼을 눌러주세요.", 
                                     font=("Helvetica", 14, "bold"), fg="#34495e")
        self.status_label.grid(row=1, column=0, pady=(10, 5))
        
        # 3. 관상 분석 결과 영역 (상태 라벨 아래)
        self.result_frame = tk.Frame(self)
        self.result_frame.grid(row=2, column=0, pady=(10, 10), padx=20, sticky='ew')
        
        self.result_title = tk.Label(self.result_frame, text="결과 대기 중", 
                                     font=("Helvetica", 18, "bold"), fg="#8e44ad")
        self.result_title.pack()
        
        self.result_description = tk.Label(self.result_frame, text="분석이 완료되면 여기에 관상이 표시됩니다.", 
                                           font=("Helvetica", 12), wraplength=800, justify='center')
        self.result_description.pack()

        # 4. 버튼 영역 (중앙 하단)
        button_frame = tk.Frame(self)
        button_frame.grid(row=3, column=0, pady=(10, 30))
        
        # '카메라 시작' 버튼
        self.start_button = tk.Button(button_frame, text="📷 카메라 시작", 
                                      command=self.start_camera, 
                                      bg="#2ecc71", fg="white", font=("Helvetica", 12, "bold"), 
                                      padx=15, pady=8)
        self.start_button.pack(side=tk.LEFT, padx=10)

        # '분석' 버튼
        self.analyze_button = tk.Button(button_frame, text="✨ 관상 분석 시작", 
                                        command=self.start_analysis, 
                                        bg="#f39c12", fg="white", font=("Helvetica", 12, "bold"), 
                                        padx=15, pady=8, state=tk.DISABLED)
        self.analyze_button.pack(side=tk.LEFT, padx=10)

        # '종료' 버튼
        self.exit_button = tk.Button(button_frame, text="❌ 프로그램 종료", 
                                     command=self.exit_app, 
                                     bg="#e74c3c", fg="white", font=("Helvetica", 12, "bold"), 
                                     padx=15, pady=8)
        self.exit_button.pack(side=tk.LEFT, padx=10)
        
        # 창이 닫힐 때 exit_app 함수가 실행되도록 설정
        self.protocol("WM_DELETE_WINDOW", self.exit_app)

    def start_camera(self):
        """웹캠을 초기화하고 비디오 루프 스레드를 시작합니다."""
        if self.video_capture is not None and self.video_capture.isOpened():
            messagebox.showinfo("정보", "카메라가 이미 실행 중입니다.")
            return

        # '기다려주세요' 문구 표시
        self.webcam_label.config(text="⏳ 기다려주세요...\n웹캠을 연결하는 중입니다.", 
                                font=("Helvetica", 14, "bold"))
        self.status_label.config(text="⏳ 웹캠 연결 중...", fg="#e67e22")
        self.start_button.config(state=tk.DISABLED)
        
        # GUI 업데이트를 위해 잠시 대기
        self.update()
        
        # 웹캠 연결을 별도 스레드에서 처리 (GUI 멈춤 방지)
        camera_thread = threading.Thread(target=self._initialize_camera)
        camera_thread.start()

    def _initialize_camera(self):
        """웹캠을 초기화하는 함수 (별도 스레드에서 실행)"""
        camera_found = False
        
        # 웹캠 인덱스 순차 시도 (0, 1, 2)
        for index in range(3):
            self.video_capture = cv2.VideoCapture(index)
            time.sleep(0.5) # 초기화 대기
            
            if self.video_capture.isOpened():
                camera_found = True
                # GUI 업데이트 (메인 스레드에서 실행)
                self.after(0, lambda idx=index: self._on_camera_success(idx))
                return

            self.video_capture.release()

        # 웹캠을 찾지 못한 경우
        if not camera_found:
            self.after(0, self._on_camera_failure)

    def _on_camera_success(self, camera_index):
        """웹캠 연결 성공 시 호출되는 함수"""
        self.status_label.config(text=f"✅ 웹캠 (인덱스 {camera_index}) 연결 성공!", fg="#27ae60")
        # '기다려주세요' 문구 제거
        self.webcam_label.config(text="")
        self.analyze_button.config(state=tk.NORMAL)
        
        # 비디오 루프 스레드 시작
        self.stop_event.clear()
        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()

    def _on_camera_failure(self):
        """웹캠 연결 실패 시 호출되는 함수"""
        messagebox.showerror("오류", "사용 가능한 웹캠 장치를 찾을 수 없습니다.\n연결 및 권한을 확인하세요.")
        self.status_label.config(text="❌ 웹캠 연결 실패", fg="#e74c3c")
        self.webcam_label.config(text="[웹캠 연결 실패]")
        self.start_button.config(state=tk.NORMAL)

    def video_loop(self):
        """웹캠에서 프레임을 읽고 GUI에 표시하는 반복 함수 (별도 스레드에서 실행)."""
        try:
            while not self.stop_event.is_set():
                if self.video_capture is None or not self.video_capture.isOpened():
                    break
                    
                ret, frame = self.video_capture.read()
                if not ret:
                    break

                # 프레임 업데이트 (메인 스레드에서 안전하게 실행)
                self.after(0, lambda f=frame.copy(): self._update_webcam_frame(f))

                time.sleep(0.03) # 약 30 FPS
        
        except Exception as e:
            if not self.stop_event.is_set():
                print(f"비디오 루프 오류: {e}")

    def _update_webcam_frame(self, frame):
        """웹캠 프레임을 Tkinter Label에 표시합니다."""
        try:
            # 프레임 크기 조정
            frame = cv2.resize(frame, (self.webcam_width, self.webcam_height))
            frame = cv2.flip(frame, 1) # 좌우 반전 (거울 모드)
            
            # 분석 중일 때 오버레이 표시
            if self.is_analyzing:
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (self.webcam_width, 60), (0, 0, 0), -1)
                frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
                cv2.putText(frame, "Analyzing... Please Wait!", (20, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
            
            # BGR을 RGB로 변환
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # PIL Image로 변환
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # GUI 업데이트
            self.webcam_label.imgtk = imgtk
            self.webcam_label.config(image=imgtk)
        except Exception as e:
            print(f"프레임 업데이트 오류: {e}")

    def start_analysis(self):
        """'분석 버튼'을 눌렀을 때 관상 분석을 시뮬레이션합니다."""
        if self.is_analyzing:
            return
        if self.video_capture is None or not self.video_capture.isOpened():
            messagebox.showerror("오류", "먼저 '카메라 시작' 버튼을 눌러주세요.")
            return

        # '기다려주세요' 멘트 출력
        self.status_label.config(text="⏳ [관상 분석 중] 기다려주세요!", fg="#e67e22")
        self.analyze_button.config(state=tk.DISABLED)
        self.is_analyzing = True

        # 분석은 GUI를 멈추지 않도록 별도의 스레드에서 실행
        analysis_thread = threading.Thread(target=self._run_analysis_simulation, daemon=True)
        analysis_thread.start()

    def _run_analysis_simulation(self):
        """실제 분석 로직 (3초 시뮬레이션) 및 결과 표시."""
        time.sleep(3) # 3초 시뮬레이션 시간

        self.is_analyzing = False
        
        # 랜덤 관상 결과 선택
        result = random.choice(PHYSIOGNOMY_DATA)
        
        # GUI 업데이트 (메인 스레드에서 실행)
        self.after(0, lambda: self._display_result(result))

    def _display_result(self, result):
        """분석 결과를 GUI에 표시합니다."""
        # '인식 완료' 멘트 출력
        self.status_label.config(text="✅ 인식 완료! 아래 결과를 확인하세요.", fg="#27ae60")
        
        self.result_title.config(text=f"🔥 당신의 관상은? : {result['title']}")
        self.result_description.config(text=result['description'], wraplength=800) 
        self.analyze_button.config(state=tk.NORMAL)
        
    def exit_app(self):
        """프로그램 종료: 웹캠 해제 및 앱 종료."""
        
        # 스레드 종료 이벤트 설정
        self.stop_event.set()
        
        # 웹캠 해제
        if self.video_capture is not None:
            self.video_capture.release()
            
        # 모든 OpenCV 창 닫기
        cv2.destroyAllWindows()
        
        # 스레드 종료 대기
        if self.video_thread is not None and self.video_thread.is_alive():
            self.video_thread.join(timeout=1)
            
        # 애플리케이션 종료
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = FaceAnalyzerApp()
    app.mainloop()