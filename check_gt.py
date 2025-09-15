#!/usr/bin/env python3

import zipfile
import pickle
import pandas as pd

def analyze_ground_truth():
    """Ground Truth vs Predictions 데이터를 분석합니다."""
    
    pklz_path = "C:/Projects/pythonProjects/sn-gamestate/outputs/sn-gamestate/2025-09-15/23-16-18/states/sn-gamestate.pklz"
    
    print("🔍 Ground Truth vs Predictions 분석:")
    
    try:
        with zipfile.ZipFile(pklz_path, 'r') as zf:
            file_list = zf.namelist()
            print(f"📁 파일들: {file_list}")
            
            # 메인 데이터 (Predictions)
            with zf.open('021.pkl') as f:
                pred_df = pickle.load(f)
            
            # 이미지 관련 데이터 확인 (Ground Truth 포함 가능성)
            with zf.open('021_image.pkl') as f:
                image_data = pickle.load(f)
            
        print(f"📊 Predictions 데이터: {pred_df.shape}")
        print(f"📊 Image 데이터 타입: {type(image_data)}")
        
        if isinstance(image_data, pd.DataFrame):
            print(f"📊 Image 데이터 크기: {image_data.shape}")
            print(f"📋 Image 데이터 컬럼: {list(image_data.columns)}")
            
            # Ground Truth 분석
            if 'jersey_number' in image_data.columns:
                gt_jersey_valid = image_data['jersey_number'].notna().sum()
                print(f"🎯 GT 저지 번호 유효: {gt_jersey_valid}/{len(image_data)}")
                
                if gt_jersey_valid > 0:
                    gt_jersey_samples = image_data[image_data['jersey_number'].notna()]['jersey_number'].unique()[:10]
                    print(f"🎯 GT 저지 번호 샘플: {gt_jersey_samples}")
            
            if 'team' in image_data.columns:
                gt_team_counts = image_data['team'].value_counts()
                print(f"🎯 GT 팀 분포: {dict(gt_team_counts)}")
                
            if 'role' in image_data.columns:
                gt_role_counts = image_data['role'].value_counts()
                print(f"🎯 GT 역할 분포: {dict(gt_role_counts)}")
                
            # 샘플 비교
            print(f"\n📄 GT 첫 3개 행:")
            sample_cols = [col for col in ['track_id', 'team', 'role', 'jersey_number'] if col in image_data.columns]
            if sample_cols:
                print(image_data[sample_cols].head(3))
        
        print(f"\n� 첫 5개 행 상세:")
        sample_cols = ['track_id', 'team', 'role', 'bbox_pitch', 'jersey_number']
        print(df[sample_cols].head(5))
        
        # bbox_pitch 상세 확인
        bbox_pitch_sample = df['bbox_pitch'].head(5)
        print(f"\nbbox_pitch 샘플:")
        for i, bbox in enumerate(bbox_pitch_sample):
            print(f"  {i}: {type(bbox)} = {bbox}")
        
        # 각 컬럼별 통계
        print(f"\n📊 컬럼별 통계:")
        for col in ['team', 'role', 'jersey_number', 'bbox_pitch']:
            if col in df.columns:
                valid_count = df[col].notna().sum()
                unique_count = len(df[col].unique())
                print(f"{col}: {valid_count}/{len(df)} 유효, {unique_count}개 유니크값")
                if valid_count > 0:
                    unique_vals = df[col].dropna().unique()[:5]
                    print(f"  샘플값: {unique_vals}")
                    
        print(f"\n�🔄 비교 요약:")
        print(f"Predictions 저지번호: {pred_df['jersey_number'].notna().sum()}")
        if isinstance(image_data, pd.DataFrame) and 'jersey_number' in image_data.columns:
            print(f"Ground Truth 저지번호: {image_data['jersey_number'].notna().sum()}")
        else:
            print("Ground Truth: Image 데이터에 저지번호 없음")
            
    except Exception as e:
        print(f"❌ 에러: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_ground_truth()