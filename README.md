# ArrangingFolders
unreal plugin

## Engine-Level Plugin Setup

### 엔진 레벨 플러그인 설정

엔진 레벨 플러그인은 해당 언리얼 엔진 버전을 사용하는 모든 프로젝트에서 공통으로 사용할 수 있는 플러그인입니다.
여러 프로젝트에서 동일한 플러그인을 재사용할 때 적합합니다.

설정 방법:

* 언리얼 엔진 설치 경로를 찾습니다.

```
예) C:\Program Files\Epic Games\UE_5.4\Engine\Plugins
```

* Plugins 폴더 내부에 사용자 전용 폴더를 생성합니다.

```
예) MyCompany 또는 CustomTools
```

* 제작한 플러그인 폴더를 그 안에 넣습니다.

```
예) C:\Program Files\Epic Games\UE_5.4\Engine\Plugins\MyCompany\MyPlugin
```

* 언리얼 에디터를 재시작하면,

```
Edit → Plugins → Installed → Engine 탭에서 플러그인을 확인할 수 있습니다.
```

* 플러그인을 활성화하고, 에디터 재시작 안내가 뜨면 다시 실행합니다.

주의사항:
* 엔진 폴더 수정 시 관리자 권한이 필요합니다.
* 엔진 업데이트나 재설치 시 플러그인이 삭제될 수 있으니 백업을 권장합니다.

⸻

## Project-Level Plugin Setup

### 프로젝트 레벨 플러그인 설정

프로젝트 레벨 플러그인은 특정 프로젝트 내부에 저장되며, 해당 프로젝트에서만 사용할 수 있습니다.
특정 프로젝트 전용 플러그인을 개발할 때 적합합니다.

설정 방법:
* 프로젝트 폴더를 엽니다.
```
예) D:\workspace\MyGameProject
```
* Plugins 폴더가 없다면 직접 새로 생성합니다.
	
* 플러그인 폴더를 그 안에 복사합니다.
```
예) D:\workspace\MyGameProject\Plugins\MyPlugin
```

* 언리얼 에디터를 재시작합니다.
	
* Edit → Plugins → Installed → Project 탭에서 플러그인을 확인하고 활성화합니다.

주의사항:
* 프로젝트 내부에 포함되므로 Git 등 버전 관리에 용이합니다.
* 관리자 권한이 필요하지 않습니다.
* 개발 중 잦은 수정 및 테스트에 유리합니다.