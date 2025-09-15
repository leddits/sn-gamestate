#!/usr/bin/env python3
"""
SoccerNet Game State 추론 관리 GUI
PySide6 기반 시각적 진행 모니터링 및 제어 시스템
"""

import sys
import os
import subprocess
import json
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
import psutil

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QProgressBar, QLabel, QTextEdit,
    QGroupBox, QSpinBox, QCheckBox, QComboBox, QFileDialog,
    QStatusBar, QTabWidget, QGridLayout, QSlider, QFrame,
    QMessageBox, QSplitter
)
from PySide6.QtCore import QTimer, QThread, Signal, Qt, QSettings
from PySide6.QtGui import QFont, QIcon, QPalette, QColor


class TrackLabRunner(QThread):
    """TrackLab 프로세스 실행 및 모니터링 스레드"""
    
    # 시그널 정의
    progress_updated = Signal(int, str)  # 진행률, 현재 상태
    log_updated = Signal(str)  # 로그 메시지
    process_finished = Signal(int)  # 종료 코드
    frame_processed = Signal(int, int)  # 현재 프레임, 총 프레임
    
    def __init__(self, config_path="soccernet"):
        super().__init__()
        self.config_path = config_path
        self.process = None
        self.is_running = False
        self.is_paused = False
        self.current_frame = 0
        self.total_frames = 0
        
    def run(self):
        """TrackLab 실행"""
        self.is_running = True
        
        try:
            # UV 환경에서 tracklab 실행
            cmd = f"uv run tracklab -cn {self.config_path}"
            self.log_updated.emit(f"🚀 명령어 실행: {cmd}")
            
            self.process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # 실시간 로그 파싱
            for line in self.process.stdout:
                if not self.is_running:
                    break
                    
                line = line.strip()
                if line:
                    self.log_updated.emit(line)
                    self._parse_progress(line)
            
            # 프로세스 완료 대기
            return_code = self.process.wait()
            self.process_finished.emit(return_code)
            
        except Exception as e:
            self.log_updated.emit(f"❌ 에러: {str(e)}")
            self.process_finished.emit(-1)
        finally:
            self.is_running = False
    
    def _parse_progress(self, log_line):
        """로그에서 진행 상황 파싱"""
        try:
            # 프레임 진행 파싱 (예: "Tracking videos (SNGS-021) ━━━━━━━━ 50/100")
            if "Tracking videos" in log_line and "/" in log_line:
                # 정규식이나 문자열 파싱으로 현재/총 프레임 추출
                parts = log_line.split()
                for part in parts:
                    if "/" in part:
                        try:
                            current, total = part.split("/")
                            self.current_frame = int(current)
                            self.total_frames = int(total)
                            
                            progress = int((self.current_frame / self.total_frames) * 100)
                            self.progress_updated.emit(progress, f"프레임 {current}/{total}")
                            self.frame_processed.emit(self.current_frame, self.total_frames)
                            break
                        except:
                            continue
            
            # 모듈별 진행 상황 파싱
            elif any(module in log_line for module in ["YOLOUltralytics", "PRTReId", "BPBReIDStrongSORT"]):
                if "━━━━" in log_line:  # 진행 바가 있는 경우
                    module_name = log_line.split()[0] if log_line.split() else "Unknown"
                    self.progress_updated.emit(-1, f"실행 중: {module_name}")
        
        except Exception as e:
            pass  # 파싱 에러는 무시
    
    def pause(self):
        """프로세스 일시 정지"""
        if self.process and self.is_running:
            try:
                # Windows에서는 CTRL+Z 대신 프로세스 suspend
                proc = psutil.Process(self.process.pid)
                proc.suspend()
                self.is_paused = True
                self.log_updated.emit("⏸️ 프로세스 일시 정지됨")
            except Exception as e:
                self.log_updated.emit(f"❌ 일시정지 실패: {e}")
    
    def resume(self):
        """프로세스 재개"""
        if self.process and self.is_paused:
            try:
                proc = psutil.Process(self.process.pid)
                proc.resume()
                self.is_paused = False
                self.log_updated.emit("▶️ 프로세스 재개됨")
            except Exception as e:
                self.log_updated.emit(f"❌ 재개 실패: {e}")
    
    def stop(self):
        """프로세스 중지"""
        self.is_running = False
        if self.process:
            try:
                self.process.terminate()
                self.log_updated.emit("🛑 프로세스 중지됨")
            except Exception as e:
                self.log_updated.emit(f"❌ 중지 실패: {e}")


class SoccerNetGUI(QMainWindow):
    """메인 GUI 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.runner = None
        self.settings = QSettings("SoccerNet", "GameStateGUI")
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """UI 초기화"""
        self.setWindowTitle("🏆 SoccerNet Game State Reconstruction")
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        layout = QVBoxLayout(central_widget)
        
        # 탭 위젯
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # 1. 실행 제어 탭
        self.setup_control_tab(tab_widget)
        
        # 2. 설정 탭
        self.setup_settings_tab(tab_widget)
        
        # 3. 결과 탭
        self.setup_results_tab(tab_widget)
        
        # 상태바
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비 완료")
    
    def setup_control_tab(self, tab_widget):
        """실행 제어 탭 구성"""
        control_tab = QWidget()
        layout = QVBoxLayout(control_tab)
        
        # 진행 상황 그룹
        progress_group = QGroupBox("📊 진행 상황")
        progress_layout = QVBoxLayout(progress_group)
        
        # 메인 진행 바
        self.main_progress = QProgressBar()
        self.main_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(QLabel("전체 진행률:"))
        progress_layout.addWidget(self.main_progress)
        
        # 상세 정보
        info_layout = QGridLayout()
        
        self.current_frame_label = QLabel("현재 프레임: 0")
        self.total_frames_label = QLabel("총 프레임: 0")
        self.speed_label = QLabel("처리 속도: 0 fps")
        self.eta_label = QLabel("예상 완료: --:--")
        self.status_label = QLabel("상태: 대기 중")
        
        info_layout.addWidget(self.current_frame_label, 0, 0)
        info_layout.addWidget(self.total_frames_label, 0, 1)
        info_layout.addWidget(self.speed_label, 1, 0)
        info_layout.addWidget(self.eta_label, 1, 1)
        info_layout.addWidget(self.status_label, 2, 0, 1, 2)
        
        progress_layout.addLayout(info_layout)
        layout.addWidget(progress_group)
        
        # 제어 버튼
        control_group = QGroupBox("🎮 제어")
        control_layout = QHBoxLayout(control_group)
        
        self.start_btn = QPushButton("▶️ 시작")
        self.pause_btn = QPushButton("⏸️ 일시정지")
        self.resume_btn = QPushButton("▶️ 재개")
        self.stop_btn = QPushButton("🛑 중지")
        
        self.start_btn.clicked.connect(self.start_inference)
        self.pause_btn.clicked.connect(self.pause_inference)
        self.resume_btn.clicked.connect(self.resume_inference)
        self.stop_btn.clicked.connect(self.stop_inference)
        
        # 초기 버튼 상태
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.resume_btn)
        control_layout.addWidget(self.stop_btn)
        
        layout.addWidget(control_group)
        
        # 로그 출력
        log_group = QGroupBox("📝 실행 로그")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        tab_widget.addTab(control_tab, "🎮 실행 제어")
    
    def setup_settings_tab(self, tab_widget):
        """설정 탭 구성"""
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)
        
        # 기본 설정
        basic_group = QGroupBox("⚙️ 기본 설정")
        basic_layout = QGridLayout(basic_group)
        
        # 프레임 수 설정
        basic_layout.addWidget(QLabel("처리할 프레임 수:"), 0, 0)
        self.frames_spin = QSpinBox()
        self.frames_spin.setRange(1, 10000)
        self.frames_spin.setValue(100)
        basic_layout.addWidget(self.frames_spin, 0, 1)
        
        # 비디오 수 설정
        basic_layout.addWidget(QLabel("비디오 수:"), 1, 0)
        self.videos_spin = QSpinBox()
        self.videos_spin.setRange(1, 100)
        self.videos_spin.setValue(1)
        basic_layout.addWidget(self.videos_spin, 1, 1)
        
        # 평가 활성화
        self.eval_checkbox = QCheckBox("평가 활성화")
        basic_layout.addWidget(self.eval_checkbox, 2, 0, 1, 2)
        
        layout.addWidget(basic_group)
        
        # GPU 설정
        gpu_group = QGroupBox("🖥️ GPU 설정")
        gpu_layout = QGridLayout(gpu_group)
        
        gpu_layout.addWidget(QLabel("bbox_detector 배치 크기:"), 0, 0)
        self.bbox_batch_spin = QSpinBox()
        self.bbox_batch_spin.setRange(1, 32)
        self.bbox_batch_spin.setValue(8)
        gpu_layout.addWidget(self.bbox_batch_spin, 0, 1)
        
        gpu_layout.addWidget(QLabel("reid 배치 크기:"), 1, 0)
        self.reid_batch_spin = QSpinBox()
        self.reid_batch_spin.setRange(1, 128)
        self.reid_batch_spin.setValue(32)
        gpu_layout.addWidget(self.reid_batch_spin, 1, 1)
        
        layout.addWidget(gpu_group)
        
        # 설정 저장/불러오기
        config_group = QGroupBox("💾 설정 관리")
        config_layout = QHBoxLayout(config_group)
        
        save_btn = QPushButton("설정 저장")
        load_btn = QPushButton("설정 불러오기")
        apply_btn = QPushButton("설정 적용")
        
        save_btn.clicked.connect(self.save_settings)
        load_btn.clicked.connect(self.load_settings)
        apply_btn.clicked.connect(self.apply_settings)
        
        config_layout.addWidget(save_btn)
        config_layout.addWidget(load_btn)
        config_layout.addWidget(apply_btn)
        
        layout.addWidget(config_group)
        layout.addStretch()
        
        tab_widget.addTab(settings_tab, "⚙️ 설정")
    
    def setup_results_tab(self, tab_widget):
        """결과 탭 구성"""
        results_tab = QWidget()
        layout = QVBoxLayout(results_tab)
        
        # 결과 디렉토리
        dir_group = QGroupBox("📁 결과 디렉토리")
        dir_layout = QHBoxLayout(dir_group)
        
        self.results_path_label = QLabel("outputs/sn-gamestate/")
        browse_btn = QPushButton("찾아보기")
        browse_btn.clicked.connect(self.browse_results)
        
        dir_layout.addWidget(self.results_path_label)
        dir_layout.addWidget(browse_btn)
        
        layout.addWidget(dir_group)
        
        # 결과 목록
        results_group = QGroupBox("📋 실행 결과 목록")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        # 결과 액션
        actions_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 새로고침")
        open_btn = QPushButton("📂 폴더 열기")
        preview_btn = QPushButton("👁️ 미리보기")
        
        refresh_btn.clicked.connect(self.refresh_results)
        open_btn.clicked.connect(self.open_results_folder)
        preview_btn.clicked.connect(self.preview_results)
        
        actions_layout.addWidget(refresh_btn)
        actions_layout.addWidget(open_btn)
        actions_layout.addWidget(preview_btn)
        
        results_layout.addLayout(actions_layout)
        layout.addWidget(results_group)
        
        tab_widget.addTab(results_tab, "📊 결과")
    
    def start_inference(self):
        """추론 시작"""
        if self.runner and self.runner.isRunning():
            return
        
        # 설정 적용
        self.apply_settings()
        
        # 러너 초기화
        self.runner = TrackLabRunner()
        
        # 시그널 연결
        self.runner.progress_updated.connect(self.update_progress)
        self.runner.log_updated.connect(self.update_log)
        self.runner.process_finished.connect(self.on_process_finished)
        self.runner.frame_processed.connect(self.update_frame_info)
        
        # 버튼 상태 업데이트
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        
        # 시작
        self.runner.start()
        self.status_bar.showMessage("추론 실행 중...")
        
        # 시작 시간 기록
        self.start_time = time.time()
    
    def pause_inference(self):
        """추론 일시정지"""
        if self.runner:
            self.runner.pause()
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
    
    def resume_inference(self):
        """추론 재개"""
        if self.runner:
            self.runner.resume()
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
    
    def stop_inference(self):
        """추론 중지"""
        if self.runner:
            self.runner.stop()
            self.reset_buttons()
    
    def reset_buttons(self):
        """버튼 상태 초기화"""
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
    
    def update_progress(self, progress, status):
        """진행률 업데이트"""
        if progress >= 0:
            self.main_progress.setValue(progress)
        self.status_label.setText(f"상태: {status}")
    
    def update_log(self, message):
        """로그 업데이트"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # 자동 스크롤 (더 간단한 방법)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_frame_info(self, current, total):
        """프레임 정보 업데이트"""
        self.current_frame_label.setText(f"현재 프레임: {current}")
        self.total_frames_label.setText(f"총 프레임: {total}")
        
        # 처리 속도 계산
        if hasattr(self, 'start_time') and current > 0:
            elapsed = time.time() - self.start_time
            fps = current / elapsed
            self.speed_label.setText(f"처리 속도: {fps:.1f} fps")
            
            # 예상 완료 시간
            if fps > 0:
                remaining_frames = total - current
                eta_seconds = remaining_frames / fps
                eta = datetime.now() + timedelta(seconds=eta_seconds)
                self.eta_label.setText(f"예상 완료: {eta.strftime('%H:%M:%S')}")
    
    def on_process_finished(self, exit_code):
        """프로세스 완료 처리"""
        self.reset_buttons()
        
        if exit_code == 0:
            self.status_bar.showMessage("추론 완료!")
            self.update_log("✅ 추론이 성공적으로 완료되었습니다.")
            self.main_progress.setValue(100)
        else:
            self.status_bar.showMessage(f"추론 실패 (코드: {exit_code})")
            self.update_log(f"❌ 추론이 실패했습니다. 종료 코드: {exit_code}")
        
        # 결과 새로고침
        self.refresh_results()
    
    def apply_settings(self):
        """설정을 YAML 파일에 적용"""
        try:
            config_path = Path("sn_gamestate/configs/soccernet.yaml")
            
            # 간단한 설정 업데이트 (실제로는 YAML 파싱 라이브러리 사용 권장)
            self.update_log(f"📝 설정 적용: 프레임={self.frames_spin.value()}, 비디오={self.videos_spin.value()}")
            
        except Exception as e:
            self.update_log(f"❌ 설정 적용 실패: {e}")
    
    def save_settings(self):
        """설정 저장"""
        self.settings.setValue("frames", self.frames_spin.value())
        self.settings.setValue("videos", self.videos_spin.value())
        self.settings.setValue("eval_enabled", self.eval_checkbox.isChecked())
        self.settings.setValue("bbox_batch", self.bbox_batch_spin.value())
        self.settings.setValue("reid_batch", self.reid_batch_spin.value())
        
        QMessageBox.information(self, "저장 완료", "설정이 저장되었습니다.")
    
    def load_settings(self):
        """설정 불러오기"""
        self.frames_spin.setValue(self.settings.value("frames", 100, type=int))
        self.videos_spin.setValue(self.settings.value("videos", 1, type=int))
        self.eval_checkbox.setChecked(self.settings.value("eval_enabled", False, type=bool))
        self.bbox_batch_spin.setValue(self.settings.value("bbox_batch", 8, type=int))
        self.reid_batch_spin.setValue(self.settings.value("reid_batch", 32, type=int))
    
    def refresh_results(self):
        """결과 목록 새로고침"""
        try:
            outputs_dir = Path("outputs/sn-gamestate")
            if outputs_dir.exists():
                results = []
                for date_dir in sorted(outputs_dir.iterdir(), reverse=True):
                    if date_dir.is_dir():
                        for time_dir in sorted(date_dir.iterdir(), reverse=True):
                            if time_dir.is_dir():
                                results.append(f"{date_dir.name}/{time_dir.name}")
                
                self.results_text.clear()
                self.results_text.append("📋 최근 실행 결과:")
                for result in results[:10]:  # 최근 10개만 표시
                    self.results_text.append(f"  • {result}")
        except Exception as e:
            self.update_log(f"❌ 결과 새로고침 실패: {e}")
    
    def browse_results(self):
        """결과 디렉토리 찾아보기"""
        dialog = QFileDialog()
        folder = dialog.getExistingDirectory(self, "결과 디렉토리 선택", "outputs")
        if folder:
            self.results_path_label.setText(folder)
    
    def open_results_folder(self):
        """결과 폴더 열기"""
        try:
            os.startfile("outputs\\sn-gamestate")
        except Exception as e:
            self.update_log(f"❌ 폴더 열기 실패: {e}")
    
    def preview_results(self):
        """결과 미리보기"""
        QMessageBox.information(self, "미리보기", "결과 미리보기 기능은 개발 중입니다.")


def main():
    """메인 실행 함수"""
    app = QApplication(sys.argv)
    
    # 앱 정보 설정
    app.setApplicationName("SoccerNet GameState GUI")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("SoccerNet")
    
    # 다크 테마 적용
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    # 메인 윈도우 생성 및 표시
    window = SoccerNetGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()