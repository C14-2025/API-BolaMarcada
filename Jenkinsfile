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
    PGPORT = '55432'

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
          env.COMMIT = sh(script: 'git rev-parse --short=8 HEAD', returnStdout: true).trim().readLines().last().trim()

          // branch robusto (evita HEAD em detached)
          def guess = env.BRANCH_NAME ?: env.GIT_BRANCH
          if (!guess || guess.trim() == 'HEAD') {
            def nameRev = sh(script: 'git name-rev --name-only HEAD', returnStdout: true).trim()
            guess = nameRev ?: 'unknown'
          }
          guess = guess.replaceFirst(/^origin\\//, '').replaceFirst(/^remotes\\/origin\\//, '')
          env.BRANCH = guess

          env.IMAGE     = "app:${env.COMMIT}"
          env.IMAGE_TAR = "image-${env.COMMIT}.tar"

          // TAG único por build
          env.CI_TAG = "ci-${env.BUILD_NUMBER}-${env.COMMIT}"

          echo "BRANCH=${env.BRANCH}  CI_TAG=${env.CI_TAG}  COMMIT=${env.COMMIT}"
        }
      }
    }

    stage('Build image') {
      steps {
        sh '''
          # Garante .dockerignore pra não mandar tarzão & cia pro build context
          cat > .dockerignore <<'EOF'
.git
__pycache__/
*.pyc
artifacts/
reports/
image-*.tar
${JUNIT_XML}
${COVERAGE_XML}
EOF

          echo "docker version"
          docker version
          docker build --pull -t "$IMAGE" -t app:latest .
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

                  // --- Network + DB
                  sh '''
                    set -eux
                    echo "rede dedicada"
                    docker network create ci_net || echo net exists

                    echo "sobe Postgres"
                    docker rm -f ci-db || true
                    docker run -d --name ci-db --network ci_net \
                      -e POSTGRES_USER="$PGUSER" -e POSTGRES_PASSWORD="$PGPASS" -e POSTGRES_DB="$PGDB" \
                      -p "$PGPORT":5432 postgres:17-alpine
                  '''

                  int waitRc = sh(returnStatus: true, script: '''
                    set -eux
                    docker run --rm --network ci_net \
                      -e PGUSER="$PGUSER" -e PGDB="$PGDB" -e PGPASSWORD="$PGPASS" \
                      postgres:17-alpine sh -lc '
                        i=0
                        until pg_isready -h ci-db -p 5432 -U "$PGUSER" -d "$PGDB"; do
                          i=$((i+1))
                          if [ $i -ge 60 ]; then
                            echo "ERRO: Postgres não ficou pronto em 60s"
                            exit 1
                          fi
                          sleep 1
                        done
                      '
                  ''')
                  if (waitRc != 0) {
                    sh 'echo "--- LOGS DO POSTGRES ---"; docker logs ci-db || true'
                    error("Banco não ficou pronto (rc=${waitRc})")
                  }

                  // --- Testes (compartilhando o MESMO volume do container do Jenkins)
                  int rc = sh(returnStatus: true, script: '''
                    set -eux
                    docker run --rm --network ci_net \
                      --volumes-from "$(hostname)" \
                      -w "$WORKSPACE" \
                      -e POSTGRES_SERVER="$PGHOST" -e POSTGRES_HOST="$PGHOST" \
                      -e POSTGRES_USER="$PGUSER" -e POSTGRES_PASSWORD="$PGPASS" -e POSTGRES_DB="$PGDB" \
                      -e DATABASE_URL="postgresql+psycopg2://$PGUSER:$PGPASS@$PGHOST:5432/$PGDB" \
                      -e SECRET_KEY="$SECRET_KEY" \
                      -e ACCESS_TOKEN_EXPIRE_MINUTES="$ACCESS_TOKEN_EXPIRE_MINUTES" \
                      -e JUNIT_XML="$JUNIT_XML" -e COVERAGE_XML="$COVERAGE_XML" \
                      "$IMAGE" sh -lc '
                        set -eux
                        python -m pip install --disable-pip-version-check -U pip
                        python -m pip install pytest pytest-cov
                        # já estamos no $WORKSPACE
                        pytest -vv tests \
                          --junit-xml="$JUNIT_XML" \
                          --cov=. \
                          --cov-report=xml:"$COVERAGE_XML"
                      '
                  ''')
                  if (rc == 0) {
                    writeFile file: 'status_tests.txt', text: 'SUCCESS'
                  } else {
                    writeFile file: 'status_tests.txt', text: 'FAILURE'
                    error("Testes falharam (rc=${rc})")
                  }
                }
              }
            }
          }
          post {
            always {
              junit allowEmptyResults: true, testResults: "${JUNIT_XML}"
              archiveArtifacts allowEmptyArchive: true, artifacts: "${JUNIT_XML}, ${COVERAGE_XML}"
              sh '''
                set +e
                docker rm -f ci-db >/dev/null 2>&1 || true
                docker network rm ci_net >/dev/null 2>&1 || true
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
                int rcPkg = sh(returnStatus: true, script: '''
                  set -eux
                  echo "salvando imagem"
                  docker save "$IMAGE" -o "$IMAGE_TAR"
                ''')
                if (rcPkg == 0) {
                  writeFile file: 'status_package.txt', text: 'SUCCESS'
                } else {
                  writeFile file: 'status_package.txt', text: 'FAILURE'
                  error("Empacotamento falhou (rc=${rcPkg})")
                }
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
        // <<< LIBERADO PARA QUALQUER BRANCH, basta o parâmetro estar true >>>
        expression { return params.ENABLE_GH_RELEASE as boolean }
      }
      steps {
        catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
          withCredentials([usernamePassword(credentialsId: 'github-pat', usernameVariable: 'GH_USER', passwordVariable: 'GH_PAT')]) {
            script {
              if (!fileExists('scripts')) { sh 'mkdir -p scripts' }
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

            // debug rápido do que vamos subir
            sh '''
              echo "[release] TAG=$CI_TAG"
              echo "[release] ASSET=$IMAGE_TAR"
              echo "[release] REPO=C14-2025/API-BolaMarcada"
            '''

            sh '''
              docker run --rm -v "$PWD":/w -w /w alpine:3.20 sh -lc "
                set -e
                apk add --no-cache bash curl jq
                tr -d '\\r' < scripts/upload_github_release.sh > /tmp/gh_release.sh
                chmod +x /tmp/gh_release.sh
                GITHUB_TOKEN=$GH_PAT GITHUB_REPO=C14-2025/API-BolaMarcada TAG=$CI_TAG ASSET_PATH=$IMAGE_TAR bash /tmp/gh_release.sh
              "
            '''
          }
        }
      }
    }

    stage('Debug workspace') {
      steps {
        sh '''
          echo "Caminho atual:"; pwd; echo
          echo "Conteúdo do diretório atual:"; ls -la; echo
          echo "Conteúdo recursivo:"; find . -maxdepth 3 -type f | sort
        '''
      }
    }

    stage('Notificação') {
      steps {
        // Não quebrar o pipeline se o SMTP falhar
        catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
          script {
            def testsStatus   = fileExists('status_tests.txt')   ? readFile('status_tests.txt').trim()   : 'FAILURE'
            def packageStatus = fileExists('status_package.txt') ? readFile('status_package.txt').trim() : 'FAILURE'

            withCredentials([
              usernamePassword(credentialsId: 'mailtrap-smtp', usernameVariable: 'SMTP_USERNAME', passwordVariable: 'SMTP_PASSWORD'),
              string(credentialsId: 'EMAIL_TO', variable: 'TO_EMAIL')
            ]) {
              withEnv(["TESTS_STATUS=${testsStatus}", "PACKAGE_STATUS=${packageStatus}"]) {
                sh '''
                  set -eu
                  docker run --rm \
                    -e TO_EMAIL="$TO_EMAIL" \
                    -e SMTP_SERVER="smtp.mailtrap.io" \
                    -e SMTP_PORT="2525" \
                    -e FROM_EMAIL="ci@jenkins.local" \
                    -e SMTP_USERNAME="$SMTP_USERNAME" \
                    -e SMTP_PASSWORD="$SMTP_PASSWORD" \
                    -e TESTS_STATUS="$TESTS_STATUS" \
                    -e PACKAGE_STATUS="$PACKAGE_STATUS" \
                    -e GIT_SHA="$COMMIT" \
                    -e GIT_BRANCH="$BRANCH" \
                    -e GITHUB_RUN_ID="$BUILD_ID" \
                    -e GITHUB_RUN_NUMBER="$BUILD_NUMBER" \
                    python:3.12-alpine sh -lc '
                      set -e
                      python3 - <<PY
import os, smtplib, socket, ssl
from email.message import EmailMessage
to_email   = os.environ.get("TO_EMAIL","")
from_email = os.environ.get("FROM_EMAIL","ci@jenkins.local")
smtp_host  = os.environ.get("SMTP_SERVER","smtp.mailtrap.io")
smtp_port  = int(os.environ.get("SMTP_PORT","2525"))
smtp_user  = os.environ.get("SMTP_USERNAME","")
smtp_pass  = os.environ.get("SMTP_PASSWORD","")
tests      = os.environ.get("TESTS_STATUS","UNKNOWN")
package    = os.environ.get("PACKAGE_STATUS","UNKNOWN")
sha        = os.environ.get("GIT_SHA","")
branch     = os.environ.get("GIT_BRANCH","")
run_id     = os.environ.get("GITHUB_RUN_ID","")
run_num    = os.environ.get("GITHUB_RUN_NUMBER","")
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
    try:
        s.starttls(context=ctx)
    except Exception:
        pass
    if smtp_user or smtp_pass:
        s.login(smtp_user, smtp_pass)
    s.send_message(msg)
print("Email enviado para", to_email)
PY
                    '
                '''
              }
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