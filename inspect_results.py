#!/usr/bin/env python3
"""
추론 결과 데이터 포맷 확인 스크립트
"""
import pickle
import gzip
from pathlib import Path

def inspect_tracker_state(state_path):
    """TrackerState 파일 분석"""
    print(f"📁 분석 중: {state_path}")
    
    try:
        # .pklz 파일 로드 (gzip 압축된 pickle)
        with gzip.open(state_path, 'rb') as f:
            tracker_state = pickle.load(f)
        
        print(f"✅ 파일 로드 성공")
        print(f"📊 TrackerState 타입: {type(tracker_state)}")
        
        # 기본 정보
        if hasattr(tracker_state, '__dict__'):
            print(f"\n🔍 주요 속성들:")
            for key, value in tracker_state.__dict__.items():
                if hasattr(value, '__len__'):
                    try:
                        print(f"  - {key}: {type(value)} (길이: {len(value)})")
                    except:
                        print(f"  - {key}: {type(value)}")
                else:
                    print(f"  - {key}: {type(value)} = {value}")
        
        # 탐지 결과 확인
        if hasattr(tracker_state, 'detections') and tracker_state.detections:
            print(f"\n🎯 탐지 결과:")
            print(f"  - 총 프레임 수: {len(tracker_state.detections)}")
            
            # 첫 번째 프레임 분석
            first_frame = list(tracker_state.detections.keys())[0]
            first_detections = tracker_state.detections[first_frame]
            print(f"  - 첫 번째 프레임 ({first_frame}): {len(first_detections)}개 탐지")
            
            if first_detections:
                det = first_detections[0]
                print(f"  - 탐지 객체 타입: {type(det)}")
                if hasattr(det, '__dict__'):
                    print(f"  - 탐지 속성들: {list(det.__dict__.keys())}")
        
        # 트랙 정보 확인
        if hasattr(tracker_state, 'tracks') and tracker_state.tracks:
            print(f"\n🛤️ 트랙 정보:")
            print(f"  - 총 트랙 수: {len(tracker_state.tracks)}")
            
            first_track_id = list(tracker_state.tracks.keys())[0]
            first_track = tracker_state.tracks[first_track_id]
            print(f"  - 첫 번째 트랙 ({first_track_id}): {type(first_track)}")
            if hasattr(first_track, '__dict__'):
                print(f"  - 트랙 속성들: {list(first_track.__dict__.keys())}")
        
        return tracker_state
        
    except Exception as e:
        print(f"❌ 에러: {e}")
        return None

# 최신 결과 파일 찾기
outputs_dir = Path("outputs/sn-gamestate")
latest_dirs = sorted(outputs_dir.glob("*/*/states/sn-gamestate.pklz"))

if latest_dirs:
    latest_file = latest_dirs[-1]
    print(f"🔍 최신 결과 파일: {latest_file}")
    tracker_state = inspect_tracker_state(latest_file)
else:
    print("❌ 결과 파일을 찾을 수 없습니다.")