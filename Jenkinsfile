// Jenkinsfile (Scripted) — docker-compose tests + build + notify (Mailtrap)
// Requisitos no Jenkins:
// - Secret file com ID 'env-file' (contendo .env)
// - Credentials username+password com ID 'mailtrap-smtp'
// - Secret text/string credential with ID 'EMAIL_TO' (destinatário)
// - scripts/notify.py presente no repo (usa SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_TO)
// - docker & docker-compose disponíveis no agente Jenkins

node {
  // caminho absoluto do python no Windows (ajuste se necessário)
  def WIN_PY = 'C:\\\\Users\\\\jmxd\\\\AppData\\\\Local\\\\Programs\\\\Python\\\\Python313\\\\python.exe'

  // Mailtrap host/port (padrões)
  def SMTP_HOST = 'sandbox.smtp.mailtrap.io'
  def SMTP_PORT = '2525'

  def buildStatus = 'SUCCESS'

  try {
    stage('Checkout') {
      checkout scm
      echo "Checkout realizado."
    }

    //////////////////////////
    // STAGE: Tests (DIAGNOSTIC)
    //////////////////////////
    stage('Tests (docker-compose)') {
      echo "Usando secret file (.env) e docker-compose — modo DIAGNÓSTICO (mais logs)..."
      withCredentials([file(credentialsId: 'env-file', variable: 'ENV_FILE')]) {
        if (isUnix()) {
          sh '''
            set -e
            echo "=== TEST DIAGNOSTIC START (UNIX) ==="
            cp "$ENV_FILE" .env
            mkdir -p reports logs

            # cleanup containers that may conflict
            docker rm -f postgres_bolamarcada || true
            docker rm -f fastapi-ci-db-1 || true

            docker-compose down --remove-orphans || true
            docker-compose pull || true

            echo "[docker-compose up db]"
            docker-compose up -d db

            # espera maior para postgres inicializar (ajuste se necessário)
            sleep 15

            echo "[docker-compose ps -a]"
            docker-compose ps -a

            echo "[apply alembic -> logs/alembic.log]"
            docker-compose run --rm -T api sh -c "alembic upgrade head" > logs/alembic.log 2>&1 || echo "alembic exit=$?"

            echo "[run pytest -> logs/pytest.out + reports/junit.xml]"
            docker-compose run --rm -T api sh -c "python -m pytest -vv --maxfail=1 --disable-warnings --junitxml=/app/reports/junit.xml" > logs/pytest.out 2>&1 || echo "pytest exit=$?"

            echo "=== listing container /app (inside container mount) ==="
            docker-compose run --rm -T api sh -c "ls -la /app || true; stat /app/reports || true" > logs/container_fs.log 2>&1 || true

            echo "=== docker-compose logs api -> logs/container_api.log ==="
            docker-compose logs api > logs/container_api.log 2>&1 || true

            echo "=== show logs summary (head) ==="
            echo "---- ALEMBIC LOG ----"
            head -n 120 logs/alembic.log || true
            echo "---- PYTEST LOG ----"
            head -n 200 logs/pytest.out || true
            echo "---- CONTAINER FS ----"
            head -n 200 logs/container_fs.log || true
            echo "---- DOCKER-COMPOSE LOGS (api) ----"
            tail -n 200 logs/container_api.log || true

            echo "=== workspace listing (host) ==="
            ls -la . || true
            ls -la reports || true

            echo "=== content of reports/junit.xml (if exists) ==="
            if [ -f reports/junit.xml ]; then
              head -n 80 reports/junit.xml || true
            else
              echo "NO reports/junit.xml ON HOST WORKSPACE"
            fi

            echo "=== stopping/cleanup ==="
            docker-compose down || true
            echo "=== TEST DIAGNOSTIC END ==="
          '''
          // publish junit (se existir) e logs
          junit 'reports/junit.xml'
          archiveArtifacts artifacts: 'logs/**, reports/**, dist/**', allowEmptyArchive: true
        } else {
          // Windows agent flow (bat)
          bat """
            @echo off
            echo === TEST DIAGNOSTIC START (WINDOWS) ===
            copy /Y "%ENV_FILE%" .env >nul
            if not exist reports mkdir reports
            if not exist logs mkdir logs

            docker rm -f postgres_bolamarcada 2>nul || echo no_container
            docker rm -f fastapi-ci-db-1 2>nul || echo no_container

            docker-compose down --remove-orphans || exit /b 0
            docker-compose pull || exit /b 0

            echo [docker-compose up db]
            docker-compose up -d db
            timeout /t 15 /nobreak >nul

            echo [docker-compose ps -a]
            docker-compose ps -a

            echo [apply alembic -> logs\\alembic.log]
            docker-compose run --rm -T api sh -c "alembic upgrade head" > logs\\alembic.log 2>&1 || echo ALEMBIC_EXIT=%ERRORLEVEL%

            echo [run pytest -> logs\\pytest.out + reports\\junit.xml]
            docker-compose run --rm -T api sh -c "python -m pytest -vv --maxfail=1 --disable-warnings --junitxml=/app/reports/junit.xml" > logs\\pytest.out 2>&1 || echo PYTEST_EXIT=%ERRORLEVEL%

            echo === copy container fs listing ===
            docker-compose run --rm -T api sh -c "ls -la /app || true; stat /app/reports || true" > logs\\container_fs.log 2>&1 || echo FSLOG_EXIT=%ERRORLEVEL%

            echo === copy docker-compose logs api ===
            docker-compose logs api > logs\\container_api.log 2>&1 || echo LOGS_EXIT=%ERRORLEVEL%

            echo === show logs summary (head) ===
            echo ---- ALEMBIC LOG ----
            type logs\\alembic.log | more
            echo ---- PYTEST LOG ----
            type logs\\pytest.out | more
            echo ---- CONTAINER FS ----
            type logs\\container_fs.log | more
            echo ---- DOCKER-COMPOSE LOGS (api) ----
            more logs\\container_api.log

            echo === workspace listing (host) ===
            dir /B
            dir reports || echo NO_REPORTS_DIR

            if exist reports\\junit.xml (
              echo ==== JUNIT (head 80) ====
              more reports\\junit.xml
            ) else (
              echo NO reports\\junit.xml ON HOST WORKSPACE
            )

            docker-compose down || echo down_failed
            echo === TEST DIAGNOSTIC END ===
          """
          junit 'reports/junit.xml'
          archiveArtifacts artifacts: 'logs/**, reports/**, dist/**', allowEmptyArchive: true
        }
      } // withCredentials
      echo "Stage Tests (diagnostic) finalizada."
    }

    //////////////////////////
    // STAGE: Build / Package
    //////////////////////////
    stage('Build (package)') {
      echo "Empacotando artefatos (tentando build dentro do container 'api' ou via docker build)..."
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
    //////////////////////////
    // STAGE: Notify (always runs)
    //////////////////////////
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

    // cleanup: remove .env gerado
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
