pipeline {
  agent any

  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    disableConcurrentBuilds()
  }

  parameters {
    booleanParam(
      name: 'ENABLE_GH_RELEASE',
      defaultValue: true,
      description: 'Publicar image-<commit>.tar como asset em um Release do GitHub (opcional)'
    )
  }

  environment {
    // DB para testes
    PGUSER = 'postgres'
    PGPASS = 'postgres'
    PGDB   = 'bolamarcadadb'
    PGHOST = 'ci-db'
    PGPORT = '5432'

    // Relatórios/artefatos
    JUNIT_XML    = 'report-junit.xml'
    COVERAGE_XML = 'coverage.xml'
  }

  stages {
    stage('Checkout & Vars') {
      steps {
        checkout scm
        script {
          // commit curto
          env.COMMIT = bat(script: 'git rev-parse --short=8 HEAD', returnStdout: true).trim().readLines().last().trim()

          // branch robusto (evita HEAD em detached)
          def guess = env.BRANCH_NAME ?: env.GIT_BRANCH
          if (!guess || guess.trim() == 'HEAD') {
            def nameRev = bat(script: 'git name-rev --name-only HEAD', returnStdout: true).trim()
            guess = nameRev ?: 'unknown'
          }
          guess = guess.replaceFirst(/^origin\\//, '').replaceFirst(/^remotes\\/origin\\//, '')
          env.BRANCH = guess

          env.IMAGE     = "app:${env.COMMIT}"
          env.IMAGE_TAR = "image-${env.COMMIT}.tar"

          // TAG único por build (evita colar em release antiga)
          env.CI_TAG = "ci-${env.BUILD_NUMBER}-${env.COMMIT}"

          echo "BRANCH=${env.BRANCH}  CI_TAG=${env.CI_TAG}  COMMIT=${env.COMMIT}"
        }
      }
    }

    stage('Build image') {
      steps {
        bat '''
          @echo on
          docker version
          docker build --pull -t %IMAGE% -t app:latest .
        '''
      }
    }

    stage('CI (parallel)') {
      failFast false
      parallel {

        stage('Testes') {
  steps {
    script {
      catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
        withCredentials([
          string(credentialsId: 'app-secret-key',       variable: 'SECRET_KEY'),
          string(credentialsId: 'access-token-expire', variable: 'ACCESS_TOKEN_EXPIRE_MINUTES')
        ]) {
          bat """
            @echo on
            rem -- rede dedicada
            docker network create ci_net 2>nul || echo net exists

            rem -- sobe Postgres
            docker rm -f ci-db 2>nul
            docker run -d --name ci-db --network ci_net ^
              -e POSTGRES_USER=%PGUSER% -e POSTGRES_PASSWORD=%PGPASS% -e POSTGRES_DB=%PGDB% ^
              -p %PGPORT%:5432 postgres:17-alpine

            rem -- espera Postgres
            docker run --rm --network ci_net postgres:17-alpine sh -lc "until pg_isready -h %PGHOST% -p 5432 -U %PGUSER% -d %PGDB%; do sleep 1; done"

            rem -- roda pytest dentro da SUA imagem
            docker run --rm --network ci_net ^
              -e POSTGRES_SERVER=%PGHOST% -e POSTGRES_HOST=%PGHOST% ^
              -e POSTGRES_USER=%PGUSER% -e POSTGRES_PASSWORD=%PGPASS% -e POSTGRES_DB=%PGDB% ^
              -e DATABASE_URL=postgresql+psycopg2://%PGUSER%:%PGPASS%@%PGHOST%:5432/%PGDB% ^
              -e SECRET_KEY=%SECRET_KEY% ^
              -e ACCESS_TOKEN_EXPIRE_MINUTES=%ACCESS_TOKEN_EXPIRE_MINUTES% ^
              -e PYTHONPATH=/workspace ^
              -v "%cd%":/workspace -w /workspace %IMAGE% ^
              sh -lc "python -m pip install --disable-pip-version-check -U pip && python -m pip install pytest pytest-cov && pytest -vv tests --junit-xml=/workspace/%JUNIT_XML% --cov=/workspace --cov-report=xml:/workspace/%COVERAGE_XML%"

            set RC=%errorlevel%
            if %RC%==0 (
              echo SUCCESS>status_tests.txt
            ) else (
              echo FAILURE>status_tests.txt
              exit /b %RC%
            )
          """
        }
      }
    }
  }
  post {
  always {
    junit allowEmptyResults: true, testResults: "${JUNIT_XML}"
    archiveArtifacts allowEmptyArchive: true, artifacts: "${JUNIT_XML}, ${COVERAGE_XML}"
    bat '''
      @echo off
      rem -- cleanup tolerante a erros
      docker rm -f ci-db 1>nul 2>nul || ver > nul
      docker network rm ci_net 1>nul 2>nul || ver > nul
    '''
    script {
      if (!fileExists('status_tests.txt')) {
        writeFile file: 'status_tests.txt', text: 'FAILURE'
      }
    }
  }
}

        }
        stage('Empacotamento') {
          steps {
            script {
              catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                bat """
                  @echo on
                  docker save %IMAGE% -o %IMAGE_TAR%
                  set RC=%errorlevel%
                  if %RC%==0 (echo SUCCESS>status_package.txt) else (echo FAILURE>status_package.txt & exit /b %RC%)
                """
              }
            }
          }
          post {
            always {
              archiveArtifacts allowEmptyArchive: true, artifacts: "${IMAGE_TAR}"
              script {
                if (!fileExists('status_package.txt')) {
                  writeFile file: 'status_package.txt', text: 'FAILURE'
                }
              }
            }
          }
        }

      } // parallel
    }

    stage('Upload GitHub Release (opcional)') {
      when {
        allOf {
          expression { params.ENABLE_GH_RELEASE as boolean }
          // Libera para feat/CI/Docker, feat/CICD/Jenkins, main, master e release/*
          expression { return env.BRANCH ==~ /(feat\/CI\/Docker|feat\/CICD\/Jenkins|main|master|release\/.+)/ }
        }
      }
      steps {
        catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
          withCredentials([usernamePassword(credentialsId: 'github-pat', usernameVariable: 'GH_USER', passwordVariable: 'GH_PAT')]) {
            // Garante o script se não existir (idempotente e seguro)
            script {
              if (!fileExists('scripts')) { bat 'mkdir scripts 2>nul' }
              if (!fileExists('scripts/upload_github_release.sh')) {
                writeFile file: 'scripts/upload_github_release.sh', text: '''#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_TOKEN:?GITHUB_TOKEN ausente}"
: "${GITHUB_REPO:?GITHUB_REPO ausente (owner/repo)}"
: "${TAG:?TAG ausente}"
: "${ASSET_PATH:?ASSET_PATH ausente}"

if [ ! -f "$ASSET_PATH" ]; then
  echo "ERRO: asset não encontrado: $ASSET_PATH" >&2
  exit 2
fi

OWNER="${GITHUB_REPO%%/*}"
REPO="${GITHUB_REPO##*/}"
API="https://api.github.com"
UPLOADS="https://uploads.github.com"

auth=(-H "Authorization: Bearer ${GITHUB_TOKEN}" -H "Accept: application/vnd.github+json" -H "User-Agent: jenkins-ci")

echo "[gh] procurando release por tag: $TAG"
set +e
resp=$(curl -sS "${auth[@]}" "$API/repos/$OWNER/$REPO/releases/tags/$TAG")
code=$?
set -e

if echo "$resp" | jq -e .id >/dev/null 2>&1; then
  RELEASE_ID=$(echo "$resp" | jq -r .id)
  echo "[gh] release existente id=$RELEASE_ID"
else
  echo "[gh] criando release nova"
  payload=$(jq -n --arg tag "$TAG" --arg name "$TAG" \
    '{ tag_name: $tag, name: $name, draft: false, prerelease: false }')
  resp=$(curl -sS "${auth[@]}" -X POST "$API/repos/$OWNER/$REPO/releases" -d "$payload")
  if ! echo "$resp" | jq -e .id >/dev/null 2>&1; then
    echo "ERRO ao criar release: $resp" >&2
    exit 3
  fi
  RELEASE_ID=$(echo "$resp" | jq -r .id)
  echo "[gh] release criada id=$RELEASE_ID"
fi

# Apaga asset com mesmo nome (se existir) para 'clobber' real
asset_name="$(basename "$ASSET_PATH")"
assets=$(curl -sS "${auth[@]}" "$API/repos/$OWNER/$REPO/releases/$RELEASE_ID/assets")
asset_id=$(echo "$assets" | jq -r --arg n "$asset_name" '.[] | select(.name==$n) | .id' | head -n1)
if [ -n "${asset_id:-}" ] && [ "$asset_id" != "null" ]; then
  echo "[gh] removendo asset existente id=$asset_id ($asset_name)"
  curl -sS "${auth[@]}" -X DELETE "$API/repos/$OWNER/$REPO/releases/assets/$asset_id" >/dev/null
fi

echo "[gh] enviando asset: $asset_name"
upload_url="$UPLOADS/repos/$OWNER/$REPO/releases/$RELEASE_ID/assets?name=$(printf '%s' "$asset_name" | jq -sRr @uri)"
curl -sS -X POST "${auth[@]}" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @"$ASSET_PATH" \
  "$upload_url" >/dev/null

echo "[gh] ok: release=$TAG asset=$asset_name"
'''
              }
            }

            bat """
              @echo on
              docker run --rm -v "%cd%":/w -w /w alpine:3.20 sh -lc "set -e; apk add --no-cache bash curl jq; tr -d '\\r' < scripts/upload_github_release.sh > /tmp/gh_release.sh; chmod +x /tmp/gh_release.sh; GITHUB_TOKEN=%GH_PAT% GITHUB_REPO=C14-2025/API-BolaMarcada TAG=%CI_TAG% ASSET_PATH=%IMAGE_TAR% bash /tmp/gh_release.sh"
            """
          }
        }
      }
    }

    stage('Notificação') {
      steps {
        // Não quebrar o pipeline se o SMTP falhar
        catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
          script {
            def testsStatus   = fileExists('status_tests.txt')   ? readFile('status_tests.txt').trim()   : 'FAILURE'
            def packageStatus = fileExists('status_package.txt') ? readFile('status_package.txt').trim() : 'FAILURE'

            // garante o script de notificação caso não exista no repo
            if (!fileExists('scripts')) {
              bat 'mkdir scripts 2>nul'
            }
            if (!fileExists('scripts/notify_email.py')) {
              writeFile file: 'scripts/notify_email.py', text: '''
import os, smtplib, socket, ssl
from email.message import EmailMessage

to_email   = os.environ.get("TO_EMAIL", "")
from_email = os.environ.get("FROM_EMAIL", "ci@jenkins.local")
smtp_host  = os.environ.get("SMTP_SERVER", "smtp.mailtrap.io")
smtp_port  = int(os.environ.get("SMTP_PORT", "2525"))
smtp_user  = os.environ.get("SMTP_USERNAME", "")
smtp_pass  = os.environ.get("SMTP_PASSWORD", "")
tests      = os.environ.get("TESTS_STATUS", "UNKNOWN")
package    = os.environ.get("PACKAGE_STATUS", "UNKNOWN")
sha        = os.environ.get("GIT_SHA", "")
branch     = os.environ.get("GIT_BRANCH", "")
run_id     = os.environ.get("GITHUB_RUN_ID", "")
run_num    = os.environ.get("GITHUB_RUN_NUMBER", "")

body = f"""Pipeline Jenkins finalizado.

Branch: {branch}
Commit: {sha}

Testes:   {tests}
Empacote: {package}

Run ID: {run_id}
Run #:  {run_num}
Host:   {socket.gethostname()}
"""

msg = EmailMessage()
msg["Subject"] = f"[CI] {branch} @ {sha} — tests:{tests} pkg:{package}"
msg["From"] = from_email
msg["To"] = to_email
msg.set_content(body)

ctx = ssl.create_default_context()
with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as s:
    s.ehlo()
    try:
        s.starttls(context=ctx)
        s.ehlo()
    except Exception as e:
        print("WARN: STARTTLS não disponível ou falhou:", e)
    if smtp_user or smtp_pass:
        s.login(smtp_user, smtp_pass)
    s.send_message(msg)
print("Email enviado para", to_email)
'''.trim()
            }

            withCredentials([
              usernamePassword(credentialsId: 'mailtrap-smtp', usernameVariable: 'SMTP_USERNAME', passwordVariable: 'SMTP_PASSWORD'),
              string(credentialsId: 'EMAIL_TO', variable: 'TO_EMAIL')
            ]) {
              bat """
                @echo on
                docker run --rm ^
                  -e TO_EMAIL=%TO_EMAIL% ^
                  -e SMTP_SERVER=smtp.mailtrap.io ^
                  -e SMTP_PORT=2525 ^
                  -e FROM_EMAIL=ci@jenkins.local ^
                  -e SMTP_USERNAME=%SMTP_USERNAME% ^
                  -e SMTP_PASSWORD=%SMTP_PASSWORD% ^
                  -e TESTS_STATUS=${testsStatus} ^
                  -e PACKAGE_STATUS=${packageStatus} ^
                  -e GIT_SHA=%COMMIT% ^
                  -e GIT_BRANCH=%BRANCH% ^
                  -e GITHUB_RUN_ID=%BUILD_ID% ^
                  -e GITHUB_RUN_NUMBER=%BUILD_NUMBER% ^
                  -v "%cd%":/w -w /w python:3.12-alpine ^
                  sh -lc "apk add --no-cache ca-certificates && python scripts/notify_email.py"
              """
            }
          }
        }
      }
    }
  }

  post {
    always {
      echo "Pipeline finalizado."
    }
  }
}  