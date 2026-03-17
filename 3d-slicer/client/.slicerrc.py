import os
import shutil
import configparser
import qt
import slicer

# ==============================================================================
# [설정] 소스 폴더 경로 자동 인식
# setup.bat를 통해 사용자 홈 폴더로 복사된 후 실행되므로, 
# 현재 스크립트가 있는 위치(__file__)를 기준으로 동봉된 파일들을 찾습니다.
# ==============================================================================

CUSTOM_SOURCE_DIR = os.path.expanduser("~")

def setup_environment():
    print("-" * 60)
    print(f"[Auto-Setup] 소스 파일 경로: {CUSTOM_SOURCE_DIR}")
    print("[Auto-Setup] Slicer 환경 자동 구성을 시작합니다.")

    # --------------------------------------------------------------------------
    # 1. 확장 프로그램 설치 점검 (DICOMweb, NNInteractive, QuantitativeReporting)
    # --------------------------------------------------------------------------
    required_extensions = ["DICOMwebBrowser", "NNInteractive", "QuantitativeReporting"]
    
    manager = slicer.app.extensionsManagerModel()
    need_restart = False

    for ext_name in required_extensions:
        if not manager.isExtensionInstalled(ext_name):
            print(f"[Install] '{ext_name}' 확장 프로그램 설치 중... (다운로드)")
            if manager.installExtensionFromServer(ext_name):
                print(f"[Install] '{ext_name}' 설치 성공.")
                need_restart = True
            else:
                print(f"[Error] '{ext_name}' 설치 실패. 인터넷 연결이나 확장 명칭을 확인하세요.")
        else:
            print(f"[Check] '{ext_name}' 이미 설치되어 있습니다.")

    if need_restart:
        print("[System] 확장 프로그램 설치 완료. 적용을 위해 Slicer를 재시작합니다...")
        qt.QTimer.singleShot(1000, slicer.util.restart)
        return

    # --------------------------------------------------------------------------
    # 2. 파일 교체 및 config.ini 복사
    # --------------------------------------------------------------------------
    try:
        if not hasattr(slicer.modules, 'dicomwebbrowser'):
            print("[Warning] DICOMwebBrowser 모듈이 아직 로드되지 않았습니다.")
        else:
            # 실제 설치된 모듈 경로 추적
            target_module_path = slicer.modules.dicomwebbrowser.path
            target_dir = os.path.dirname(target_module_path)
            
            print(f"[Path] 타겟 설치 경로: {target_dir}")

            # (1) DICOMwebBrowser.py 교체
            src_py = os.path.join(CUSTOM_SOURCE_DIR, "DICOMwebBrowser.py")
            if os.path.exists(src_py):
                try:
                    shutil.copy2(src_py, target_module_path)
                    print("[Update] DICOMwebBrowser.py 파일을 성공적으로 교체했습니다.")
                except PermissionError:
                     print("[Error] 파일 교체 권한이 없습니다.")
            else:
                print(f"[Skip] 교체할 파일이 없습니다: {src_py}")

            # (2) config.ini 복사
            src_conf = os.path.join(CUSTOM_SOURCE_DIR, "config.ini")
            target_conf = os.path.join(target_dir, "config.ini")
            
            if os.path.exists(src_conf):
                shutil.copy2(src_conf, target_conf)
                print("[Update] config.ini 파일을 모듈 폴더로 복사했습니다.")
                
                # --------------------------------------------------------------------------
                # 3. config.ini 검증 (DICOMwebBrowser가 서버별 자동 인증 처리)
                #    - 섹션명(hostname)으로 접속 시 자동 매칭되므로 전역 등록 불필요
                #    - 서버 추가 시 config.ini에 [hostname] 섹션만 추가하면 자동 반영
                # --------------------------------------------------------------------------
                config = configparser.ConfigParser()
                config.read(target_conf)

                if config.sections():
                    for section in config.sections():
                        if config.has_option(section, "user") and config.has_option(section, "password"):
                            user_id = config.get(section, "user")
                            print(f"[Auth] 서버 [{section}] -> ID({user_id}) 설정 확인됨 (접속 시 자동 인증)")
                        else:
                            print(f"[Warning] [{section}] 섹션에 'user' 또는 'password' 항목이 없습니다.")
                    print(f"[Auth] 총 {len(config.sections())}개 서버 설정 로드 완료.")
                else:
                    print("[Warning] config.ini 파일에 서버 설정([...])이 없습니다.")

            else:
                print(f"[Skip] 설정 파일이 없습니다: {src_conf}")

    except Exception as e:
        print(f"[Error] 작업 중 예기치 않은 오류 발생: {e}")

    print("[Auto-Setup] 모든 설정 완료.")
    print("-" * 60)

# 함수 실행
setup_environment()