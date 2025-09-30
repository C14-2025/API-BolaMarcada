// Jenkinsfile (Scripted) — testes via docker-compose + build + notify (mailto via Mailtrap)
// Requisitos (já configurados):
// - Secret file com ID 'env-file' (contendo .env)
// - Credentials username+password com ID 'mailtrap-smtp'
// - Secret text with ID 'EMAIL_TO' (ou string credential) - destinatário do e-mail
// - scripts/notify.py presente no repo (usa SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_TO)
// - docker & docker-compose disponíveis no agente Jenkins

node {
  // caminho absoluto do python no Windows (opcional — não necessário se o envío for feito em container)
  def WIN_PY = 'C:\\\\Users\\\\jmxd\\\\AppData\\\\Local\\\\Programs\\\\Python\\\\Python313\\\\python.exe'
  // Mailtrap host/port (não secretos)
  def SMTP_HOST = 'sandbox.smtp.mailtrap.io'
  def SMTP_PORT = '2525'

  def buildStatus = 'SUCCESS'

  try {
    stage('Checkout') {
      checkout scm
      echo "Checkout realizado."
    }

    stage('Tests (docker-compose)') {
      echo "Usando secret file (.env) e docker-compose para rodar testes..."
      // Espera que exista um credential Secret file com ID 'env-file'
      withCredentials([file(credentialsId: 'env-file', variable: 'ENV_FILE')]) {
        if (isUnix()) {
          sh '''
            # copia secret file para .env (workspace)
            cp "$ENV_FILE" .env

            # debug
            docker --version || true
            docker-compose --version || docker compose version || true

            # cleanup e start db
            docker-compose down --remove-orphans || true
            docker-compose pull || true
            docker-compose up -d db

            # aguarda o DB inicializar (ajuste se necessário)
            sleep 5

            # opcional: rodar migrações
            # docker-compose run --rm api alembic upgrade head

            # roda testes dentro do container 'api' e gera junit
            docker-compose run --rm api pytest -q --junitxml=reports/junit.xml

            # baixa e limpa
            docker-compose down
          '''
          // publica relatório e artefatos
          junit 'reports/junit.xml'
          archiveArtifacts artifacts: 'reports/**, dist/**', allowEmptyArchive: true
        } else {
          bat """
            @echo off
            REM copia secret file para .env no workspace
            copy /Y "%ENV_FILE%" .env >nul

            REM debug
            docker --version || echo docker nao encontrado
            docker-compose --version || docker compose version || echo docker-compose nao encontrado

            REM cleanup e start db
            docker-compose down --remove-orphans || exit /b 0
            docker-compose pull || exit /b 0
            docker-compose up -d db
            timeout /t 5 /nobreak >nul

            REM opcional: rodar migrações
            REM docker-compose run --rm api alembic upgrade head

            REM roda pytest dentro do container 'api' (gera reports/junit.xml)
            docker-compose run --rm api %COMSPEC% /C "python -m pytest -q --junitxml=reports\\junit.xml"

            docker-compose down
          """
          junit 'reports/junit.xml'
          archiveArtifacts artifacts: 'reports/**, dist/**', allowEmptyArchive: true
        }
      }
      echo "Stage Tests finalizada."
    }

    stage('Build (package)') {
      echo "Empacotando artefatos (executa build dentro do container 'api' se aplicável)..."
      // Tenta criar pacote Python (se houver pyproject) dentro do container api, gerando dist/
      if (isUnix()) {
        sh '''
          # se você usa pyproject.toml, gerar wheel/sdist dentro do container
          if [ -f pyproject.toml ]; then
            docker-compose run --rm api python -m pip install --upgrade pip build || true
            docker-compose run --rm api python -m build || true
          else
            # fallback: build via docker
            docker build -t api-bolamarcada:ci .
          fi
        '''
      } else {
        bat """
          @echo off
          if exist pyproject.toml (
            docker-compose run --rm api %COMSPEC% /C "${WIN_PY} -m pip install --upgrade pip build" || exit /b 0
            docker-compose run --rm api %COMSPEC% /C "${WIN_PY} -m build" || exit /b 0
          ) else (
            docker build -t api-bolamarcada:ci .
          )
        """
      }
      // arquiva dist (pode estar no host via volume .:/app)
      archiveArtifacts artifacts: 'dist/**', allowEmptyArchive: true
      echo "Stage Build finalizada."
    }

  } catch (err) {
    // marca falha e repassa
    buildStatus = 'FAILURE'
    currentBuild.result = 'FAILURE'
    echo "Pipeline falhou: ${err}"
    throw err
  } finally {
    // --- NOTIFY (sempre executa) ---
    echo "Enviando notificação de fim de pipeline (status: ${buildStatus})..."

    // tentativa robusta de enviar email: injeta credenciais e chama scripts/notify.py
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
            # chama o script de notificação (usa o python do agente)
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
            REM chama o script de notificação usando Python absoluto configurado (WIN_PY)
            "${WIN_PY}" scripts\\notify.py --status "${buildStatus}" --run-id "${env.BUILD_ID}" --repo "${env.GIT_URL}" --branch "${env.GIT_BRANCH ?: 'main'}" || echo notify_failed
          """
        }
      }
      echo "Notificação enviada (ou tentativa concluída)."
    } catch (notifErr) {
      echo "Falha ao enviar notificação: ${notifErr}"
    }

    // cleanup: remove .env gerado (se existir) para não deixar segredos em workspace
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
