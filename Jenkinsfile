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
          echo "[ci] IMAGE_TAG=${env.IMAGE_TAG}"
        }
      }
    }

    stage('Preparar .env') {
      steps {
        script {
          if (isUnix()) {
            withCredentials([string(credentialsId: 'app-env', variable: 'APP_ENV')]) {
              sh '''
                set -e
                printf "%s\\n" "$APP_ENV" | tr -d '\\r' > .env
                echo "[ci] .env criado a partir do credential 'app-env'"

                # override pra NÃO publicar porta do Postgres no host (evita conflito da 5433)
                cat > docker-compose.override.yml <<'YAML'
services:
  db:
    ports: []
YAML

                # exporta pro shell atual se algo precisar direto
                set -a
                . ./.env
                set +a
              '''
            }
          } else {
            withCredentials([string(credentialsId: 'app-env', variable: 'APP_ENV')]) {
              powershell '''
$ErrorActionPreference = "Stop"
$dest = Join-Path $Env:WORKSPACE ".env"
[System.IO.File]::WriteAllText($dest, $Env:APP_ENV)
Write-Host "[ci] .env criado a partir do credential 'app-env'"

# override pra remover publicação de portas do serviço db
$override = @"
services:
  db:
    ports: []
"@
[System.IO.File]::WriteAllText((Join-Path $Env:WORKSPACE "docker-compose.override.yml"), $override)

# exporta variáveis deste .env pro processo atual (se algum passo usar direto)
Get-Content $dest | ForEach-Object {
  if ($_ -eq $null) { return }
  $line = $_.ToString()
  $trim = $line.Trim()
  if ($trim.Length -eq 0) { return }       # em branco
  if ($trim.StartsWith('#')) { return }    # comentário
  $kv = $line.Split('=', 2)
  if ($kv.Count -ne 2) { return }
  $k = $kv[0].Trim()
  $v = $kv[1]
  [System.Environment]::SetEnvironmentVariable($k, $v, 'Process')
}
              '''
            }
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

              compose_cmd="docker compose"
              if ! docker compose version >/dev/null 2>&1; then
                if command -v docker-compose >/dev/null 2>&1; then compose_cmd="docker-compose"; fi
              fi
              echo "Usando: $compose_cmd"

              cleanup() { $compose_cmd -f docker-compose.yml -f docker-compose.override.yml down -v || true; }
              trap cleanup EXIT

              # carrega .env explicitamente e usa override pra não publicar portas
              $compose_cmd --env-file .env -f docker-compose.yml -f docker-compose.override.yml up -d db
              $compose_cmd --env-file .env -f docker-compose.yml -f docker-compose.override.yml run --rm api bash scripts/run_tests.sh
            '''
          } else {
            powershell '''
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path "reports" | Out-Null
New-Item -ItemType Directory -Force -Path "artifacts" | Out-Null
$Env:COMPOSE_PROJECT_NAME = "fastapi-ci-$Env:BUILD_NUMBER"

$composeCmd = 'docker compose'
try { docker compose version | Out-Null } catch {
  if (Get-Command docker-compose -ErrorAction SilentlyContinue) { $composeCmd = 'docker-compose' }
}
Write-Host "Usando: $composeCmd"

# usa .env explicitamente e override sem portas
Invoke-Expression "$composeCmd --env-file .env -f docker-compose.yml -f docker-compose.override.yml up -d db"
try {
  Invoke-Expression "$composeCmd --env-file .env -f docker-compose.yml -f docker-compose.override.yml run --rm api bash scripts/run_tests.sh"
} finally {
  try { Invoke-Expression "$composeCmd -f docker-compose.yml -f docker-compose.override.yml down -v" } catch { Write-Warning "Falha ao derrubar serviços: $($_.Exception.Message)" }
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
                python:3.13-slim sh -lc "python scripts/notify.py --status \\"$STATUS\\" --run-id \\"$RUNID\\" --repo \\"$REPO\\" --branch \\"$BRANCH\\""
            '''
          } else {
            powershell '''
$ErrorActionPreference = "Stop"
$STATUS = "${currentBuild.currentResult}"
$REPO = git config --get remote.origin.url 2>$null; if ([string]::IsNullOrWhiteSpace($REPO)) { $REPO = 'unknown' }
$BRANCH = git rev-parse --abbrev-ref HEAD 2>$null; if ([string]::IsNullOrWhiteSpace($BRANCH)) { $BRANCH = 'unknown' }
$RUNID = if ($Env:BUILD_URL) { $Env:BUILD_URL } else { "${JOB_NAME}#${BUILD_NUMBER}" }

# usa WORKSPACE para montar o volume corretamente no Windows
$workspace = $Env:WORKSPACE
$volume = "$workspace:/app"
docker run --rm -v "$volume" -w /app `
  -e SMTP_HOST="$Env:SMTP_HOST" -e SMTP_PORT="$Env:SMTP_PORT" `
  -e SMTP_USER="$Env:SMTP_USER" -e SMTP_PASS="$Env:SMTP_PASS" -e EMAIL_TO="$Env:EMAIL_TO" `
  python:3.13-slim sh -lc "python scripts/notify.py --status `"$STATUS`" --run-id `"$RUNID`" --repo `"$REPO`" --branch `"$BRANCH`""
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
