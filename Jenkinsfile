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

                    rem -- espera Postgres via container Linux (evita loop batch + stdin)
                    docker run --rm --network ci_net postgres:17-alpine sh -lc "until pg_isready -h %PGHOST% -p 5432 -U %PGUSER% -d %PGDB%; do sleep 1; done"

                    rem -- roda pytest dentro da SUA imagem (garante pytest+pytest-cov)
                    docker run --rm --network ci_net ^
                      -e POSTGRES_SERVER=%PGHOST% -e POSTGRES_HOST=%PGHOST% ^
                      -e POSTGRES_USER=%PGUSER% -e POSTGRES_PASSWORD=%PGPASS% -e POSTGRES_DB=%PGDB% ^
                      -e DATABASE_URL=postgresql+psycopg2://%PGUSER%:%PGPASS%@%PGHOST%:5432/%PGDB% ^
                      -e SECRET_KEY=%SECRET_KEY% ^
                      -e ACCESS_TOKEN_EXPIRE_MINUTES=%ACCESS_TOKEN_EXPIRE_MINUTES% ^
                      -v "%cd%":/workspace -w /app %IMAGE% ^
                      sh -lc "python -m pip install -q --disable-pip-version-check pytest pytest-cov && pytest -q --junit-xml=/workspace/%JUNIT_XML% --cov=. --cov-report=xml:/workspace/%COVERAGE_XML%"

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
                docker rm -f ci-db 2>nul
                docker network rm ci_net 2>nul
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
          expression { return params.ENABLE_GH_RELEASE }
          expression { return env.BRANCH == 'feat/CICD/Jenkins' }
        }
      }
      steps {
        catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
          withCredentials([usernamePassword(credentialsId: 'github-pat', usernameVariable: 'GH_USER', passwordVariable: 'GH_PAT')]) {
            bat """
              @echo on
              docker run --rm -v "%cd%":/w -w /w alpine:3.20 sh -lc "set -e; apk add --no-cache bash curl jq; if [ -f scripts/upload_github_release.sh ]; then tr -d '\\r' < scripts/upload_github_release.sh > /tmp/gh_release.sh; chmod +x /tmp/gh_release.sh; GITHUB_TOKEN=%GH_PAT% GITHUB_REPO=C14-2025/API-BolaMarcada TAG=ci-%COMMIT% ASSET_PATH=%IMAGE_TAR% bash /tmp/gh_release.sh; else echo 'scripts/upload_github_release.sh nao encontrado, pulando.'; fi"
            """
          }
        }
      }
    }

    stage('Notificação') {
      steps {
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

  post {
    always {
      echo "Pipeline finalizado."
    }
  }
}
