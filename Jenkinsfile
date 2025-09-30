// Jenkinsfile (Scripted) — compatível com agentes Unix e Windows
node {
  def WIN_PY = 'C:\\Users\\jmxd\\AppData\\Local\\Programs\\Python\\Python313\\python.exe'

  try {
    stage('Checkout') {
      checkout scm
      echo "Checkout realizado."
    }

    stage('Tests') {
      echo "Instalando dependências e rodando testes (pytest)..."
      if (isUnix()) {
        sh '''
          python3 -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip3 install -r requirements.txt; fi
          pytest -q
        '''
      } else {
        bat """
          @echo off
          \"${WIN_PY}\" -m pip install --upgrade pip
          if exist requirements.txt (
            \"${WIN_PY}\" -m pip install -r requirements.txt
          )
          \"${WIN_PY}\" -m pytest -q
        """
      }
      echo "Testes finalizados."
    }

    stage('Build') {
      echo "Empacotamento / Build (ajuste conforme necessário)..."
      if (isUnix()) {
        sh '''
          if [ -f pyproject.toml ]; then
            python3 -m pip install --upgrade pip build
            python3 -m build
          else
            echo "Sem pyproject.toml — pulando build python."
          fi
        '''
      } else {
        bat """
          @echo off
          if exist pyproject.toml (
            \"${WIN_PY}\" -m pip install --upgrade pip build
            \"${WIN_PY}\" -m build
          ) else (
            echo Sem pyproject.toml - pulando build python.
          )
        """
      }
      echo "Build concluído."
    }

    stage('Notify') {
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
          bat """
            @echo off
            set SMTP_HOST=sandbox.smtp.mailtrap.io
            set SMTP_PORT=2525
            echo Enviando notificação para: %EMAIL_TO%
            \"${WIN_PY}\" scripts\\notify.py --status "tests,build" --run-id "${env.BUILD_ID}" --repo "${env.GIT_URL}" --branch "${env.GIT_BRANCH ?: 'main'}"
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
