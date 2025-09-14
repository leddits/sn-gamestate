#!/bin/bash

# AGX Orin GPU 최적화 #!/bin/bash

# AGX Orin GPU 최적화 설치 스크립트
# JetPack 6.2.1 (L4T 36.4.4) 기준
# Python 3.10 가상환경 생성 및 NVIDIA PyTorch GPU 버전 설치

set -e  # 오류 발생 시 스크립트 중단

echo "🚀 AGX Orin GPU 최적화 환경 설정을 시작합니다..."
echo "📋 대상 환경: JetPack 6.2.1 (L4T 36.4.4), Python 3.10"

# 시스템 정보 확인
echo "🔍 시스템 정보 확인..."
jetson_release || echo "⚠️  jetson_release를 실행할 수 없습니다."
echo ""

# Python 3.10 설치 확인
if ! command -v python3.10 &> /dev/null; then
    echo "❌ Python 3.10이 설치되지 않았습니다."
    echo "다음 명령으로 설치하세요: sudo apt update && sudo apt install python3.10 python3.10-venv"
    exit 1
fi

echo "✅ Python 3.10 설치 확인: $(python3.10 --version)"

# 기존 가상환경이 있다면 제거
if [ -d ".venv" ]; then
    echo "🗑️  기존 .venv 폴더가 발견되었습니다. 제거 후 새로 생성합니다."
    rm -rf .venv
fi

# Python 3.10 가상환경 생성
echo "📦 Python 3.10 가상환경 생성 중..."
uv venv --python 3.10

# 가상환경 활성화
echo "🔧 가상환경 활성화 중..."
source .venv/bin/activate

echo "✅ 가상환경 활성화 완료: $VIRTUAL_ENV"
echo "🐍 Python 버전: $(python --version)"

# CUDA 환경 변수 설정
echo "🔧 CUDA 환경 변수 설정..."
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# GPU 및 CUDA 정보 확인
echo "🔍 GPU 및 CUDA 정보 확인..."
nvidia-smi || echo "⚠️  nvidia-smi를 실행할 수 없습니다."
echo "CUDA 정보:"
vncc --version || echo "⚠️  nvcc를 실행할 수 없습니다."
echo ""

# pip 설치 (uv 가상환경에는 기본으로 없음)
echo "🔧 pip 설치 중..."
uv pip install pip

# cusparselt 설치 (PyTorch 24.06+ 버전에 필요)
echo "🔧 cusparselt 설치 중..."
if [ ! -f "./install_cusparselt.sh" ]; then
    wget https://raw.githubusercontent.com/pytorch/pytorch/5c6af2b583709f6176898c017424dc9981023c28/.ci/docker/common/install_cusparselt.sh
fi
export CUDA_VERSION=12.6
bash ./install_cusparselt.sh || echo "⚠️  cusparselt 설치 실패 (선택사항)"

# NVIDIA PyTorch 설치
echo "🔥 NVIDIA 공식 PyTorch for Jetson 설치 중..."
echo "📋 설치 대상: PyTorch 2.5.0a0+872d972e41 (JetPack 6.1+용, Python 3.10)"

export TORCH_INSTALL=https://developer.download.nvidia.com/compute/redist/jp/v61/pytorch/torch-2.5.0a0+872d972e41.nv24.08.17622132-cp310-cp310-linux_aarch64.whl

python3 -m pip install --no-cache $TORCH_INSTALL

# PyTorch 설치 검증
echo "🧪 PyTorch GPU 기능 검증 중..."
python -c "
import torch
cuda_available = torch.cuda.is_available()
print(f'PyTorch 버전: {torch.__version__}')
print(f'CUDA 사용 가능: {cuda_available}')
if cuda_available:
    print(f'CUDA 버전: {torch.version.cuda}')
    print(f'cuDNN 버전: {torch.backends.cudnn.version()}')
    print(f'CUDA 장치 수: {torch.cuda.device_count()}')
    print(f'장치 이름: {torch.cuda.get_device_name(0)}')
    print('✅ GPU 지원 PyTorch 설치 성공!')
else:
    print('❌ GPU 지원이 활성화되지 않음')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ PyTorch GPU 설치에 실패했습니다."
    exit 1
fi

echo "✅ NVIDIA PyTorch 설치 및 검증 완료!"

# 호환되는 torchvision 설치
echo "🔧 호환되는 torchvision 설치 중..."
python3 -m pip install torchvision==0.20.0 --no-deps

# 다른 필수 패키지들 설치
echo "📚 필수 패키지 설치 중..."
uv pip install numpy==1.26.4

# 프로젝트 의존성 설치 (torch 제외)
echo "📦 프로젝트 의존성 설치 중..."

# 개별 패키지 설치로 torch 덮어쓰기 방지
uv pip install tracklab
uv pip install easyocr==1.7.1  
uv pip install soccernet==0.1.55
uv pip install mmocr==1.0.1
uv pip install "mmdet~=3.1.0"
uv pip install openmim==0.3.9
uv pip install lightning==2.0.9

# Git 기반 패키지들
echo "🔗 Git 기반 패키지 설치 중..."
uv pip install "git+https://github.com/VlSomers/prtreid"
uv pip install "git+https://github.com/VlSomers/bpbreid"

# calibration 플러그인 설치
echo "🔧 Calibration 플러그인 설치 중..."
uv pip install -e ./plugins/calibration

# MMCV 설치 시도
echo "🔧 MMCV 설치 시도 중..."
python -m mim install "mmcv==2.0.1" || {
    echo "⚠️  MMCV 설치 실패. 수동으로 설치가 필요할 수 있습니다."
}

# 프로젝트 자체를 editable 모드로 설치 (torch 덮어쓰기 방지를 위해 --no-deps 사용)
echo "📦 프로젝트를 editable 모드로 설치 중..."
pip install -e . --no-deps

echo "🧪 최종 설치 검증 중..."

# 최종 검증
python -c "
import torch
print('=' * 60)
print('🔍 AGX Orin JetPack 6.2.1 설치 검증 결과')
print('=' * 60)
print(f'PyTorch 버전: {torch.__version__}')
print(f'CUDA 사용 가능: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA 버전: {torch.version.cuda}')
    print(f'cuDNN 버전: {torch.backends.cudnn.version()}')
    print(f'CUDA 장치 수: {torch.cuda.device_count()}')
    print(f'장치 이름: {torch.cuda.get_device_name(0)}')
    
    # GPU 메모리 테스트
    x = torch.randn(1000, 1000).cuda()
    y = torch.randn(1000, 1000).cuda()
    z = torch.matmul(x, y)
    print(f'GPU 연산 테스트: {z.shape} - ✅ 성공')
    print('🎉 GPU 가속 준비 완료!')
else:
    print('❌ GPU 지원이 활성화되지 않음')
print('=' * 60)

try:
    import tracklab, easyocr, soccernet
    print('✅ 주요 라이브러리 import 성공')
except ImportError as e:
    print(f'❌ Import 오류: {e}')

try:
    import torchvision
    print(f'✅ torchvision 버전: {torchvision.__version__}')
except ImportError as e:
    print(f'❌ torchvision import 오류: {e}')


echo ""
echo "🎉 AGX Orin JetPack 6.2.1 환경 설정이 완료되었습니다!"
echo ""
echo "📝 사용법:"
echo "   1. 가상환경 활성화: source .venv/bin/activate"
echo "   2. GPU 상태 확인: nvidia-smi"
echo "   3. PyTorch GPU 테스트: python -c \"import torch; print(torch.cuda.is_available())\""
echo "   4. 모델 실행: python your_script.py"
echo ""
echo "🔧 추가 정보:"
echo "   - JetPack 버전: 6.2.1 (L4T 36.4.4)"
echo "   - Python 버전: 3.10"
echo "   - PyTorch 버전: 2.5.0a0+872d972e41 (NVIDIA 최적화)"
echo "   - CUDA: 12.6, cuDNN: 9.3"
echo ""# JetPack 5.x/6.x 기준
# 처음부터 가상환경 생성 및 PyTorch GPU 버전 설치

set -e  # 오류 발생 시 스크립트 중단

echo "🚀 AGX Orin GPU 최적화 환경 설정을 시작합니다..."

# 기존 가상환경이 있다면 제거
if [ -d ".venv" ]; then
    echo "기존 .venv 폴더가 발견되었습니다. 제거 후 새로 생성합니다."
    rm -rf .venv
fi

# Python 3.9 가상환경 생성
echo "📦 Python 3.9 가상환경 생성 중..."
uv venv --python 3.9

# 가상환경 활성화
echo "🔧 가상환경 활성화 중..."
source .venv/bin/activate

echo "✅ 가상환경 활성화 완료: $VIRTUAL_ENV"

# CUDA 환경 변수 설정
echo "🔧 CUDA 환경 변수 설정..."
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# 시스템 정보 확인
echo "� 시스템 정보 확인..."
echo "GPU 정보:"
nvidia-smi || echo "⚠️  nvidia-smi를 실행할 수 없습니다."

echo "CUDA 정보:"
nvcc --version || echo "⚠️  nvcc를 실행할 수 없습니다."

# PyTorch 설치 - 여러 방법 시도
echo "🔥 AGX Orin용 PyTorch 설치 시도 중..."

# 방법 1: CUDA 12.1 호환 버전
echo "방법 1: CUDA 12.1 호환 PyTorch 시도..."
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 설치 검증
python -c "
import torch
cuda_available = torch.cuda.is_available()
print(f'PyTorch 버전: {torch.__version__}')
print(f'CUDA 사용 가능: {cuda_available}')
if cuda_available:
    print(f'CUDA 버전: {torch.version.cuda}')
    print('✅ GPU 지원 PyTorch 설치 성공!')
    exit(0)
else:
    print('❌ GPU 지원이 활성화되지 않음')
    exit(1)
" || {
    echo "방법 1 실패. 방법 2 시도 중..."
    
    # 방법 2: CPU 버전으로 설치 후 경고
    uv pip install torch torchvision torchaudio --force-reinstall
    echo "⚠️  CPU 버전 PyTorch가 설치되었습니다."
    echo "🔧 GPU 지원을 위해서는 다음 중 하나를 시도하세요:"
    echo "   1. NVIDIA Container: sudo docker pull nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3"
    echo "   2. JetPack SDK Manager로 완전 설치"
    echo "   3. PyTorch 소스에서 빌드"
}

echo "📚 프로젝트 의존성 설치 중..."

# 필수 패키지 설치
uv pip install easyocr==1.7.1
uv pip install soccernet==0.1.55
uv pip install mmocr==1.0.1
uv pip install "mmdet~=3.1.0"
uv pip install openmim==0.3.9
uv pip install lightning==2.0.9
uv pip install "numpy<2.0"

# Git 기반 패키지들
echo "🔗 Git 기반 패키지 설치 중..."
uv pip install "git+https://github.com/VlSomers/prtreid"
uv pip install "git+https://github.com/VlSomers/bpbreid"

# 기타 패키지
uv pip install tracklab

# 프로젝트 자체를 editable 모드로 설치
echo "📦 프로젝트를 editable 모드로 설치 중..."
uv pip install -e .

# MMCV 설치 시도
echo "🔧 MMCV 설치 시도 중..."
python -m mim install "mmcv==2.0.1" || {
    echo "⚠️  MMCV 설치 실패. 수동으로 설치가 필요할 수 있습니다."
}

echo "🧪 최종 설치 검증 중..."

# 최종 검증
python -c "
import torch
print('=' * 50)
print('🔍 AGX Orin 설치 검증 결과')
print('=' * 50)
print(f'PyTorch 버전: {torch.__version__}')
print(f'CUDA 사용 가능: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA 버전: {torch.version.cuda}')
    print(f'CUDA 장치 수: {torch.cuda.device_count()}')
    print(f'장치 이름: {torch.cuda.get_device_name(0)}')
    print('🎉 GPU 가속 준비 완료!')
else:
    print('⚠️  현재 CPU 모드로 실행됩니다.')
    print('GPU 최적화를 위한 추가 설정이 필요합니다.')
print('=' * 50)

try:
    import tracklab, easyocr, soccernet
    print('✅ 주요 라이브러리 import 성공')
except ImportError as e:
    print(f'❌ Import 오류: {e}')
"

echo ""
echo "🎉 AGX Orin 환경 설정이 완료되었습니다!"
echo ""
echo "📝 사용법:"
echo "   1. 가상환경 활성화: source .venv/bin/activate"
echo "   2. GPU 상태 확인: nvidia-smi"
echo "   3. PyTorch GPU 테스트: python -c \"import torch; print(torch.cuda.is_available())\""
echo ""
if ! python -c "import torch; exit(0 if torch.cuda.is_available() else 1)" 2>/dev/null; then
    echo "� GPU 최적화 추가 옵션:"
    echo "   - NVIDIA Container 사용 권장"
    echo "   - JetPack 완전 설치 확인"
    echo "   - PyTorch 소스 빌드 고려"
fi
