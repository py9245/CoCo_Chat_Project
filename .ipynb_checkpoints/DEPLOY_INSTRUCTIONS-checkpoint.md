# ssafy1811teams.com 배포 & 운영 가이드

배포 구성은 `~/app` 디렉터리의 Docker Compose 스택(Django + Postgres + Nginx)과 `frontend_build/index.html` 단일 파일로 이뤄져 있습니다. 도메인 `ssafy1811teams.com`을 기준으로 접속할 수 있도록 환경이 맞춰져 있으니, 아래 순서만 따라 하면 어느 네트워크에서든 접근 가능합니다.

---

## 1. DNS 연결
1. 도메인 관리 콘솔에 접속.
2. `ssafy1811teams.com`과 `www.ssafy1811teams.com`의 A 레코드를 모두 **15.164.232.40**로 설정.
3. 전파 여부는 `nslookup ssafy1811teams.com` 또는 `dig ssafy1811teams.com`으로 확인.

> DNS가 제대로 연결돼야 SSL 인증서 갱신이나 접속 테스트가 정상 동작합니다.

## 2. TLS 인증서
- 현재 `certs/live/ssafy1811teams.com/{fullchain.pem, privkey.pem}`에 자체 서명 인증서를 넣어 두었습니다. 브라우저 경고 없이 운영하려면 동일 경로에 **Let’s Encrypt나 정식 CA 인증서**를 덮어쓰면 됩니다.
- 예시) certbot 등으로 발급 후 결과물을 `~/app/certs/live/ssafy1811teams.com/`에 복사 → `docker compose restart nginx`.

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
1. 헬스체크: `curl -k https://ssafy1811teams.com/api/healthz`
2. 메시지 API: `curl -k https://ssafy1811teams.com/api/messages`
3. 브라우저 접속: `https://ssafy1811teams.com/` (브라우저 경고는 인증서 교체 시 사라짐)

## 6. 자주 하는 작업
- 새로운 메시지를 노출하고 싶다면 Django Admin(`https://ssafy1811teams.com/admin/`)에 로그인 후 **Message** 모델에 레코드를 추가.
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
