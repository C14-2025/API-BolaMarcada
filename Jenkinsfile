pipeline {
  agent any

  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 45, unit: 'MINUTES')
  }

  environment {
    DOCKER_BUILDKIT = '1'
    IMAGE_NAME = 'ci-api'
    IMAGE_TAG  = ''                 // setado no Checkout (fallback no build)
    SMTP_HOST  = 'smtp.mailtrap.io'
    SMTP_PORT  = '2525'
    REPO_SLUG  = 'C14-2025/API-BolaMarcada'  // dono/repositorio no GitHub

    // ===== Credentials (um por variável) =====
    POSTGRES_SERVER = credentials('postgres-server')         // Secret text: db
    POSTGRES_DB     = credentials('postgres-dbname')         // Secret text: bolamarcadadb
    SECRET_KEY      = credentials('app-secret-key')          // Secret text
    ACCESS_TOKEN_EXPIRE_MINUTES = credentials('access-token-expire') // Secret text
    DB = credentials('pg-db') // Username+Password -> cria DB_USR e DB_PSW
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        script {
          if (isUnix()) {
            env.GIT_SHORT = sh(script: 'git rev-parse --short=8 HEAD || echo local', returnStdout: true).trim()
          } else {
            env.GIT_SHORT = powershell(script: '''
$ErrorActionPreference = "Stop"
$git = git rev-parse --short=8 HEAD 2>$null
if ([string]::IsNullOrWhiteSpace($git)) { $git = 'local' }
$git
''', returnStdout: true).trim()
          }
          env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_SHORT}"
          echo "[ci] IMAGE_TAG=${env.IMAGE_TAG ?: 'null'}"
        }
      }
    }

    stage('Compose override (CI)') {
      steps {
        script {
          if (isUnix()) {
            sh '''
cat > docker-compose.ci.yml <<'YAML'
services:
  db:
    ports: []
  api:
    env_file: []
    environment:
      SECRET_KEY: ${SECRET_KEY}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES}
      POSTGRES_SERVER: ${POSTGRES_SERVER}
      POSTGRES_HOST: ${POSTGRES_SERVER}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
YAML
'''
          } else {
            powershell '''
$override = @'
services:
  db:
    ports: []
  api:
    env_file: []
    environment:
      SECRET_KEY: ${SECRET_KEY}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES}
      POSTGRES_SERVER: ${POSTGRES_SERVER}
      POSTGRES_HOST: ${POSTGRES_SERVER}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
'@
[System.IO.File]::WriteAllText((Join-Path $Env:WORKSPACE "docker-compose.ci.yml"), $override)
'''
          }
        }
      }
    }

    stage('Testes (pytest)') {
      steps {
        script {
          if (isUnix()) {
            sh '''
set -e
mkdir -p reports artifacts
export COMPOSE_PROJECT_NAME="fastapi-ci-${BUILD_NUMBER}"

# Mapear DB_USR/DB_PSW para nomes esperados pelo compose/app
export POSTGRES_USER="$DB_USR"
export POSTGRES_PASSWORD="$DB_PSW"

compose_cmd="docker compose"
if ! docker compose version >/dev/null 2>&1; then
  if command -v docker-compose >/dev/null 2>&1; then compose_cmd="docker-compose"; fi
fi
echo "Usando: $compose_cmd"

cleanup() { $compose_cmd -f docker-compose.yml -f docker-compose.ci.yml down -v || true; }
trap cleanup EXIT

$compose_cmd -f docker-compose.yml -f docker-compose.ci.yml up -d db

# Normaliza CRLF sem sed -i (evita erro de rename no FS montado)
$compose_cmd -f docker-compose.yml -f docker-compose.ci.yml run --rm api bash -lc 'tr -d "\\r" < scripts/run_tests.sh > /tmp/run_tests.sh && chmod +x /tmp/run_tests.sh && /tmp/run_tests.sh'
'''
          } else {
            // Windows/PowerShell com passagem de argumentos (sem Invoke-Expression)
            powershell '''
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path "reports" | Out-Null
New-Item -ItemType Directory -Force -Path "artifacts" | Out-Null
$Env:COMPOSE_PROJECT_NAME = "fastapi-ci-$Env:BUILD_NUMBER"

# Mapeia DB_USR/DB_PSW -> nomes esperados
$Env:POSTGRES_USER     = $Env:DB_USR
$Env:POSTGRES_PASSWORD = $Env:DB_PSW

$dc  = Join-Path $Env:WORKSPACE 'docker-compose.yml'
$ci  = Join-Path $Env:WORKSPACE 'docker-compose.ci.yml'

# docker compose up -d db
$upArgs = @('compose','-f', $dc, '-f', $ci, 'up','-d','db')
& docker @upArgs

try {
  # Comando que será passado ao bash -lc
  $cmdStr = "tr -d '\r' < scripts/run_tests.sh > /tmp/run_tests.sh && chmod +x /tmp/run_tests.sh && /tmp/run_tests.sh"
  $runArgs = @('compose','-f', $dc, '-f', $ci, 'run','--rm','api','bash','-lc', $cmdStr)
  & docker @runArgs
}
finally {
  try {
    $downArgs = @('compose','-f', $dc, '-f', $ci, 'down','-v')
    & docker @downArgs
  } catch {
    Write-Warning "Falha ao derrubar serviços: $($_.Exception.Message)"
  }
}
'''
          }
        }
      }
      post {
        always {
          junit allowEmptyResults: true, testResults: 'reports/junit.xml'
          archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
      }
    }

    stage('Paralelo: Empacotamento + Notificação') {
      parallel {
        stage('Empacotamento (Docker)') {
          steps {
            script {
              if (isUnix()) {
                sh '''
set -e
mkdir -p artifacts
if [ -z "${IMAGE_TAG}" ]; then export IMAGE_TAG="${BUILD_NUMBER}-local"; fi
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -f Dockerfile .
docker image ls ${IMAGE_NAME}:${IMAGE_TAG}
docker save -o artifacts/${IMAGE_NAME}_${IMAGE_TAG}.tar ${IMAGE_NAME}:${IMAGE_TAG}
'''
              } else {
                powershell '''
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path "artifacts" | Out-Null
if ([string]::IsNullOrWhiteSpace($Env:IMAGE_TAG)) { $Env:IMAGE_TAG = "$($Env:BUILD_NUMBER)-local" }
$tag = "$($Env:IMAGE_NAME):$($Env:IMAGE_TAG)"
$archive = "artifacts/$($Env:IMAGE_NAME)_$($Env:IMAGE_TAG).tar"
docker build -t "$tag" -f Dockerfile .
docker image ls "$tag"
docker save -o "$archive" "$tag"
'''
              }
            }
            archiveArtifacts artifacts: 'artifacts/*.tar', onlyIfSuccessful: true
          }
        }

        stage('Notificação (paralela)') {
          steps {
            withCredentials([
              usernamePassword(credentialsId: 'mailtrap-smtp', usernameVariable: 'SMTP_USER', passwordVariable: 'SMTP_PASS'),
              string(credentialsId: 'EMAIL_TO', variable: 'EMAIL_TO')
            ]) {
              script {
                if (isUnix()) {
                  sh '''
set -e
STATUS="IN_PROGRESS"
REPO="$(git config --get remote.origin.url || echo unknown)"
BRANCH="$(git rev-parse --abbrev-ref HEAD || echo unknown)"
RUNID="${BUILD_URL:-${JOB_NAME}#${BUILD_NUMBER}}"

docker run --rm -v "$PWD:/app" -w /app \
  -e SMTP_HOST="${SMTP_HOST}" -e SMTP_PORT="${SMTP_PORT}" \
  -e SMTP_USER="$SMTP_USER" -e SMTP_PASS="$SMTP_PASS" -e EMAIL_TO="$EMAIL_TO" \
  python:3.13-slim python scripts/notify.py \
    --status "$STATUS" --run-id "$RUNID" --repo "$REPO" --branch "$BRANCH"
'''
                } else {
                  powershell '''
$ErrorActionPreference = "Stop"
$STATUS = "IN_PROGRESS"
$REPO = git config --get remote.origin.url 2>$null; if ([string]::IsNullOrWhiteSpace($REPO)) { $REPO = 'unknown' }
$BRANCH = git rev-parse --abbrev-ref HEAD 2>$null; if ([string]::IsNullOrWhiteSpace($BRANCH)) { $BRANCH = 'unknown' }
$RUNID = if ($Env:BUILD_URL) { $Env:BUILD_URL } else { "${JOB_NAME}#${BUILD_NUMBER}" }

$volume = "$($Env:WORKSPACE):/app"
$args = @(
  'run','--rm','-v', $volume,'-w','/app',
  '-e', "SMTP_HOST=$($Env:SMTP_HOST)",
  '-e', "SMTP_PORT=$($Env:SMTP_PORT)",
  '-e', "SMTP_USER=$($Env:SMTP_USER)",
  '-e', "SMTP_PASS=$($Env:SMTP_PASS)",
  '-e', "EMAIL_TO=$($Env:EMAIL_TO)",
  'python:3.13-slim',
  'python','scripts/notify.py',
  '--status', $STATUS,
  '--run-id', $RUNID,
  '--repo', $REPO,
  '--branch', $BRANCH
)
& docker @args
'''
                }
              }
            }
          }
        }
      }
    }

    stage('Publicar artefatos no GitHub') {
      steps {
        script { env.CI_STATUS = env.CI_STATUS ?: (currentBuild.currentResult ?: 'IN_PROGRESS') }

        // 1) Release (Linux usa gh cli em container autenticado no GHCR)
        withCredentials([usernamePassword(credentialsId: 'github-pat', usernameVariable: 'GH_USER', passwordVariable: 'GITHUB_TOKEN')]) {
          script {
            if (isUnix()) {
              sh '''
set -e
TAG="build-${BUILD_NUMBER}-${GIT_SHORT}"
OWNER="${REPO_SLUG%%/*}"

{
  echo "status=${CI_STATUS}"
  echo "image=${IMAGE_NAME}:${IMAGE_TAG}"
  echo "repo=${REPO_SLUG}"
  echo "commit=${GIT_SHORT}"
  echo "run=${BUILD_URL:-${JOB_NAME}#${BUILD_NUMBER}}"
} > build-info.txt

# login no GHCR para puxar ghcr.io/cli/cli
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GH_USER" --password-stdin

# cria release (ou só faz upload se já existir)
docker run --rm -v "$PWD:/w" -w /w -e GH_TOKEN="$GITHUB_TOKEN" ghcr.io/cli/cli:latest \
  release create "$TAG" reports/junit.xml build-info.txt \
  --repo "${REPO_SLUG}" \
  --title "Build ${BUILD_NUMBER} (${GIT_SHORT})" \
  --notes "Artefatos do Jenkins. Imagem Docker: ghcr.io/${OWNER}/ci-api:${IMAGE_TAG}" \
|| docker run --rm -v "$PWD:/w" -w /w -e GH_TOKEN="$GITHUB_TOKEN" ghcr.io/cli/cli:latest \
  release upload "$TAG" reports/junit.xml build-info.txt --repo "${REPO_SLUG}" --clobber

# envia artifacts/*.tar se existir
docker run --rm -v "$PWD:/w" -w /w \
  -e GH_TOKEN="$GITHUB_TOKEN" -e TAG="$TAG" -e REPO_SLUG="$REPO_SLUG" \
  ghcr.io/cli/cli:latest sh -lc 'set -- artifacts/*.tar; if [ -e "$1" ]; then gh release upload "$TAG" "$@" --repo "$REPO_SLUG" --clobber; fi'
'''
            } else {
              // Windows: usa REST API (sem precisar do gh cli)
              powershell '''
$ErrorActionPreference = "Stop"

$TAG = "build-$($Env:BUILD_NUMBER)-$($Env:GIT_SHORT)"
$owner = $Env:REPO_SLUG.Split('/')[0]

# build-info.txt
$lines = @(
  "status=$($Env:CI_STATUS)",
  "image=$($Env:IMAGE_NAME):$($Env:IMAGE_TAG)",
  "repo=$($Env:REPO_SLUG)",
  "commit=$($Env:GIT_SHORT)",
  "run=$($Env:BUILD_URL)"
)
[IO.File]::WriteAllLines((Join-Path $Env:WORKSPACE 'build-info.txt'), $lines)

$Headers = @{
  Authorization = "Bearer $($Env:GITHUB_TOKEN)"
  Accept        = "application/vnd.github+json"
  "User-Agent"  = "jenkins-ci"
}

# cria ou obtém release
$body = @{
  tag_name   = $TAG
  name       = "Build $($Env:BUILD_NUMBER) ($($Env:GIT_SHORT))"
  body       = "Artefatos do Jenkins. Imagem Docker: ghcr.io/$owner/ci-api:$($Env:IMAGE_TAG)"
  draft      = $false
  prerelease = $false
} | ConvertTo-Json

try {
  $res = Invoke-RestMethod -Method Post -Uri "https://api.github.com/repos/$($Env:REPO_SLUG)/releases" -Headers $Headers -Body $body
} catch {
  if ($_.Exception.Response.StatusCode.Value__ -eq 422) {
    $res = Invoke-RestMethod -Method Get -Uri "https://api.github.com/repos/$($Env:REPO_SLUG)/releases/tags/$TAG" -Headers $Headers
  } else { throw }
}

# upload_url vem como "...{?name,label}" -> corta antes do '{' (sem regex p/ evitar conflito no Groovy)
$uploadUrl = $res.upload_url.Split('{')[0]

# arquivos para enviar
$files = @("reports/junit.xml","build-info.txt")
$tarFiles = Get-ChildItem -Path "artifacts" -Filter *.tar -ErrorAction SilentlyContinue
if ($tarFiles) { $files += $tarFiles.FullName }

foreach ($f in $files) {
  if (Test-Path $f) {
    $name = [IO.Path]::GetFileName($f)
    Invoke-RestMethod -Method Post -Uri "$uploadUrl?name=$name" `
      -Headers @{ Authorization = $Headers.Authorization; "Content-Type" = "application/octet-stream"; "User-Agent" = "jenkins-ci" } `
      -InFile $f | Out-Null
  }
}
'''
            }
          }
        }

        // 2) Push da imagem para GHCR (Packages)
        withCredentials([usernamePassword(credentialsId: 'ghcr-cred', usernameVariable: 'GHCR_USER', passwordVariable: 'GHCR_TOKEN')]) {
          script {
            if (isUnix()) {
              sh '''
set -e
OWNER="${REPO_SLUG%%/*}"
echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
TARGET="ghcr.io/${OWNER}/ci-api:${IMAGE_TAG}"
docker tag ${IMAGE_NAME}:${IMAGE_TAG} "$TARGET"
docker push "$TARGET"
'''
            } else {
              powershell '''
$ErrorActionPreference = "Stop"
$OWNER = $Env:REPO_SLUG.Split('/')[0]
$TARGET = "ghcr.io/$OWNER/ci-api:$($Env:IMAGE_TAG)"
$Env:GHCR_TOKEN | docker login ghcr.io -u $Env:GHCR_USER --password-stdin
docker tag "$($Env:IMAGE_NAME):$($Env:IMAGE_TAG)" $TARGET
docker push $TARGET
'''
            }
          }
        }
      }
    }
  }

  post {
    always {
      script { env.CI_STATUS = currentBuild.currentResult ?: 'UNKNOWN' }

      withCredentials([
        usernamePassword(credentialsId: 'mailtrap-smtp', usernameVariable: 'SMTP_USER', passwordVariable: 'SMTP_PASS'),
        string(credentialsId: 'EMAIL_TO', variable: 'EMAIL_TO')
      ]) {
        script {
          if (isUnix()) {
            sh '''
set -e
STATUS="${CI_STATUS}"
REPO="$(git config --get remote.origin.url || echo unknown)"
BRANCH="$(git rev-parse --abbrev-ref HEAD || echo unknown)"
RUNID="${BUILD_URL:-${JOB_NAME}#${BUILD_NUMBER}}"

docker run --rm -v "$PWD:/app" -w /app \
  -e SMTP_HOST="${SMTP_HOST}" -e SMTP_PORT="${SMTP_PORT}" \
  -e SMTP_USER="$SMTP_USER" -e SMTP_PASS="$SMTP_PASS" -e EMAIL_TO="$EMAIL_TO" \
  python:3.13-slim python scripts/notify.py \
    --status "$STATUS" --run-id "$RUNID" --repo "$REPO" --branch "$BRANCH"
'''
          } else {
            powershell '''
$ErrorActionPreference = "Stop"
$STATUS = if ($Env:CI_STATUS) { $Env:CI_STATUS } else { "UNKNOWN" }
$REPO = git config --get remote.origin.url 2>$null; if ([string]::IsNullOrWhiteSpace($REPO)) { $REPO = 'unknown' }
$BRANCH = git rev-parse --abbrev-ref HEAD 2>$null; if ([string]::IsNullOrWhiteSpace($BRANCH)) { $BRANCH = 'unknown' }
$RUNID = if ($Env:BUILD_URL) { $Env:BUILD_URL } else { "${JOB_NAME}#${BUILD_NUMBER}" }

$volume = "$($Env:WORKSPACE):/app"
$args = @(
  'run','--rm','-v', $volume,'-w','/app',
  '-e', "SMTP_HOST=$($Env:SMTP_HOST)",
  '-e', "SMTP_PORT=$($Env:SMTP_PORT)",
  '-e', "SMTP_USER=$($Env:SMTP_USER)",
  '-e', "SMTP_PASS=$($Env:SMTP_PASS)",
  '-e', "EMAIL_TO=$($Env:EMAIL_TO)",
  'python:3.13-slim',
  'python','scripts/notify.py',
  '--status', $STATUS,
  '--run-id', $RUNID,
  '--repo', $REPO,
  '--branch', $BRANCH
)
& docker @args
'''
          }
        }
      }

      script {
        if (isUnix()) {
          sh 'docker system prune -f || true'
        } else {
          powershell '''
$ErrorActionPreference = "SilentlyContinue"
try { docker system prune -f | Out-Null } catch { Write-Warning "Falha ao limpar docker: $($_.Exception.Message)" }
'''
        }
      }
    }
  }
}
