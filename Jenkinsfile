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
              # 1) remove ports do db (evita conflito)
              # 2) remove env_file do api e injeta envs do Jenkins
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
              $compose_cmd -f docker-compose.yml -f docker-compose.ci.yml run --rm api bash scripts/run_tests.sh
            '''
          } else {
            powershell '''
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path "reports" | Out-Null
New-Item -ItemType Directory -Force -Path "artifacts" | Out-Null
$Env:COMPOSE_PROJECT_NAME = "fastapi-ci-$Env:BUILD_NUMBER"

# Mapeia DB_USR/DB_PSW -> nomes esperados
$Env:POSTGRES_USER     = $Env:DB_USR
$Env:POSTGRES_PASSWORD = $Env:DB_PSW

# (failsafe) se existir algum container publicando 5433, para
$ids = docker ps --format "{{.ID}} {{.Ports}}" `
  | Select-String ":5433->" `
  | ForEach-Object { $_.ToString().Trim().Split(' ',[System.StringSplitOptions]::RemoveEmptyEntries)[0] }
if ($ids) { $ids | ForEach-Object { Write-Host "[ci] Parando container que usa 5433: $_"; docker stop $_ | Out-Null } }

$composeCmd = 'docker compose'
try { docker compose version | Out-Null } catch {
  if (Get-Command docker-compose -ErrorAction SilentlyContinue) { $composeCmd = 'docker-compose' }
}
Write-Host "Usando: $composeCmd"

$dc  = Join-Path $Env:WORKSPACE 'docker-compose.yml'
$ci  = Join-Path $Env:WORKSPACE 'docker-compose.ci.yml'

Invoke-Expression "$composeCmd -f `"$dc`" -f `"$ci`" up -d db"
try {
  Invoke-Expression "$composeCmd -f `"$dc`" -f `"$ci`" run --rm api bash scripts/run_tests.sh"
} finally {
  try { Invoke-Expression "$composeCmd -f `"$dc`" -f `"$ci`" down -v" } catch { Write-Warning "Falha ao derrubar serviços: $($_.Exception.Message)" }
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

    stage('Build & Package (Docker)') {
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
  }

  post {
    always {
      withCredentials([
        usernamePassword(credentialsId: 'mailtrap-smtp', usernameVariable: 'SMTP_USER', passwordVariable: 'SMTP_PASS'),
        string(credentialsId: 'EMAIL_TO', variable: 'EMAIL_TO')
      ]) {
        script {
          if (isUnix()) {
            sh '''
              set -e
              STATUS="${currentBuild.currentResult}"
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
$STATUS = "${currentBuild.currentResult}"
$REPO = git config --get remote.origin.url 2>$null; if ([string]::IsNullOrWhiteSpace($REPO)) { $REPO = 'unknown' }
$BRANCH = git rev-parse --abbrev-ref HEAD 2>$null; if ([string]::IsNullOrWhiteSpace($BRANCH)) { $BRANCH = 'unknown' }
$RUNID = if ($Env:BUILD_URL) { $Env:BUILD_URL } else { "${JOB_NAME}#${BUILD_NUMBER}" }

# volume com expansão segura
$volume = "$($Env:WORKSPACE):/app"

# chama docker run usando ARRAY de argumentos (sem malabarismo de aspas)
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
