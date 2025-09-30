// Jenkinsfile (Scripted) — compatível com agentes Unix e Windows
node {
  try {
    stage('Checkout') {
      checkout scm
      echo "Checkout realizado."
    }

    stage('Tests') {
      echo "Instalando dependências e rodando testes (pytest)..."
      if (isUnix()) {
        // Unix / Linux
        sh '''
          python3 -m pip install --upgrade pip || true
          if [ -f requirements.txt ]; then pip3 install -r requirements.txt; fi
          pytest -q
        '''
      } else {
        // Windows
        bat """
          @echo off
          python -m pip install --upgrade pip
          if exist requirements.txt (
             python -m pip install -r requirements.txt
          )
          pytest -q
        """
      }
      echo "Testes finalizados (ver logs acima)."
    }

    stage('Build') {
      echo "Empacotamento / Build (ajuste conforme necessário)..."
      if (isUnix()) {
        sh '''
          if [ -f pyproject.toml ]; then
            python3 -m pip install --upgrade pip build || true
            python3 -m build || true
          else
            echo "Sem pyproject.toml — pulando build python."
          fi
        '''
      } else {
        bat """
          @echo off
          if exist pyproject.toml (
            python -m pip install --upgrade pip build
            python -m build
          ) else (
            echo Sem pyproject.toml - pulando build python.
          )
        """
      }
      echo "Build concluído."
    }

    stage('Notify') {
      // usa as credenciais que você já criou (mailtrap-smtp e EMAIL_TO)
      withCredentials([
        usernamePassword(credentialsId: 'mailtrap-smtp', usernameVariable: 'SMTP_USER', passwordVariable: 'SMTP_PASS'),
        string(credentialsId: 'EMAIL_TO', variable: 'EMAIL_TO')
      ]) {
        if (isUnix()) {
          sh """
            export SMTP_HOST=sandbox.smtp.mailtrap.io
            export SMTP_PORT=2525
            echo "Enviando notificação para: ${EMAIL_TO}"
            python3 scripts/notify.py --status "tests,build" --run-id "${env.BUILD_ID}" --repo "${env.GIT_URL}" --branch "${env.GIT_BRANCH ?: 'main'}"
          """
        } else {
          // Windows bat: note que %EMAIL_TO% é lido em tempo de execução pelo agente
          bat """
            @echo off
            set SMTP_HOST=sandbox.smtp.mailtrap.io
            set SMTP_PORT=2525
            echo Enviando notificação para: %EMAIL_TO%
            python scripts\\notify.py --status "tests,build" --run-id "${env.BUILD_ID}" --repo "${env.GIT_URL}" --branch "${env.GIT_BRANCH ?: 'main'}"
          """
        }
      }
      echo "Stage Notify finalizada."
    }

  } catch (err) {
    currentBuild.result = 'FAILURE'
    echo "Pipeline falhou: ${err}"
    throw err
  } finally {
    echo "Fim do pipeline."
  }
}
