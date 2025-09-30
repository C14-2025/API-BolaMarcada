// Jenkinsfile (Scripted) — docker-compose tests + robust docker cp + build + notify (Mailtrap)
node {
  // ajuste se necessário
  def WIN_PY = 'C:\\\\Users\\\\jmxd\\\\AppData\\\\Local\\\\Programs\\\\Python\\\\Python313\\\\python.exe'
  def SMTP_HOST = 'sandbox.smtp.mailtrap.io'
  def SMTP_PORT = '2525'
  def buildStatus = 'SUCCESS'

  try {
    stage('Checkout') {
      checkout scm
      echo "Checkout realizado."
    }

    stage('Prepare workspace') {
      // garante diretório reports no workspace
      if (isUnix()) {
        sh 'mkdir -p reports logs || true'
      } else {
        bat 'if not exist reports mkdir reports'
        bat 'if not exist logs mkdir logs'
      }
    }

    stage('Tests (docker-compose + reliable docker cp)') {
      echo "Usando secret file (.env) e docker-compose para rodar migrations + testes (copy fallback)..."
      withCredentials([file(credentialsId: 'env-file', variable: 'ENV_FILE')]) {
        if (isUnix()) {
          sh '''
            set -e
            cp "$ENV_FILE" .env
            mkdir -p reports logs

            # cleanup gentle
            docker rm -f jenkins_api_test 2>/dev/null || true
            docker-compose down --remove-orphans || true
            docker-compose pull || true

            # sobe apenas DB
            docker-compose up -d db
            echo "esperando DB inicializar..."
            sleep 8

            # build imagem (opcional); nome consistente
            docker build -t api-bolamarcada:jenkins . > logs/build_image.log 2>&1 || true

            # roda testes via docker-compose RUN mas sem --rm para podermos copiar artefatos
            docker-compose run --no-deps --name jenkins_api_test api sh -c "python -m pytest -q --junitxml=/app/reports/junit.xml" || true

            # traz o relatório do container para o host workspace
            echo "tentando docker cp jenkins_api_test:/app/reports -> ./reports"
            docker cp jenkins_api_test:/app/reports ./reports 2>/dev/null || true

            # salva logs do container
            docker logs jenkins_api_test --tail 500 > logs/pytest_fallback.out 2>&1 || true

            # cleanup
            docker rm -f jenkins_api_test 2>/dev/null || true
            docker-compose down || true
          '''
          // Agora o junit step tenta ler o arquivo do workspace
          junit 'reports/junit.xml'
          archiveArtifacts artifacts: 'reports/**, dist/**', allowEmptyArchive: true
        } else {
          bat """
            @echo off
            copy /Y "%ENV_FILE%" .env >nul
            if not exist reports mkdir reports
            if not exist logs mkdir logs

            rem cleanup
            docker rm -f jenkins_api_test 2>nul || echo no_container

            docker-compose down --remove-orphans || exit /b 0
            docker-compose pull || exit /b 0
            docker-compose up -d db
            echo esperando DB inicializar...
            timeout /t 8 /nobreak >nul

            rem build image (log)
            docker build -t api-bolamarcada:jenkins . > logs\\build_image.log 2>&1 || echo build_failed

            rem run tests (image is linux-based; use sh -c). Note: do NOT pass --rm so we can docker cp afterwards
            docker-compose run --no-deps --name jenkins_api_test api sh -c "python -m pytest -q --junitxml=/app/reports/junit.xml" || echo pytest_failed

            rem copy reports from container to workspace
            echo Tentando docker cp...
            docker cp jenkins_api_test:/app/reports .\\reports 2>nul || echo DOCKER_CP_FAILED

            rem save container logs
            docker logs jenkins_api_test --tail 500 > logs\\pytest_fallback.out 2>&1 || echo LOG_FAIL

            rem cleanup
            docker rm -f jenkins_api_test 2>nul || echo no_container
            docker-compose down || exit /b 0
          """
          // junit step reads from workspace
          junit 'reports/junit.xml'
          archiveArtifacts artifacts: 'reports/**, dist/**', allowEmptyArchive: true
        }
      } // withCredentials
      echo "Stage Tests finalizada."
    }

    stage('Build (package)') {
      echo "Empacotando artefatos..."
      if (isUnix()) {
        sh '''
          if [ -f pyproject.toml ]; then
            docker-compose run --rm api sh -c "python -m pip install --upgrade pip build || true"
            docker-compose run --rm api sh -c "python -m build || true"
          else
            docker build -t api-bolamarcada:ci . > logs/build_package.log 2>&1 || true
          fi
        '''
      } else {
        bat """
          @echo off
          if exist pyproject.toml (
            docker-compose run --rm api sh -c "python -m pip install --upgrade pip build" || echo build_fail
            docker-compose run --rm api sh -c "python -m build" || echo build_fail
          ) else (
            docker build -t api-bolamarcada:ci . > logs\\build_package.log 2>&1 || echo build_fail
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
    // Notify (sempre)
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

    // cleanup .env
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
