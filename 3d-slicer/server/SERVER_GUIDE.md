# PACS 서버 설치/운영 가이드

Orthanc PACS + NNInteractive AI 서버 배포 및 운영 (WSL2 / Linux / Windows)

---

## 구성도

```
┌─ 서버 (WSL2 / Linux / Windows) ─────────────────────────────────┐
│                                                                   │
│  ┌──────────┐   ┌──────────────┐      ┌────────────────────┐    │
│  │PostgreSQL│◄──│   Orthanc    │      │   NNInteractive    │    │
│  │ :5432    │   │  PACS 서버   │      │   AI 서버 (GPU)    │    │
│  │ (내부)    │   │ :8042 :4242  │      │     :1527          │    │
│  └──────────┘   └──────┬───────┘      └──────────┬─────────┘    │
│                        │                          │              │
└────────────────────────┼──────────────────────────┼──────────────┘
                         │                          │
          DICOMweb (REST API)          AI 추론 요청/결과 (HTTP)
            :8042/dicom-web                  :1527
                         │                          │
              ┌──────────┴──────────────────────────┴──────┐
              │          3D Slicer (Windows 클라이언트)      │
              │                                            │
              │  DICOMweb Browser ←→ Orthanc (영상 조회)   │
              │  NNInteractive    ←→ AI 서버 (세그멘테이션) │
              └────────────────────────────────────────────┘
```

### 서비스 포트 요약

| 서비스 | 포트 | 프로토콜 | 용도 |
|---|---|---|---|
| Orthanc | **8042** | HTTP | 웹 UI + REST API + **DICOMweb** |
| Orthanc | 4242 | DICOM | C-STORE, C-FIND (전통 DICOM) |
| NNInteractive | 1527 | HTTP | AI 세그멘테이션 서버 |
| PostgreSQL | 5432 | TCP | 내부 전용 (외부 노출 안 됨) |

### 배포 옵션

| 옵션 | 클라이언트 접속 URL | 적합한 상황 |
|---|---|---|
| **WSL2** (같은 PC) | `http://localhost:8042/dicom-web` | 개발/테스트, 1인 사용 |
| **Linux** (원격 서버) | `http://서버IP:8042/dicom-web` | 운영 환경, 다수 사용자 |
| **Windows** (Docker Desktop) | `http://localhost:8042/dicom-web` 또는 `http://서버IP:8042/dicom-web` | GPU 워크스테이션 활용 |

---

## 서버 배포

### 사전 요구사항

| 항목 | WSL2 | Linux | Windows |
|---|---|---|---|
| OS | Windows 10 21H2+ / 11 | Ubuntu 20.04+ 등 | Windows 10/11 |
| Docker | Docker Desktop (WSL2 backend) | Docker Engine + Compose | Docker Desktop |
| GPU | Windows NVIDIA 드라이버 | NVIDIA 드라이버 + nvidia-container-toolkit | Windows NVIDIA 드라이버 |
| 비고 | WSL 내부에 별도 GPU 드라이버 불필요 | 서버 전용 권장 | Docker Desktop이 WSL2 backend 사용 |

GPU 확인:
```bash
# WSL2 / Linux
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```
```powershell
# Windows (PowerShell)
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### 1단계: 저장 경로 설정

`anno-docker-compose.yml`에서 `[수정 필요]` 표시된 볼륨 경로를 변경합니다.

#### WSL2

> **주의: PostgreSQL + NTFS 권한 문제**
>
> PostgreSQL은 첫 초기화(`initdb`) 시 데이터 디렉토리에 `chmod 700`을 실행합니다.
> WSL2에서 `/mnt/c/`, `/mnt/d/` 등 Windows 드라이브 경로(NTFS)를 사용하면 기본적으로 chmod가 동작하지 않아 다음 에러가 발생합니다:
> ```
> initdb: error: could not change permissions of directory: Operation not permitted
> ```
> 이미 초기화된 데이터가 있으면 문제없이 동작하지만, 새로 초기화할 때 실패합니다.

**방법 A: WSL2 내부 경로 사용 (권장)**

가장 안정적이고 I/O 성능도 좋습니다.

```yaml
# WSL2 내부 경로
- /home/user/pacs/postgres_data:/var/lib/postgresql/data
- /home/user/pacs/orthanc_dicom:/var/lib/orthanc/db
- /home/user/pacs/nn_data:/data
```

compose 파일을 WSL2 내부에 복사한 뒤 실행하면 상대경로(`./postgres_data`)도 그대로 사용 가능합니다:
```bash
mkdir -p ~/pacs
cp /mnt/d/commpany/project/cancer/install/server/anno-docker-compose.yml ~/pacs/
cd ~/pacs
docker compose -f anno-docker-compose.yml up -d
```

**방법 B: NTFS에서 chmod 활성화 (Windows 경로 유지)**

WSL2의 `/etc/wsl.conf`에 `metadata` 옵션을 추가하면 NTFS에서도 chmod가 동작합니다.

```bash
# WSL2 터미널에서
sudo tee /etc/wsl.conf > /dev/null << 'EOF'
[automount]
options = "metadata"
EOF
```

Windows PowerShell에서 WSL 재시작:
```powershell
wsl --shutdown
```

재시작 후 기존 Windows 경로(`/mnt/d/...`)를 그대로 사용할 수 있습니다:
```yaml
- /mnt/d/pacs/postgres_data:/var/lib/postgresql/data
- /mnt/d/pacs/orthanc_dicom:/var/lib/orthanc/db
- /mnt/d/pacs/nn_data:/data
```

> **참고**: metadata 옵션 적용 후에도 I/O 성능은 WSL2 내부 경로가 더 빠릅니다. 대용량 DICOM 데이터를 다루는 운영 환경에서는 방법 A를 권장합니다.

#### Linux

```yaml
- /data/pacs/postgres_data:/var/lib/postgresql/data
- /data/pacs/orthanc_dicom:/var/lib/orthanc/db
- /data/pacs/nn_data:/data
```

#### Windows (Docker Desktop)

```yaml
# Windows 경로 (슬래시 방향 주의)
- D:/pacs/postgres_data:/var/lib/postgresql/data
- D:/pacs/orthanc_dicom:/var/lib/orthanc/db
- D:/pacs/nn_data:/data
```

> Docker Desktop은 Windows 경로를 자동 마운트합니다. `D:\pacs\...` 대신 `D:/pacs/...`(슬래시)로 작성하세요.

### 2단계: 환경변수 설정

`anno-docker-compose.yml`의 `environment` 섹션에서 Orthanc의 동작을 설정합니다.

> **Docker 이미지**: `orthancteam/orthanc` — `ORTHANC__` 환경변수를 네이티브 지원합니다.
> `jodogne/orthanc` 이미지는 이 방식을 지원하지 않으므로 반드시 `orthancteam/orthanc`을 사용하세요.

#### 환경변수 → JSON 매핑 규칙

Orthanc은 JSON 설정 파일(`orthanc.json`)로 동작합니다. `orthancteam/orthanc` 이미지는 `ORTHANC__` 접두어 환경변수를 자동으로 JSON 설정에 매핑합니다.

**변환 규칙**: `ORTHANC__` 접두어 제거 → `__`(이중 밑줄)을 JSON 중첩으로 → 대문자를 CamelCase로

| 환경변수 | JSON 설정 | 설명 |
|---|---|---|
| `ORTHANC__AUTHENTICATION_ENABLED` | `{"AuthenticationEnabled": true}` | 인증 활성화 |
| `ORTHANC__REGISTERED_USERS` | `{"RegisteredUsers": {...}}` | 사용자 목록 (JSON 오브젝트) |
| `ORTHANC__DICOM_WEB__ENABLE` | `{"DicomWeb": {"Enable": true}}` | DICOMweb 플러그인 활성화 |
| `ORTHANC__DICOM_WEB__ROOT` | `{"DicomWeb": {"Root": "/dicom-web/"}}` | DICOMweb API 경로 |
| `ORTHANC__POSTGRESQL__HOST` | `{"PostgreSQL": {"Host": "postgres"}}` | PostgreSQL 호스트 |
| `ORTHANC__POSTGRESQL__ENABLE_INDEX` | `{"PostgreSQL": {"EnableIndex": true}}` | PostgreSQL 인덱스 사용 |

#### compose 파일 환경변수 전체 목록

```yaml
environment:
  # --- PostgreSQL 플러그인 ---
  ORTHANC__POSTGRESQL__HOST: postgres           # DB 컨테이너 호스트명
  ORTHANC__POSTGRESQL__PORT: "5432"             # DB 포트
  ORTHANC__POSTGRESQL__DATABASE: orthanc_db     # DB 이름
  ORTHANC__POSTGRESQL__USERNAME: orthanc        # DB 사용자
  ORTHANC__POSTGRESQL__PASSWORD: orthanc_password  # DB 비밀번호
  ORTHANC__POSTGRESQL__ENABLE_INDEX: "true"     # 인덱스를 PostgreSQL에 저장

  # --- 인증 ---
  ORTHANC__AUTHENTICATION_ENABLED: "true"       # 인증 활성화
  ORTHANC__REGISTERED_USERS: |                  # 사용자 목록 (JSON)
    {"UserID": "UserID!23"}

  # --- DICOMweb 플러그인 ---
  ORTHANC__DICOM_WEB__ENABLE: "true"            # DICOMweb 활성화
  ORTHANC__DICOM_WEB__ROOT: /dicom-web/         # API 루트 경로
  ORTHANC__DICOM_WEB__STUDIES_METADATA: Full    # Study 메타데이터 전체 반환
  ORTHANC__DICOM_WEB__SERIES_METADATA: Full     # Series 메타데이터 전체 반환
```

> **주의**: boolean과 숫자 값은 `"true"`, `"5432"`처럼 따옴표로 감싸야 합니다 (YAML에서 문자열로 전달).
> `REGISTERED_USERS`는 `|` (YAML 블록 스칼라)를 사용해 JSON 오브젝트를 멀티라인으로 전달합니다.

#### 인증 사용자 설정

```yaml
ORTHANC__AUTHENTICATION_ENABLED: "true"
ORTHANC__REGISTERED_USERS: |
  {"UserID": "UserID!23"}
```

> 이 ID/PW가 클라이언트 `config.ini`의 user/password와 일치해야 합니다.

사용자 추가 — JSON 오브젝트에 쉼표로 추가:
```yaml
ORTHANC__REGISTERED_USERS: |
  {"UserID": "UserID!23", "doctor01": "pass456"}
```

### 3단계: 서버 실행

#### WSL2

```bash
cd /mnt/d/commpany/project/cancer
docker compose -f anno-docker-compose.yml up -d
```

#### Linux

```bash
cd /path/to/cancer
docker compose -f anno-docker-compose.yml up -d
```

#### Windows (PowerShell)

```powershell
cd D:\commpany\project\cancer
docker compose -f anno-docker-compose.yml up -d
```

### 4단계: 동작 확인

```bash
# 컨테이너 상태
docker compose -f anno-docker-compose.yml ps

# Orthanc 웹 UI (브라우저)
#   같은 PC: http://localhost:8042
#   원격:    http://서버IP:8042
#   ID: UserID / PW: UserID!23

# DICOMweb 엔드포인트
curl -u UserID:UserID!23 http://localhost:8042/dicom-web/studies

# NNInteractive AI 서버
curl http://localhost:1527
```

Windows에서 curl이 없으면 브라우저에서 `http://localhost:8042` 접속으로 확인합니다.

### 서버 관리 명령어

```bash
docker compose -f anno-docker-compose.yml down         # 중지
docker compose -f anno-docker-compose.yml restart       # 전체 재시작
docker compose -f anno-docker-compose.yml restart orthanc  # Orthanc만 재시작
docker compose -f anno-docker-compose.yml logs -f orthanc  # 로그 확인
```

### 사용자 추가/변경

`anno-docker-compose.yml`에서 `ORTHANC__REGISTERED_USERS`를 수정 후 재시작:

```yaml
ORTHANC__REGISTERED_USERS: |
  {"UserID": "UserID!23", "newuser": "newpass"}
```

```bash
docker compose -f anno-docker-compose.yml restart orthanc
```

---

## 데이터 전송 (업로드)

Orthanc PACS에 DICOM 데이터를 올리는 방법입니다.

### 방법 1: Orthanc 웹 UI (소량, 간편)

1. 브라우저에서 `http://서버주소:8042` 접속 (ID/PW 입력)
2. 좌측 상단 **Upload** 클릭
3. `.dcm` 파일 또는 DICOM 폴더를 드래그 앤 드롭
4. **Start the upload** 클릭

### 방법 2: REST API (스크립트/자동화)

```bash
#우분투
# 단일 파일 업로드
curl -u UserID:UserID!23 -X POST \
  http://localhost:8042/instances \
  --data-binary @/path/to/file.dcm

# 폴더 일괄 업로드 (Linux/WSL2)
find /path/to/dicom_folder -name "*.dcm" -print0 | \
  xargs -0 -I {} curl -s -u UserID:UserID!23 -X POST \
    http://localhost:8042/instances \
    --data-binary @"{}"

# 병렬 업로드 (동시 4개)
find /path/to/dicom_folder -name "*.dcm" -print0 | \
  xargs -0 -P 4 -I {} curl -s -u UserID:UserID!23 -X POST \
    http://localhost:8042/instances \
    --data-binary @"{}"

```

Windows PowerShell:
```powershell
# 단일 파일
curl.exe -u UserID:UserID!23 -X POST `
  http://localhost:8042/instances `
  --data-binary "@D:\dicom\file.dcm"

# 폴더 일괄 업로드
Get-ChildItem -Path "D:\dicom" -Filter "*.dcm" -Recurse | ForEach-Object {
  curl.exe -s -u UserID:UserID!23 -X POST `
    http://localhost:8042/instances `
    --data-binary "@$($_.FullName)"
}
```

### 방법 3: DICOMweb STOW-RS (표준 프로토콜)

```bash
# 우분투
curl -u UserID:UserID!23 -X POST \
  http://localhost:8042/dicom-web/studies \
  -H "Content-Type: application/dicom" \
  --data-binary @/path/to/file.dcm
```

### 방법 4: DICOM C-STORE (dcmtk)

```bash
#우분투
# dcmtk 설치 (Ubuntu/Debian)
sudo apt install dcmtk

# 포트 4242 = DICOM 전용 (8042와 다름)
storescu localhost 4242 /path/to/file.dcm
storescu localhost 4242 /path/to/dicom_folder/
storescu 192.168.0.100 4242 /path/to/dicom_folder/
```



### 전송 방법 비교

| 방법 | 포트 | 적합한 상황 | OS |
|---|---|---|---|
| 웹 UI 업로드 | 8042 | 소량, 비개발자 | 전체 |
| REST API | 8042 | 스크립트 자동화, 대량 업로드 | 전체 |
| DICOMweb STOW-RS | 8042 | 표준 호환 | Linux/WSL2 |
| C-STORE (storescu) | 4242 | 기존 PACS 장비 연동 | Linux/WSL2 |

---

## 데이터 영속성과 백업

### 데이터 저장 구조

Orthanc은 데이터를 **두 곳**에 나누어 저장합니다. 복구 시 반드시 둘 다 필요합니다.

```
호스트 디스크
├── postgres_data/          ← PostgreSQL (메타데이터 인덱스)
│   └── DICOM 태그, Study/Series/Instance 관계, 검색 인덱스
│
└── orthanc_dicom/          ← Orthanc Storage (실제 영상 파일)
    └── 해시된 디렉토리 구조로 .dcm 파일 저장
```

| 저장소 | 내용 | 손실 시 영향 |
|---|---|---|
| `postgres_data` | DICOM 메타데이터, 검색 인덱스 | 영상 파일은 있지만 검색/조회 불가 |
| `orthanc_dicom` | 실제 DICOM 영상 파일 | 메타데이터만 남고 영상 없음 |

### 컨테이너 재시작 시 데이터 유지 여부

현재 compose는 **bind mount** (호스트 절대경로 마운트) 방식이므로 Docker 명령과 무관하게 호스트 디스크에 데이터가 남습니다.

```yaml
# bind mount (현재 방식) — 호스트에 파일 그대로 유지
- /data/pacs/orthanc_dicom:/var/lib/orthanc/db

# named volume (이 방식이 아님) — down -v 시 삭제됨
# - orthanc_data:/var/lib/orthanc/db
```

| 상황 | 데이터 유지 | 설명 |
|---|---|---|
| `docker compose restart` | O | 컨테이너 재시작 |
| `docker compose stop` → `up -d` | O | 컨테이너 중지 후 재시작 |
| `docker compose down` → `up -d` | O | 컨테이너 삭제 후 재생성 |
| `docker compose down -v` → `up -d` | O | bind mount는 `-v`에 영향받지 않음 |
| 서버 재부팅 | O | `restart: always` 설정으로 자동 복구 |
| Docker 재설치 | O | 호스트 파일이므로 Docker와 무관 |
| **호스트 디스크 장애** | **X** | 별도 백업 없으면 복구 불가 |
| **호스트 경로 수동 삭제** | **X** | 직접 삭제하면 소실 |

### 백업 방법

#### 전체 백업 스크립트 (Linux/WSL2)

```bash
#!/bin/bash
# backup_pacs.sh
BACKUP_DIR="/backup/pacs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/pacs_backup_${TIMESTAMP}"
mkdir -p "${BACKUP_PATH}"

echo "[1/3] PostgreSQL 덤프..."
docker exec orthanc_db pg_dump -U orthanc orthanc_db \
  > "${BACKUP_PATH}/orthanc_db.sql"

echo "[2/3] DICOM 영상 파일 백업..."
rsync -a --info=progress2 \
  /data/pacs/orthanc_dicom/ \
  "${BACKUP_PATH}/orthanc_dicom/"

echo "[3/3] 설정 파일 백업..."
cp anno-docker-compose.yml "${BACKUP_PATH}/"

echo "=== 백업 완료: ${BACKUP_PATH} ==="
du -sh "${BACKUP_PATH}"
```

#### 전체 백업 스크립트 (Windows PowerShell)

```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = "D:\backup\pacs\pacs_backup_$timestamp"
New-Item -ItemType Directory -Path $backupPath -Force

docker exec orthanc_db pg_dump -U orthanc orthanc_db > "$backupPath\orthanc_db.sql"
robocopy "D:\pacs\orthanc_dicom" "$backupPath\orthanc_dicom" /E /MT:4
Copy-Item "anno-docker-compose.yml" -Destination $backupPath

Write-Host "백업 완료: $backupPath"
```

#### 개별 백업

```bash
# PostgreSQL만
docker exec orthanc_db pg_dump -U orthanc orthanc_db > orthanc_db_backup.sql
docker exec orthanc_db pg_dump -U orthanc orthanc_db | gzip > orthanc_db_backup.sql.gz

# DICOM 영상만 (Linux/WSL2)
rsync -a --info=progress2 /data/pacs/orthanc_dicom/ /backup/orthanc_dicom/
```

```powershell
# DICOM 영상만 (Windows)
robocopy "D:\pacs\orthanc_dicom" "D:\backup\orthanc_dicom" /MIR /MT:4
```

#### REST API 백업 (서비스 무중단)

```bash
curl -s -u UserID:UserID!23 http://localhost:8042/studies | python3 -m json.tool
curl -u UserID:UserID!23 http://localhost:8042/studies/{study-id}/archive -o study.zip
```

### 복구 방법

#### 전체 복구

```bash
# 1. 컨테이너 중지
docker compose -f anno-docker-compose.yml down

# 2. DICOM 영상 파일 복원
rsync -a /backup/orthanc_dicom/ /data/pacs/orthanc_dicom/   # Linux/WSL2
# robocopy "D:\backup\orthanc_dicom" "D:\pacs\orthanc_dicom" /MIR  # Windows

# 3. PostgreSQL 데이터 초기화
rm -rf /data/pacs/postgres_data/*   # Linux/WSL2
# Remove-Item "D:\pacs\postgres_data\*" -Recurse -Force  # Windows

# 4. 컨테이너 시작 + DB 초기화 대기
docker compose -f anno-docker-compose.yml up -d
sleep 10

# 5. PostgreSQL 덤프 복원
docker exec -i orthanc_db psql -U orthanc orthanc_db < /backup/orthanc_db.sql

# 6. Orthanc 재시작
docker compose -f anno-docker-compose.yml restart orthanc
```

#### DB 백업 없이 영상 파일만 있는 경우 (인덱스 재구축)

```bash
docker compose -f anno-docker-compose.yml down
rm -rf /data/pacs/postgres_data/*
docker compose -f anno-docker-compose.yml up -d
sleep 10

# DICOM 파일을 Orthanc에 다시 업로드 (인덱스 자동 재구축)
find /backup/orthanc_dicom -name "*.dcm" | while read f; do
  curl -s -u UserID:UserID!23 -X POST \
    http://localhost:8042/instances \
    --data-binary @"$f"
done
```

> 파일 수가 많으면 시간이 오래 걸립니다. PostgreSQL 백업도 함께 유지하세요.

### 백업/복구 테스트

#### 테스트 1: 영속성 확인

```bash
# Study 수 확인 → 컨테이너 재시작 → 다시 확인 (동일해야 함)
curl -s -u UserID:UserID!23 http://localhost:8042/statistics
docker compose -f anno-docker-compose.yml down
docker compose -f anno-docker-compose.yml up -d
curl -s -u UserID:UserID!23 http://localhost:8042/statistics
```

#### 테스트 2: 백업 → 삭제 → 복구

```bash
# 1. 상태 기록 + 백업
curl -s -u UserID:UserID!23 http://localhost:8042/statistics > before.json
docker exec orthanc_db pg_dump -U orthanc orthanc_db > test_backup.sql
rsync -a /data/pacs/orthanc_dicom/ /tmp/test_orthanc_dicom/

# 2. Study 하나 삭제
STUDY_ID=$(curl -s -u UserID:UserID!23 http://localhost:8042/studies \
  | python3 -c "import sys,json; print(json.load(sys.stdin)[0])")
curl -u UserID:UserID!23 -X DELETE http://localhost:8042/studies/${STUDY_ID}

# 3. 복구 실행
docker compose -f anno-docker-compose.yml down
rm -rf /data/pacs/postgres_data/*
rsync -a /tmp/test_orthanc_dicom/ /data/pacs/orthanc_dicom/
docker compose -f anno-docker-compose.yml up -d
sleep 10
docker exec -i orthanc_db psql -U orthanc orthanc_db < test_backup.sql
docker compose -f anno-docker-compose.yml restart orthanc
sleep 5

# 4. 검증 (차이 없으면 성공)
curl -s -u UserID:UserID!23 http://localhost:8042/statistics > after.json
diff <(python3 -m json.tool before.json) <(python3 -m json.tool after.json)
```

### 정기 백업 자동화

#### Linux/WSL2 (cron)

```bash
# crontab -e
0 2 * * * /path/to/backup_pacs.sh >> /var/log/pacs_backup.log 2>&1
0 3 * * * find /backup/pacs -name "pacs_backup_*" -mtime +30 -exec rm -rf {} +
```

#### Windows (작업 스케줄러)

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-File D:\scripts\backup_pacs.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At "02:00"
Register-ScheduledTask -TaskName "PACS_Backup" -Action $action -Trigger $trigger
```

---

## 문제 해결

### 컨테이너 시작 안 됨
```bash
docker compose -f anno-docker-compose.yml logs orthanc
docker compose -f anno-docker-compose.yml logs postgres
```

### DICOMweb 엔드포인트 응답 없음
```bash
# 인증 포함 테스트
curl -u UserID:UserID!23 http://localhost:8042/dicom-web/studies

# 원격 서버
curl -u UserID:UserID!23 http://192.168.0.100:8042/dicom-web/studies
```

### 원격 클라이언트에서 접속 안 됨
- 방화벽에서 **8042**, **1527** 포트 인바운드 허용 확인
- Docker가 0.0.0.0에 바인딩되어 있는지 확인 (기본값: O)
- 같은 네트워크 대역인지 확인

### WSL2 관련
- Docker Desktop이 WSL2 backend 사용 중인지 확인 (Settings > General > Use the WSL 2 based engine)
- GPU 인식 안 될 때: Windows NVIDIA 드라이버 업데이트
- 메모리 제한: `%USERPROFILE%\.wslconfig`에서 `memory=` 설정
