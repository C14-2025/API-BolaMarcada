// Jenkinsfile (Scripted) — testes via docker-compose + build + notify (Mailtrap)
// Requisitos no Jenkins:
// - Secret file com ID 'env-file' (contendo .env)
// - Credentials username+password com ID 'mailtrap-smtp'
// - Secret text/string credential with ID 'EMAIL_TO' (destinatário)
// - scripts/notify.py presente no repo
// - docker & docker-compose disponíveis no agente Jenkins

node {
  def WIN_PY = 'C:\\\\Users\\\\jmxd\\\\AppData\\\\Local\\\\Programs\\\\Python\\\\Python313\\\\python.exe'
  def SMTP_HOST = 'sandbox.smtp.mailtrap.io'
  def SMTP_PORT = '2525'
  def buildStatus = 'SUCCESS'

  try {
    stage('Checkout') {
      checkout scm
      echo "Checkout realizado."
    }

    stage('Tests (docker-compose)') {
      echo "Usando secret file (.env) e docker-compose para rodar migrations + testes..."
      withCredentials([file(credentialsId: 'env-file', variable: 'ENV_FILE')]) {
        if (isUnix()) {
          sh '''
            set -e
            cp "$ENV_FILE" .env
            mkdir -p reports

            # cleanup containers that may conflict
            docker rm -f postgres_bolamarcada || true
            docker rm -f fastapi-ci-db-1 || true

            docker-compose down --remove-orphans || true
            docker-compose pull || true
            docker-compose up -d db

            # espera mais tempo para o DB inicializar (aumente se necessário)
            sleep 10

            # aplica migrations
            docker-compose run --rm -T api sh -c "alembic upgrade head || true"

            # roda pytest dentro do container (sem TTY)
            docker-compose run --rm -T api sh -c "python -m pytest -q --junitxml=reports/junit.xml"

            # mostra se o relatório foi gerado (ajuda debug no console)
            echo "=== reports files (UNIX) ==="
            ls -la reports || true
            if [ -f reports/junit.xml ]; then
              echo "---- head of reports/junit.xml ----"
              head -n 40 reports/junit.xml || true
            else
              echo "No junit.xml found"
            fi

            docker-compose down
          '''
          junit 'reports/junit.xml'
          archiveArtifacts artifacts: 'reports/**, dist/**', allowEmptyArchive: true
        } else {
          // Windows agent flow
          bat """
            @echo off
            setlocal enabledelayedexpansion
            copy /Y "%ENV_FILE%" .env >nul
            if not exist reports mkdir reports

            docker rm -f postgres_bolamarcada 2>nul || echo no_container
            docker rm -f fastapi-ci-db-1 2>nul || echo no_container

            docker-compose down --remove-orphans || exit /b 0
            docker-compose pull || exit /b 0
            docker-compose up -d db
            timeout /t 10 /nobreak >nul

            rem apply migrations inside container (no TTY)
            docker-compose run --rm -T api sh -c "alembic upgrade head || true"

            rem run pytest inside container using sh (image is linux) without TTY
            docker-compose run --rm -T api sh -c "python -m pytest -q --junitxml=reports\\junit.xml"

            echo === reports files (WINDOWS) ===
            if exist reports (
              dir /B reports
              type reports\\junit.xml | more
            ) else (
              echo No reports folder found
            )

            docker-compose down
          """
          junit 'reports/junit.xml'
          archiveArtifacts artifacts: 'reports/**, dist/**', allowEmptyArchive: true
        }
      }
      echo "Stage Tests finalizada."
    }

    stage('Build (package)') {
      echo "Empacotando artefatos..."
      if (isUnix()) {
        sh '''
          if [ -f pyproject.toml ]; then
            docker-compose run --rm -T api sh -c "python -m pip install --upgrade pip build || true"
            docker-compose run --rm -T api sh -c "python -m build || true"
          else
            docker build -t api-bolamarcada:ci .
          fi
        '''
      } else {
        bat """
          @echo off
          if exist pyproject.toml (
            docker-compose run --rm -T api sh -c "python -m pip install --upgrade pip build" || exit /b 0
            docker-compose run --rm -T api sh -c "python -m build" || exit /b 0
          ) else (
            docker build -t api-bolamarcada:ci .
          )
        """
      }
      archiveArtifacts artifacts: 'dist/**', allowEmptyArchive: true
      echo "Stage Build finalizada."
    }

  } catch (err) {
    buildStatus = 'FAILURE'
    currentBuild.result = 'FAILURE'
    echo "Pipeline falhou: ${err}"
    throw err
  } finally {
    echo "Enviando notificação de fim de pipeline (status: ${buildStatus})..."
    try {
      withCredentials([
        usernamePassword(credentialsId: 'mailtrap-smtp', usernameVariable: 'SMTP_USER', passwordVariable: 'SMTP_PASS'),
        string(credentialsId: 'EMAIL_TO', variable: 'EMAIL_TO')
      ]) {
        if (isUnix()) {
          sh """
            export SMTP_HOST=${SMTP_HOST}
            export SMTP_PORT=${SMTP_PORT}
            export SMTP_USER=${SMTP_USER}
            export SMTP_PASS=${SMTP_PASS}
            export EMAIL_TO=${EMAIL_TO}
            python3 scripts/notify.py --status "${buildStatus}" --run-id "${env.BUILD_ID}" --repo "${env.GIT_URL}" --branch "${env.GIT_BRANCH ?: 'main'}" || echo "notify script returned non-zero"
          """
        } else {
          bat """
            @echo off
            set SMTP_HOST=${SMTP_HOST}
            set SMTP_PORT=${SMTP_PORT}
            set SMTP_USER=%SMTP_USER%
            set SMTP_PASS=%SMTP_PASS%
            set EMAIL_TO=%EMAIL_TO%
            "${WIN_PY}" scripts\\notify.py --status "${buildStatus}" --run-id "${env.BUILD_ID}" --repo "${env.GIT_URL}" --branch "${env.GIT_BRANCH ?: 'main'}" || echo notify_failed
          """
        }
      }
      echo "Notificação enviada (ou tentativa concluída)."
    } catch (notifErr) {
      echo "Falha ao enviar notificação: ${notifErr}"
    }

    try {
      if (isUnix()) {
        sh 'if [ -f .env ]; then rm -f .env; fi || true'
      } else {
        bat 'if exist .env del /Q .env'
      }
    } catch (cleanupErr) {
      echo "Aviso: falha ao remover .env: ${cleanupErr}"
    }

    echo "Fim do pipeline. Resultado: ${buildStatus}"
  }
}
