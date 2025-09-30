// Jenkinsfile (Scripted) — testes via docker-compose + build + notify (Mailtrap)
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
    // STAGE: Tests
    //////////////////////////
    stage('Tests (docker-compose)') {
      echo "Usando secret file (.env) e docker-compose para rodar migrations + testes..."
      withCredentials([file(credentialsId: 'env-file', variable: 'ENV_FILE')]) {
        if (isUnix()) {
          sh '''
            # copia secret file para .env no workspace
            cp "$ENV_FILE" .env
            mkdir -p reports

            # tenta remover containers órfãos que causam conflito (silencioso)
            docker rm -f postgres_bolamarcada || true
            docker rm -f fastapi-ci-db-1 || true

            # garante estado limpo e sobe o DB
            docker-compose down --remove-orphans || true
            docker-compose pull || true
            docker-compose up -d db

            # espera simples para o DB inicializar; aumentar se necessário
            sleep 6

            # garantir esquema: aplica migrations antes dos testes
            docker-compose run --rm api sh -c "alembic upgrade head || true"

            # roda pytest dentro do container 'api' usando sh -c (gera reports/junit.xml)
            docker-compose run --rm api sh -c "python -m pytest -q --junitxml=reports/junit.xml"

            # baixa e limpa
            docker-compose down
          '''
          junit 'reports/junit.xml'
          archiveArtifacts artifacts: 'reports/**, dist/**', allowEmptyArchive: true
        } else {
          // Windows agent flow (não usar %COMSPEC% para comando do container)
          bat """
            @echo off
            rem copy secret file into workspace
            copy /Y "%ENV_FILE%" .env >nul
            if not exist reports mkdir reports

            rem cleanup potential conflicting containers
            docker rm -f postgres_bolamarcada 2>nul || echo no_container
            docker rm -f fastapi-ci-db-1 2>nul || echo no_container

            docker-compose down --remove-orphans || exit /b 0
            docker-compose pull || exit /b 0
            docker-compose up -d db
            timeout /t 6 /nobreak >nul

            rem apply migrations inside the api container (ensures schema)
            docker-compose run --rm api sh -c "alembic upgrade head || true"

            rem run pytest inside container using sh (image is linux)
            docker-compose run --rm api sh -c "python -m pytest -q --junitxml=reports\\junit.xml"

            docker-compose down
          """
          junit 'reports/junit.xml'
          archiveArtifacts artifacts: 'reports/**, dist/**', allowEmptyArchive: true
        }
      } // withCredentials env-file end
      echo "Stage Tests finalizada."
    }

    //////////////////////////
    // STAGE: Build / Package
    //////////////////////////
    stage('Build (package)') {
      echo "Empacotando artefatos (tentando build dentro do container 'api' ou via docker build)..."
      if (isUnix()) {
        sh '''
          # se existir pyproject.toml, usar build; caso contrário, fallback para docker build
          if [ -f pyproject.toml ]; then
            docker-compose run --rm api sh -c "python -m pip install --upgrade pip build || true"
            docker-compose run --rm api sh -c "python -m build || true"
          else
            docker build -t api-bolamarcada:ci .
          fi
        '''
      } else {
        bat """
          @echo off
          if exist pyproject.toml (
            docker-compose run --rm api sh -c "python -m pip install --upgrade pip build" || exit /b 0
            docker-compose run --rm api sh -c "python -m build" || exit /b 0
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
