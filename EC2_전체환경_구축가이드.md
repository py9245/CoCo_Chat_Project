# EC2 + Vue/Django/Docker/nginx + GitHub Pages 구축 가이드

새 EC2 인스턴스에서 **백엔드(Django + Postgres + Gunicorn)**, **정적 배포(Vue 3 + Vite 빌드)**, **Reverse Proxy(nginx)**, **GitHub Pages 프런트**를 동일한 흐름으로 재현하는 방법을 단계별로 정리했습니다. 아래 절차만 따르면 팀원이 처음 EC2를 받은 상황에서도 같은 구성을 만들 수 있습니다.

---

## 1. 사전 준비
- **AWS 계정**과 IAM 권한(EC2, Elastic IP, Certificate Manager/LetsEncrypt 발급 권한 등).
- **도메인** 또는 nip.io 같은 임시 도메인.
- **GitHub 저장소 2개**
  1. 애플리케이션(백엔드/프런트/인프라) 저장소
  2. GitHub Pages (`<username>.github.io`) 저장소
- **로컬 개발 PC**
  - SSH 접속 가능 (pem 키 관리)
  - Node.js LTS(18+) / npm, Docker Desktop(선택)
- **배포용 비밀 값**
  - Django `SECRET_KEY`
  - Postgres 계정/DB 이름/패스워드
  - S3·메일 등 외부 서비스 키(선택)

---

## 2. EC2 인스턴스 생성
1. **콘솔 → EC2 → Launch Instance**
2. AMI: Ubuntu Server 22.04 LTS
3. 인스턴스 타입: t3.small 이상 권장 (CPU 2 vCPU / RAM 2~4GB)
4. 키 페어: 팀 공용 키 혹은 개인 키 등록
5. 네트워크:
   - VPC/Subnet: 기본값 또는 사전 지정 서브넷
   - 보안 그룹: 아래 규칙 참고 (HTTP 80, HTTPS 443 전체 오픈, SSH는 특정 IP)
6. 저장소: gp3 30GB 이상 (Docker 이미지 + DB 데이터 여유 감안)
7. Launch 후 탄력적 IP를 연결하거나 nip.io를 사용할 IP를 확인

---

## 3. 최초 접속 & 기본 패키지 설치
```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
sudo apt update && sudo apt upgrade -y

# Docker & Compose
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu       # 재로그인 필요
sudo apt install -y docker-compose-plugin

# 필수 도구
sudo apt install -y git make python3-pip nginx certbot python3-certbot-nginx

# Node.js (프런트 빌드용)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

재로그인 후 `docker ps`, `node -v`, `npm -v`가 동작하는지 확인합니다.

---

## 4. 프로젝트 구조 배치
```bash
cd /home/ubuntu
git clone <app-repo> app
cd app
cp .env.example .env   # 없으면 직접 작성
```

필요 폴더:
- `backend/`, `frontend/`, `frontend_build/`
- `docker-compose.yml`, `docker-compose.local.yml`
- `nginx/nginx.conf`
- `certs/`, `dbdata/` (컨테이너가 자동으로 채움)

---

## 5. 환경 변수(.env) 작성
`app/.env`에 아래 값을 채웁니다. 실제 비밀 값으로 치환하세요.

```dotenv
# Django
DJANGO_SECRET_KEY=your-secure-key
DJANGO_DEBUG=False
DJANGO_TIME_ZONE=Asia/Seoul
DJANGO_ALLOWED_HOSTS=example.com,www.example.com,15.164.x.x,*.nip.io,localhost,127.0.0.1
DJANGO_TRUSTED_ORIGINS=https://example.com,https://www.example.com,https://15.164.x.x

# Postgres (docker-compose db 서비스와 일치)
POSTGRES_USER=appuser
POSTGRES_PASSWORD=super-strong-password
POSTGRES_DB=appdb
DATABASE_URL=postgresql://appuser:super-strong-password@db:5432/appdb

# CORS (프런트 도메인)
CORS_ALLOWED_ORIGINS=https://<username>.github.io

# (선택) S3, Email 등 외부 서비스 키
USE_S3=0
```

필요 시 `.env.local`을 만들어 로컬 개발과 분리합니다.

---

## 6. Docker Compose로 백엔드/DB/nginx 구동
```bash
cd /home/ubuntu/app
docker compose pull               # 이미지 최신화 (필요 시)
docker compose build backend      # 백엔드 Dockerfile 빌드
docker compose up -d db           # DB 먼저 기동
docker compose up -d backend
docker compose up -d nginx

# 최초 마이그레이션/슈퍼유저
docker compose exec backend python manage.py migrate --noinput
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py collectstatic --noinput
```

컨테이너 상태는 `docker compose ps`, 로그는 `docker compose logs -f <service>`로 확인합니다.

---

## 7. TLS 인증서 (Let’s Encrypt 예시)
1. nginx가 80/443을 리슨하고 있어야 함
2. DNS(A/CNAME)이 EC2 Public IP를 가리키는지 확인
3. `sudo certbot --nginx -d example.com -d www.example.com`
4. 인증서 경로(`/etc/letsencrypt/live/...`)를 `app/nginx/nginx.conf` 또는 `docker-compose.yml` 내 `./certs` 볼륨과 연결
5. 자동 갱신 크론 확인: `sudo systemctl list-timers | grep certbot`

현재 프로젝트는 `./certs` 폴더를 nginx 컨테이너에 마운트하는 방식이므로, EC2 호스트의 `/home/ubuntu/app/certs` 아래에 인증서 심볼릭 링크를 준비해야 합니다.

---

## 8. 프런트엔드 빌드 & GitHub Pages 배포
```bash
cd /home/ubuntu/app/frontend
npm ci      # 또는 npm install
npm run build
```

- 빌드 산출물은 `../frontend_build`에 생성됩니다.
- GitHub Pages 저장소(예: `py9245/py9245.github.io`)를 로컬/별도 클론 후 `frontend_build` 내용을 복사해서 커밋/푸시합니다.

GitHub Actions나 Deploy Script를 쓰고 싶다면:
1. `frontend_build`를 압축하여 Pages 저장소에 push
2. 또는 `vite build` 결과를 Pages repo의 서브모듈로 연결

> **TIP:** `import.meta.env.VITE_API_BASE_URL` 환경변수 또는 `window.API_BASE_URL` 전역값으로 백엔드 API 도메인을 주입하면 GitHub Pages에서도 백엔드와 통신합니다.

---

## 9. 런타임 점검
- **헬스체크**: `curl -I https://<domain>/healthz`
- **Django Admin**: `https://<domain>/admin/`
- **정적 SPA**: `https://<domain>/` (nginx가 `frontend_build` 서빙)
- **GitHub Pages**: `https://<username>.github.io/` → 개발자 도구 네트워크 탭에서 API 요청이 EC2 도메인으로 나가는지 확인

---

## 10. 운영 팁
- 컨테이너 재시작: `docker compose restart backend`
- 로그 확인: `docker compose logs -n 100 backend`
- DB 백업: `docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql`
- 배포 자동화: GitHub Actions/CodeBuild에서 SSH 배포 또는 ECR + ECS 전환 검토
- 모니터링: AWS CloudWatch Agent, Sentry, Prometheus 등과 연동 가능

위 단계들을 순서대로 수행하면 EC2 인스턴스마다 동일한 Docker 기반 운영 환경을 재현할 수 있습니다.
