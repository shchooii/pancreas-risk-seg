# pancreas-risk-seg

췌장 CT/MRI 데이터를 대상으로  
**3D Slicer, Orthanc, nnInteractive**를 활용해  
영상 조회와 annotation을 수행하기 위한 연구용 저장소입니다.

향후 본 파이프라인을 기반으로  
**pancreas / cyst segmentation** 및 **risk classification** 연구로 확장할 예정입니다.

## Overview

이 프로젝트는 다음과 같은 workflow를 목표로 합니다.

- Orthanc 서버에 DICOM 업로드
- 3D Slicer에서 영상 조회
- nnInteractive를 이용한 segmentation annotation
- 향후 segmentation 및 위험도 분류 연구로 확장

## Structure

```bash
3d-slicer/
├── client/
│   ├── CLIENT_GUIDE.md
│   ├── DICOMwebBrowser.py
│   ├── .slicerrc.py
│   └── setup.bat
└── server/
    ├── SERVER_GUIDE.md
    └── anno-docker-compose.yml
````

## Server

서버는 **Orthanc + PostgreSQL + nnInteractive** 로 구성됩니다.

실행:

```bash
cd 3d-slicer/server
docker compose -f anno-docker-compose.yml up -d
```

주요 포트:

* `8042` : Orthanc web / DICOMweb
* `4242` : DICOM
* `1527` : nnInteractive


## 3D Slicer 사용 방법

### 1. 서버 실행

먼저 Orthanc 서버를 실행합니다.

```bash
cd 3d-slicer/server
docker compose -f anno-docker-compose.yml up -d
```

### 2. 클라이언트 설정

`3d-slicer/client` 폴더의 설정 파일을 사용합니다.

* `setup.bat`
* `.slicerrc.py`
* `DICOMwebBrowser.py`

### 3. 3D Slicer 실행

3D Slicer를 실행한 뒤,
**DICOMweb Browser** 를 통해 Orthanc 서버에 연결합니다.

예시:

```text
http://localhost:8042/dicom-web
```

### 4. 영상 조회

Orthanc에 업로드된 CT/MRI 영상을
3D Slicer에서 조회합니다.

### 5. Annotation

nnInteractive와 연결하여
pancreas / cyst segmentation annotation을 수행합니다.

## Upload Example

Orthanc에 DICOM 업로드:

```bash
curl -u USER:PASSWORD -X POST \
  http://localhost:8042/instances \
  --data-binary @/path/to/file.dcm
```

폴더 단위 업로드:

```bash
find /path/to/dicom_folder -name "*.dcm" -print0 | \
xargs -0 -P 4 -I {} curl -s -u USER:PASSWORD -X POST \
  http://localhost:8042/instances \
  --data-binary @"{}"
```

## Current Status

* Orthanc 서버 배포 및 관리
* 3D Slicer 기반 영상 조회
* nnInteractive 기반 annotation 진행 중
* 향후 segmentation / risk classification 실험 예정
