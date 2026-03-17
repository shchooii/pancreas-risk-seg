# 3D Slicer 클라이언트 설치 가이드 (Windows)

PACS 서버 연동을 위한 3D Slicer 설정

> 서버 배포는 [SERVER_GUIDE.md](SERVER_GUIDE.md)를 참고하세요.

---

## 구성도

```
┌─ 서버 (WSL2 / Linux / Windows) ─────────────────────────────────┐
│                                                                   │
│  ┌──────────────┐      ┌────────────────────┐                   │
│  │   Orthanc    │      │   NNInteractive    │                   │
│  │ :8042 :4242  │      │     :1527          │                   │
│  └──────┬───────┘      └──────────┬─────────┘                   │
│         │                          │                             │
└─────────┼──────────────────────────┼─────────────────────────────┘
          │                          │
          │ :8042/dicom-web          │ :1527
          │                          │
┌─────────┴──────────────────────────┴──────┐
│          3D Slicer (Windows)              │
│                                            │
│  DICOMweb Browser ←→ Orthanc (영상 조회)   │
│  NNInteractive    ←→ AI 서버 (세그멘테이션) │
└────────────────────────────────────────────┘
```

---

## 사전 요구사항

- **3D Slicer 5.x 이상** (`install/Slicer-5.10.0-win-amd64.exe` 포함)
- **인터넷 연결** (확장 프로그램 자동 설치용)
- PACS 서버 접속 정보 (URL, ID, Password)

---

## 설치 파일

```
install/
├── Slicer-5.10.0-win-amd64.exe  # 3D Slicer 설치 파일
├── setup.bat            # 자동 설치 스크립트 (더블클릭 실행)
├── .slicerrc.py         # Slicer 시작 시 자동 실행되는 설정 스크립트
├── DICOMwebBrowser.py   # PACS 연동용 커스텀 DICOMweb 브라우저 모듈
└── config.ini           # PACS 서버 인증 정보
```

---

## 설치 순서

### 1단계: 3D Slicer 설치

`Slicer-5.10.0-win-amd64.exe`를 실행하여 설치합니다.

### 2단계: PACS 서버 정보 설정

`config.ini` 파일을 편집하여 접속할 PACS 서버 정보를 입력합니다.

```ini
# 섹션명 = 서버 호스트명 (URL의 도메인/IP 부분, 포트 제외)

# 운영 서버 (도메인)
[pacs.ziovision.ai]
user = bsnuh
password = bsnuh!23

# WSL2 / Windows Docker Desktop (같은 PC)
[localhost]
user = bsnuh
password = bsnuh!23

# 원격 Linux 서버 (IP 직접 접속)
[192.168.0.100]
user = bsnuh
password = bsnuh!23
```

**섹션명 규칙** — Slicer에 입력할 URL에서 **호스트명만** 사용합니다. 포트는 포함하지 않습니다.

| Slicer URL 입력값 | config.ini 섹션명 |
|---|---|
| `https://pacs.ziovision.ai/dicom-web` | `[pacs.ziovision.ai]` |
| `http://localhost:8042/dicom-web` | `[localhost]` |
| `http://192.168.0.100:8042/dicom-web` | `[192.168.0.100]` |

### 3단계: setup.bat 실행

`setup.bat`를 **더블클릭**하여 실행합니다.

수행 작업:
- `.slicerrc.py` → 사용자 홈 폴더(`%USERPROFILE%`)로 복사
- `config.ini` → 사용자 홈 폴더로 복사
- `DICOMwebBrowser.py` → 사용자 홈 폴더로 복사

### 4단계: 3D Slicer 실행 (첫 실행)

Slicer를 실행하면 `.slicerrc.py`가 자동으로 동작합니다.

**첫 실행 시 (자동 처리):**
1. 필수 확장 프로그램 설치: `DICOMwebBrowser`, `NNInteractive`, `QuantitativeReporting`
2. 설치 완료 후 Slicer **자동 재시작**

**재시작 후 (자동 처리):**
1. 커스텀 `DICOMwebBrowser.py`를 확장 모듈 경로에 덮어쓰기
2. `config.ini`를 모듈 폴더로 복사
3. 설정된 서버 목록 검증 및 로그 출력

### 5단계: PACS 서버 접속

1. Slicer 메뉴에서 **Modules > Informatics > DICOMweb Browser** 선택
2. Server URL 입력: 예시

| 서버 위치 | 입력할 URL |
|---|---|
| WSL2 / Docker Desktop (같은 PC) | `http://localhost:8042/dicom-web` |
| 원격 서버 (Linux/Windows) | `http://서버IP:8042/dicom-web` |
| 운영 도메인 | `https://pacs.ziovision.ai/dicom-web` |

3. **Connect** 클릭
4. `config.ini`에 해당 호스트의 인증정보가 있으면 **자동으로 인증** 처리됨

---

## 서버 추가/변경

### 방법 1: Slicer 모듈 폴더의 config.ini 직접 편집 (권장)

모듈 폴더 위치 확인 (Slicer Python 콘솔에서):
```python
import slicer
print(slicer.modules.dicomwebbrowser.path)
```

해당 경로의 폴더에 있는 `config.ini`에 서버 섹션 추가.
**Slicer 재시작 없이** 다음 Connect 시 바로 적용됩니다.

### 방법 2: setup.bat 재실행

1. `install/config.ini` 수정
2. `setup.bat` 재실행
3. Slicer 재시작

---

## 인증 흐름

```
사용자가 Server URL 입력 후 Connect 클릭
        │
        ▼
URL에서 hostname 추출
  http://192.168.0.100:8042/dicom-web → 192.168.0.100
  http://localhost:8042/dicom-web     → localhost
  https://pacs.ziovision.ai/dicom-web → pacs.ziovision.ai
        │
        ▼
config.ini에서 [hostname] 섹션 검색
        │
        ├─ 매칭됨 → user/password로 HTTPBasicAuth 자동 설정
        │
        └─ 없음   → 인증 없이 접속 시도
                    (googleapis.com → Google OAuth 토큰)
                    (kheops → URL 토큰 기반 인증)
```



## 문제 해결

### 확장 프로그램 설치 실패
- 인터넷 연결 확인
- Slicer 버전 확인 (5.x 이상 권장)
- Slicer를 **관리자 권한**으로 실행

### DICOMwebBrowser 모듈이 로드되지 않았습니다
- 첫 실행 후 Slicer 재시작 필요 (자동 재시작되지 않았을 경우 수동 재시작)

### PACS 서버 접속 실패
- Server URL 형식 확인: **`http://호스트:8042/dicom-web`** (Orthanc 기본 경로)
- `config.ini`의 섹션명이 URL의 호스트명과 **정확히 일치**하는지 확인 (포트 제외)
- 서버 동작 확인: 브라우저에서 `http://서버주소:8042` 접속 시 Orthanc 웹 UI가 뜨는지 확인
- 네트워크/방화벽에서 8042, 1527 포트 확인

### localhost 접속은 되는데 IP 접속이 안 될 때
- 서버측 방화벽에서 8042, 1527 포트 인바운드 허용 확인
- 같은 네트워크 대역인지 확인

### config.ini 위치 확인

Slicer Python 콘솔에서:
```python
import os, slicer
module_dir = os.path.dirname(slicer.modules.dicomwebbrowser.path)
config_path = os.path.join(module_dir, 'config.ini')
print(f"config.ini 경로: {config_path}")
print(f"파일 존재: {os.path.exists(config_path)}")
```

### 현재 등록된 서버 목록 확인

Slicer Python 콘솔에서:
```python
import configparser, os, slicer
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(slicer.modules.dicomwebbrowser.path), 'config.ini')
config.read(config_path)
for section in config.sections():
    print(f"  서버: {section}, ID: {config.get(section, 'user')}")
```
