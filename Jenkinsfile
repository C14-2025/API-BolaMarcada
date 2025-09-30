// Jenkinsfile completo — docker-compose tests + fallback docker cp + build + notify (Mailtrap)
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

    stage('Tests (docker-compose + fallback)') {
      echo "Usando secret file (.env) e docker-compose para rodar migrations + testes (com fallback docker cp)..."
      withCredentials([file(credentialsId: 'env-file', variable: 'ENV_FILE')]) {
        if (isUnix()) {
          sh '''
            set -e
            cp "$ENV_FILE" .env
            mkdir -p reports logs

            # cleanup
            docker rm -f postgres_bolamarcada || true
            docker rm -f jenkins_api_test || true

            docker-compose down --remove-orphans || true
            docker-compose pull || true
            docker-compose up -d db
            sleep 15

            # tentativa normal (sem TTY)
            echo "[normal run] docker-compose run --rm -T api pytest -> logs/pytest.out"
            docker-compose run --rm -T api sh -c "alembic upgrade head || true; python -m pytest -q --junitxml=/app/reports/junit.xml" > logs/pytest.out 2>&1 || true

            echo "=> Verificando se reports/junit.xml existe no HOST"
            if [ -f reports/junit.xml ]; then
              echo "FOUND: reports/junit.xml"
            else
              echo "NOT FOUND: reports/junit.xml -> iniciando FALLBACK (build+docker create/start+docker cp)"
              # build image explicitly
              docker build -t api-bolamarcada:jenkins . > logs/build_image.log 2>&1 || true

              # create and run a container named jenkins_api_test with host bind to workspace
              CID=$(docker create --name jenkins_api_test -v "$(pwd)":/app -w /app api-bolamarcada:jenkins sh -c "alembic upgrade head || true; python -m pytest -q --junitxml=/app/reports/junit.xml") || CID=""
              echo "Created container: ${CID}"
              if [ -n "${CID}" ]; then
                docker start -a "${CID}" > logs/pytest_fallback.out 2>&1 || true
                echo "Attempt docker cp from container to host (reports)..."
                docker cp "${CID}":/app/reports ./reports 2>/dev/null || echo "docker cp failed (attempting to inspect container files)"
                echo "Container logs (tail 200):"
                docker logs "${CID}" --tail 200 || true
                docker rm -f "${CID}" || true
              else
                echo "Failed to create fallback container."
              fi
            fi

            echo "=== Listing host workspace and reports ==="
            ls -la .
            ls -la reports || true

            echo "=== HEAD of logs/pytest.out ==="
            head -n 200 logs/pytest.out || true
            echo "=== HEAD of logs/pytest_fallback.out ==="
            head -n 200 logs/pytest_fallback.out || true

            docker-compose down || true
          '''
        } else {
          bat """
            @echo off
            copy /Y "%ENV_FILE%" .env >nul
            if not exist reports mkdir reports
            if not exist logs mkdir logs

            docker rm -f postgres_bolamarcada 2>nul || echo no_container
            docker rm -f jenkins_api_test 2>nul || echo no_container

            docker-compose down --remove-orphans || exit /b 0
            docker-compose pull || exit /b 0
            docker-compose up -d db
            timeout /t 15 /nobreak >nul

            echo [normal run] docker-compose run --rm -T api pytest -> logs\\pytest.out
            docker-compose run --rm -T api sh -c "alembic upgrade head || true; python -m pytest -q --junitxml=/app/reports/junit.xml" > logs\\pytest.out 2>&1 || echo TEST_RUN_FAILED

            echo Verificando reports\\junit.xml no HOST
            if exist reports\\junit.xml (
              echo FOUND: reports\\junit.xml
            ) else (
              echo NOT FOUND: reports\\junit.xml -> iniciando FALLBACK (build + create + start + docker cp)
              docker build -t api-bolamarcada:jenkins . > logs\\build_image.log 2>&1 || echo BUILD_FAILED
              REM create container (do not --rm so we can docker cp)
              for /f "delims=" %%I in ('docker create --name jenkins_api_test -v "%cd%":/app -w /app api-bolamarcada:jenkins sh -c "alembic upgrade head || true; python -m pytest -q --junitxml=/app/reports/junit.xml"') do set CID=%%I
              echo Created container %CID%
              if not "%CID%"=="" (
                docker start -a %CID% > logs\\pytest_fallback.out 2>&1 || echo START_FAILED
                echo Tentando docker cp...
                docker cp %CID%:/app/reports ./reports 2>nul || echo DOCKER_CP_FAILED
                docker logs %CID% --tail 200 || echo LOGS_FAILED
                docker rm -f %CID% || echo RM_FAILED
              ) else (
                echo Falha ao criar container de fallback
              )
            )

            echo ==== dir workspace ====
            dir /B
            dir reports || echo NO_REPORTS_DIR

            echo ==== show logs heads ====
            more logs\\pytest.out
            if exist logs\\pytest_fallback.out more logs\\pytest_fallback.out

            docker-compose down || echo down_failed
          """
        }
        // publish junit if exists and archive logs
        junit 'reports/junit.xml'
        archiveArtifacts artifacts: 'logs/**, reports/**, dist/**', allowEmptyArchive: true
      } // withCredentials
    } // stage Tests

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
      if (isUnix()) { sh 'if [ -f .env ]; then rm -f .env; fi || true' }
      else { bat 'if exist .env del /Q .env' }
    } catch (cleanupErr) {
      echo "Aviso: falha ao remover .env: ${cleanupErr}"
    }

    echo "Fim do pipeline. Resultado: ${buildStatus}"
  }
}
