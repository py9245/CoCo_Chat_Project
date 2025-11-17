# Docker / nginx 자주 쓰는 명령어 모음

EC2 호스트에서 컨테이너 운영과 리버스 프록시 설정을 점검할 때 자주 사용하는 명령을 정리했습니다. 명령은 기본적으로 `/home/ubuntu/app`에서 실행한다고 가정합니다.

---

## 1. Docker Compose
| 목적 | 명령 | 설명 |
|------|------|------|
| 서비스 기동 | `docker compose up -d` | 모든 서비스를 백그라운드(detached)로 실행 |
| 개별 서비스 기동 | `docker compose up -d backend` | 특정 서비스만 재기동 (의존성 자동 처리) |
| 빌드 | `docker compose build backend` | 해당 서비스 Dockerfile 빌드 |
| 상태 확인 | `docker compose ps` | 현재 컨테이너 상태 요약 |
| 로그 실시간 보기 | `docker compose logs -f backend` | 특정 서비스 로그 tail |
| 마지막 N줄만 보기 | `docker compose logs --tail 200 nginx` | 문제 구간만 빠르게 확인 |
| 컨테이너 안 명령 실행 | `docker compose exec backend python manage.py migrate` | 런타임 명령 (쉘 필요 시 `-it sh`) |
| 재시작 | `docker compose restart nginx` | 설정 변경 후 빠른 반영 |
| 중지 & 삭제 | `docker compose down` | 모든 컨테이너/네트워크 정리 (데이터 볼륨은 보존) |
| 볼륨까지 삭제 | `docker compose down -v` | DB 등 영구 데이터도 삭제되니 주의 |

---

## 2. Docker 단일 컨테이너 도구
- `docker ps -a` : 모든 컨테이너 나열
- `docker rm <container>` / `docker rmi <image>` : 불필요 자원 정리
- `docker system prune -af` : 멈춘 컨테이너·dangling 이미지 삭제 (신중히 사용)
- `docker logs <container>` : Compose 외 단일 컨테이너 확인 시
- `docker exec -it <container> /bin/sh` : 컨테이너 내부 셸 접속

---

## 3. nginx 관련 명령
### 컨테이너 안에서
```bash
# 설정 문법 확인
docker compose exec nginx nginx -t

# 설정 리로드 (무중단)
docker compose exec nginx nginx -s reload

# 쉘로 들어가서 직접 확인
docker compose exec -it nginx /bin/sh
cat /etc/nginx/nginx.conf
```

### 호스트(EC2)에서
- `sudo systemctl status nginx` : 호스트 nginx 서비스가 충돌로 기동된 경우 확인 (현재 구성은 컨테이너를 사용하므로 비활성화 권장)
- `sudo lsof -i :80` / `:443` : 포트를 누가 점유하는지 확인
- 인증서 확인: `sudo ls -al /etc/letsencrypt/live/<domain>/`

---

## 4. 문제 해결 체크리스트
1. **컨테이너가 안 뜸** → `docker compose ps` 상태 / `docker compose logs <svc>` 오류 확인 (DB 연결, 마이그레이션 등)
2. **nginx 502/504** → `nginx -t` 문법, `backend` 컨테이너 포트/프로세스 확인
3. **정적 파일 미서빙** → `frontend_build` 최신 빌드인지, 볼륨이 `:ro`로 잘 마운트됐는지 확인
4. **HTTPS 실패** → 인증서 파일 경로/권한, 443 포트 충돌 여부 점검
5. **도메인 불일치** → `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `window.API_BASE_URL` 설정 재확인

필요 명령을 이 표에서 빠르게 찾아 상황에 맞게 적용하면 운영 효율을 크게 높일 수 있습니다.
