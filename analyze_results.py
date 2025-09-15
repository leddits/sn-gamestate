#!/usr/bin/env python3

import zipfile
import pickle
import pandas as pd

def analyze_latest_results():
    """최신 실행 결과를 분석하여 calibration 문제를 찾습니다."""
    
    # 최신 결과 파일 경로
    pklz_path = r"C:\Projects\pythonProjects\sn-gamestate\outputs\sn-gamestate\2025-09-15\22-10-55\states\sn-gamestate.pklz"
    
    print("🔍 최신 결과 분석 중...")
    
    try:
        with zipfile.ZipFile(pklz_path, 'r') as zf:
            with zf.open('021.pkl') as f:
                df = pickle.load(f)
        
        print(f"📊 데이터 크기: {df.shape}")
        
        # 핵심 컬럼들 분석
        print("\n📋 핵심 데이터 분석:")
        
        # bbox_pitch 분석
        bbox_pitch_valid = df['bbox_pitch'].notna().sum()
        print(f"bbox_pitch 유효 데이터: {bbox_pitch_valid}/{len(df)}")
        
        # 몇 개의 bbox_pitch 값 확인
        if bbox_pitch_valid > 0:
            valid_bbox_pitch = df[df['bbox_pitch'].notna()]['bbox_pitch'].iloc[:3]
            print(f"bbox_pitch 샘플: {list(valid_bbox_pitch)}")
        else:
            print("❌ bbox_pitch가 모두 NaN입니다!")
            
        # 팀 분류 분석
        team_counts = df['team'].value_counts()
        print(f"팀 분포: {dict(team_counts)}")
        
        # 역할 분석  
        role_counts = df['role'].value_counts()
        print(f"역할 분포: {dict(role_counts)}")
        
        # 저지 번호 분석
        jersey_valid = df['jersey_number'].notna().sum()
        print(f"저지 번호 유효 데이터: {jersey_valid}/{len(df)}")
        
        # 샘플 데이터로 문제 확인
        print(f"\n📄 첫 3개 행 샘플:")
        sample_cols = ['track_id', 'team', 'role', 'bbox_pitch', 'jersey_number']
        print(df[sample_cols].head(3))
        
        # Ground Truth와 비교를 위해 이미지 데이터도 확인
        try:
            with zipfile.ZipFile(pklz_path, 'r') as zf:
                with zf.open('021_image.pkl') as f:
                    image_data = pickle.load(f)
            
            print(f"\n🖼️ 이미지 데이터 타입: {type(image_data)}")
            if isinstance(image_data, dict):
                print(f"이미지 데이터 키들: {list(image_data.keys())}")
                
        except Exception as e:
            print(f"이미지 데이터 로딩 실패: {e}")
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_latest_results()