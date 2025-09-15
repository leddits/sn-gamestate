#!/usr/bin/env python3

import zipfile
import pickle
import pandas as pd

def compare_results():
    """여러 실행 결과를 비교하여 차이점을 찾습니다."""
    
    results = [
        "22-10-55",  # 최신
        "18-46-57",  # 이전
    ]
    
    for result_dir in results:
        pklz_path = f"C:/Projects/pythonProjects/sn-gamestate/outputs/sn-gamestate/2025-09-15/{result_dir}/states/sn-gamestate.pklz"
        
        print(f"\n🔍 {result_dir} 결과 분석:")
        
        try:
            with zipfile.ZipFile(pklz_path, 'r') as zf:
                with zf.open('021.pkl') as f:
                    df = pickle.load(f)
            
            print(f"📊 데이터 크기: {df.shape}")
            
            # bbox_pitch 분석
            bbox_pitch_valid = df['bbox_pitch'].notna().sum()
            print(f"bbox_pitch 유효: {bbox_pitch_valid}/{len(df)}")
            
            # 팀 분류 분석
            team_counts = df['team'].value_counts()
            print(f"팀 분포: {dict(team_counts)}")
            
            # 역할 분석  
            role_counts = df['role'].value_counts()
            print(f"역할 분포: {dict(role_counts)}")
            
            # 저지 번호 분석
            jersey_valid = df['jersey_number'].notna().sum()
            print(f"저지 번호 유효: {jersey_valid}/{len(df)}")
            
            if jersey_valid > 0:
                jersey_samples = df[df['jersey_number'].notna()]['jersey_number'].unique()[:5]
                print(f"저지 번호 샘플: {jersey_samples}")
                
            # Ground Truth와 다른 점 확인
            if bbox_pitch_valid == 0:
                print("❌ Predictions 레이더가 비어있을 것임")
            else:
                print("✅ Predictions 레이더에 데이터 있음")
                
        except Exception as e:
            print(f"❌ 에러: {e}")

if __name__ == "__main__":
    compare_results()