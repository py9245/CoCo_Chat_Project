# ssafy1811teams.com 배포 & 운영 가이드

배포 구성은 `~/app` 디렉터리의 Docker Compose 스택(Django + Postgres + Nginx)과 `frontend_build/index.html` 단일 파일로 이뤄져 있습니다. 도메인 `ssafy1811teams.com`을 기준으로 접속할 수 있도록 환경이 맞춰져 있으니, 아래 순서만 따라 하면 어느 네트워크에서든 접근 가능합니다.

---

## 1. 기본 접속 URL
- 별도 도메인을 구매하지 않아도 `https://15-164-232-40.nip.io` 주소로 바로 접속할 수 있습니다. `nip.io`가 자동으로 IP를 해석해 주며, 서버에 Let’s Encrypt 인증서를 발급해 두었습니다.
- 추후 커스텀 도메인을 사용하고 싶다면 `ssafy1811teams.com` 섹션에 있는 값들을 원하는 주소로 교체하면 됩니다. (A 레코드는 `15.164.232.40`으로 지정)

## 2. TLS 인증서
- `certs/live/15-164-232-40.nip.io/{fullchain.pem, privkey.pem}` 경로에 Let’s Encrypt 인증서를 발급해 두었습니다. (`nip.io` 무료 서브도메인)
- 다른 도메인으로 교체하고 싶다면 certbot으로 새 인증서를 발급한 뒤 `~/app/certs/live/<도메인>/`에 배치하고 `docker compose restart nginx`.

## 3. 환경 변수 & 설정 확인
- `.env`의 `DJANGO_ALLOWED_HOSTS`, `DJANGO_TRUSTED_ORIGINS`는 이미 도메인/IP 조합으로 세팅됨.
- `nginx/nginx.conf`의 `server_name`과 `ssl_certificate` 경로도 위 도메인을 바라보도록 구성됨.
- 수정을 했다면 `docker compose restart backend nginx`로 반영.

## 4. 서비스 기동 명령
모든 명령은 `~/app` 디렉터리에서 실행합니다.

```bash
cd ~/app

# 1) 컨테이너 이미지/의존성 최신화가 필요할 때(선택)
docker compose pull

# 2) 스택 기동 (db → backend → nginx 순)
docker compose up -d db
docker compose up -d backend
docker compose up -d nginx

# 3) 상태 확인
docker compose ps
docker compose logs -f backend   # Ctrl+C로 종료

# 4) 최초 실행 또는 마이그레이션 변경 시
docker compose exec backend python manage.py migrate --noinput
```

## 5. 동작 확인
1. 헬스체크: `curl -k https://15-164-232-40.nip.io/api/healthz` (커스텀 도메인을 쓰면 해당 주소로 교체)
2. 메시지 API: `curl -k https://15-164-232-40.nip.io/api/messages`
3. 브라우저 접속: `https://15-164-232-40.nip.io/` (GitHub Pages에서도 이 주소로 API를 호출)

## 6. 자주 하는 작업
- 새로운 메시지를 노출하고 싶다면 Django Admin(`https://15-164-232-40.nip.io/admin/`)에 로그인 후 **Message** 모델에 레코드를 추가.
- 의존성 업데이트 시
  ```bash
  cd ~/app/backend
  pip install -r requirements.in
  pip freeze > requirements.txt
  docker compose up -d --build backend
  ```
- 로그 모니터링: `docker compose logs -f nginx` 또는 `docker compose logs -f db`.

---

### Tip
- DNS, TLS, `.env` 값이 서로 맞지 않으면 브라우저 CSRF 오류나 301 루프가 생길 수 있으니, 변경 시 항상 세 요소를 함께 점검하세요.
- 도메인을 다른 곳으로 옮길 때는 위 파일들을 새 주소로 교체한 뒤 `docker compose restart nginx backend`를 실행하면 됩니다.
