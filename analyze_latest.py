#!/usr/bin/env python3

import zipfile
import pickle
import pandas as pd

def analyze_latest_results():
    """최신 결과를 상세 분석합니다."""
    
    pklz_path = "C:/Projects/pythonProjects/sn-gamestate/outputs/sn-gamestate/2025-09-15/23-16-18/states/sn-gamestate.pklz"
    
    print("🔍 최신 결과 상세 분석:")
    
    try:
        with zipfile.ZipFile(pklz_path, 'r') as zf:
            file_list = zf.namelist()
            print(f"📁 파일들: {file_list}")
            
            # 메인 데이터 (Predictions)
            with zf.open('021.pkl') as f:
                pred_df = pickle.load(f)
            
        print(f"📊 Predictions 데이터: {pred_df.shape}")
        
        # 첫 5개 행 상세 분석
        print(f"\n📄 첫 5개 행:")
        sample_cols = ['track_id', 'team', 'role', 'bbox_pitch', 'jersey_number']
        print(pred_df[sample_cols].head(5))
        
        # bbox_pitch 상세 확인
        print(f"\n🔍 bbox_pitch 샘플:")
        bbox_pitch_sample = pred_df['bbox_pitch'].head(5)
        for i, bbox in enumerate(bbox_pitch_sample):
            print(f"  [{i}] {type(bbox)}: {bbox}")
        
        # 각 컬럼별 통계
        print(f"\n📊 컬럼별 통계:")
        for col in ['team', 'role', 'jersey_number', 'bbox_pitch']:
            if col in pred_df.columns:
                valid_count = pred_df[col].notna().sum()
                total_count = len(pred_df)
                unique_count = len(pred_df[col].unique())
                print(f"{col}: {valid_count}/{total_count} 유효 ({valid_count/total_count*100:.1f}%), {unique_count}개 유니크")
                
                if valid_count > 0:
                    unique_vals = pred_df[col].dropna().unique()[:5]
                    print(f"  → 샘플값: {unique_vals}")
                else:
                    print(f"  → ❌ 모든 값이 NaN")
        
        # 결론
        print(f"\n🎯 결론:")
        bbox_valid = pred_df['bbox_pitch'].notna().sum()
        jersey_valid = pred_df['jersey_number'].notna().sum()
        
        if bbox_valid > 0:
            print(f"✅ Calibration 성공: {bbox_valid}/{len(pred_df)} 피치 좌표 변환")
        else:
            print(f"❌ Calibration 실패: 모든 피치 좌표가 NaN")
            
        if jersey_valid > 0:
            print(f"✅ 저지번호 인식 성공: {jersey_valid}/{len(pred_df)}")
        else:
            print(f"❌ 저지번호 인식 실패: 모든 저지번호가 NaN")
            
    except Exception as e:
        print(f"❌ 에러: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_latest_results()