# 개발 서버 온·오프 가이드

이 문서는 저장소 안에서 프론트엔드(Vite + Vue)와 백엔드(Django + Gunicorn)를 개발·운영할 때 서버를 안전하게 켜고 끄는 절차를 한곳에 정리한 것입니다. 로컬 개발 서버와 Docker Compose 기반의 통합 스택 모두를 다룹니다.

## 1. 공통 준비 사항

| 항목 | 권장 버전 | 비고 |
| --- | --- | --- |
| Node.js | 18 LTS 이상 | Vite 개발 서버용 |
| npm | 9 이상 | `npm run dev`, `npm run build` 실행 |
| Python | 3.11 | 백엔드 `requirements.txt`와 동일 |
| Docker / Docker Compose | 최신 | DB 및 배포형 컨테이너 실행 |
| `.env` | 루트(`./.env`) | Postgres·Django 환경변수 공유 |

> **TIP**: 이미 서버가 떠 있는 상태에서 코드를 손보려면, 먼저 어떤 프로세스가 포트를 점유 중인지(`lsof -i :포트`) 확인한 뒤 필요 시 정지하세요.

## 2. 프론트엔드(Vite) 서버

### 2-1. 최초 설정

```bash
cd ~/app/frontend
npm install
```

### 2-2. 개발 서버 켜기

```bash
npm run dev
```

- 기본 포트는 `5173`입니다. 브라우저에서 `http://localhost:5173`을 열어 확인합니다.
- Vite dev 서버는 `/api/*` 요청을 `http://localhost:8000`으로 프록시합니다. 다른 백엔드 주소를 써야 하면 `VITE_API_PROXY_TARGET=http://127.0.0.1:9000 npm run dev`처럼 환경변수를 덧붙입니다.

### 2-3. 개발 서버 끄기

- 터미널에서 `Ctrl + C`를 누르면 바로 중단됩니다.

### 2-4. 정적 빌드(Nginx용)

```bash
npm run build
```

빌드 산출물은 자동으로 `~/app/frontend_build`에 덮어써지며, `docker-compose.yml`의 nginx 서비스가 즉시 이 디렉터리를 서빙합니다. 배포 중에는 `npm run build` → `docker compose restart nginx` 순으로 진행하면 최신 빌드가 반영됩니다.

## 3. 백엔드(Django) 서버

### 3-1. 데이터베이스 컨테이너 준비

로컬에서 장고만 띄울 계획이라도 Postgres는 Compose로 실행하는 편이 가장 간단합니다.

```bash
cd ~/app
docker compose up -d db
```

- DB는 호스트에서 `localhost:5433`으로 접근할 수 있습니다.
- 중단하려면 `docker compose stop db` 또는 전체 종료 시 `docker compose down`을 사용합니다.

### 3-2. 로컬 Django 개발 서버

```bash
cd ~/app/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

- `http://localhost:8000`에서 API를 확인합니다.
- 서버를 끄려면 `Ctrl + C`를 누릅니다.
- 관리자 계정이 필요하면 별도 터미널에서 `python manage.py createsuperuser`를 실행하세요.

### 3-3. Docker 기반(배포형) 백엔드

```bash
cd ~/app
docker compose up -d backend nginx
```

- `backend` 컨테이너는 실행 시 자동으로 `migrate`와 `collectstatic`을 수행한 뒤 Gunicorn을 `0.0.0.0:8000`에 바인딩합니다.
- 정지하려면 `docker compose stop backend nginx` 또는 전체 종료 시 `docker compose down`.
- 로그 확인: `docker compose logs -f backend` / `docker compose logs -f nginx`.

## 4. 서버 상태 점검 루틴

| 단계 | 확인 방법 |
| --- | --- |
| 프론트 dev 서버 | 브라우저에서 SPA UI가 뜨는지, 콘솔 오류 여부 |
| 백엔드 dev 서버 | `curl http://localhost:8000/` 또는 헬스체크 엔드포인트 호출 |
| DB 연결 | `docker compose ps db`로 `healthy` 상태인지, `psql -h localhost -p 5433 ...` |
| 배포형 스택 | `docker compose ps`에서 `Up` / `healthy`인지, nginx 80/443 응답 여부 |

## 5. 빠른 참조 표

| 대상 | 켜기 | 끄기 | 비고 |
| --- | --- | --- | --- |
| 프론트 dev | `npm run dev` | 터미널 `Ctrl + C` | 필요 시 `VITE_API_PROXY_TARGET` 지정 |
| 프론트 빌드 | `npm run build` | (해당 없음) | 결과물이 `frontend_build/`로 복사 |
| 백엔드 dev | `python manage.py runserver 0.0.0.0:8000` | `Ctrl + C` | 실행 전 `docker compose up -d db` |
| 백엔드(배포) | `docker compose up -d backend` | `docker compose stop backend` | Gunicorn + auto migrate/collectstatic |
| 전체 스택 | `docker compose up -d` | `docker compose down` | nginx까지 함께 기동 |

## 6. 자주 묻는 질문

- **포트가 이미 사용 중이라고 나옵니다.**  
  `lsof -i :5173` 또는 `lsof -i :8000`으로 기존 프로세스를 찾은 뒤 종료하세요.

- **프론트에서 API 호출이 실패합니다.**  
  1) 백엔드 dev 서버가 켜져 있는지 확인하고, 2) 다른 호스트를 쓰고 있다면 `VITE_API_PROXY_TARGET` 혹은 `VITE_API_BASE_URL`을 올바르게 설정했는지 확인하세요.

- **정적 파일을 최신으로 만들고 싶습니다.**  
  `npm run build` 후 `docker compose exec backend python manage.py collectstatic --noinput`를 실행하고 nginx를 재시작합니다.

- **DB를 완전히 초기화하고 싶습니다.**  
  `docker compose down -v`로 `/home/ubuntu/app/dbdata` 볼륨을 지울 수 있지만, 실제 운영 데이터가 삭제되므로 신중히 결정하세요.

---

필요한 경우 이 문서를 팀 위키나 배포 노트와 링크해 두고, 신규 인원이 쉽게 따라올 수 있도록 최신 상태로 유지해 주세요.
