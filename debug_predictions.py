#!/usr/bin/env python3

import pickle
import zipfile

def analyze_tracker_state(pklz_path):
    """TrackLab 상태 파일을 분석하여 Predictions 레이더가 비어있는 이유를 찾습니다."""
    
    print(f"분석 중: {pklz_path}")
    
    try:
        # .pklz 파일은 실제로는 zip 파일입니다
        with zipfile.ZipFile(pklz_path, 'r') as zf:
            # zip 내부 파일 목록 확인
            file_list = zf.namelist()
            print(f"zip 내부 파일들: {file_list}")
            
            # .pkl 파일을 찾아서 읽기
            pkl_file = None
            for filename in file_list:
                if filename.endswith('.pkl') and not filename.endswith('_image.pkl'):
                    pkl_file = filename
                    break
            
            if pkl_file:
                print(f"로딩할 파일: {pkl_file}")
                with zf.open(pkl_file) as f:
                    tracker_state = pickle.load(f)
            else:
                print("❌ .pkl 파일을 찾을 수 없습니다")
        
        print(f"✅ 상태 파일 로딩 완료")
        print(f"📊 타입: {type(tracker_state)}")
        
        # DataFrame인 경우
        if hasattr(tracker_state, 'columns'):
            print(f"🔍 DataFrame 크기: {tracker_state.shape}")
            print(f"� 컬럼들: {list(tracker_state.columns)}")
            
            # 핵심 컬럼들 확인
            key_columns = ['bbox_pitch', 'team', 'track_id', 'role']
            for col in key_columns:
                if col in tracker_state.columns:
                    unique_values = tracker_state[col].unique()
                    non_null_count = tracker_state[col].notna().sum()
                    print(f"{col}: {non_null_count}/{len(tracker_state)} 개 값, 유니크: {len(unique_values)}")
                    if col == 'bbox_pitch':
                        # bbox_pitch가 비어있는지 확인
                        has_pitch_coords = tracker_state[col].notna().sum()
                        print(f"  -> 피치 좌표 있는 감지: {has_pitch_coords}")
                    elif col == 'team':
                        # 팀 분류 상태 확인  
                        team_counts = tracker_state[col].value_counts()
                        print(f"  -> 팀 분포: {dict(team_counts)}")
            
            # 샘플 데이터 출력
            print(f"\n📄 첫 5개 행:")
            sample_cols = ['track_id', 'team', 'role', 'bbox_pitch'] 
            available_cols = [col for col in sample_cols if col in tracker_state.columns]
            print(tracker_state[available_cols].head())
            
        else:
            print("❌ DataFrame이 아닙니다")
            print(f"사용 가능한 속성들: {dir(tracker_state)}")
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 최신 상태 파일 분석
    pklz_path = r"C:\Projects\pythonProjects\sn-gamestate\outputs\sn-gamestate\2025-09-15\22-10-55\states\sn-gamestate.pklz"
    analyze_tracker_state(pklz_path)