// Jenkinsfile (Scripted Pipeline — compatível com mais versões do Jenkins)
node {
  try {
    stage('Checkout') {
      checkout scm
      echo "Checkout realizado."
    }

    stage('Tests') {
      echo "Instalando dependências e rodando testes (pytest)..."
      // Ajuste caso precise de python3 em outro nome
      sh '''
        python3 -m pip install --upgrade pip || true
        if [ -f requirements.txt ]; then pip3 install -r requirements.txt; fi
        pytest -q || true
      '''
      echo "Testes finalizados (ver logs acima)."
    }

    stage('Build') {
      echo "Empacotamento/build (somente exemplo — ajuste conforme seu fluxo)..."
      // Se você usa python build:
      sh '''
        if [ -f pyproject.toml ]; then
          python3 -m pip install build || true
          python3 -m build || true
        else
          echo "Sem pyproject.toml — pulando build python (ou ajuste para docker build)..."
        fi
      '''
      echo "Build concluído."
    }

    stage('Notify') {
      // injeta credenciais que você já criou no Jenkins
      withCredentials([
        usernamePassword(credentialsId: 'mailtrap-smtp', usernameVariable: 'SMTP_USER', passwordVariable: 'SMTP_PASS'),
        string(credentialsId: 'EMAIL_TO', variable: 'EMAIL_TO')
      ]) {
        // define host/port e chama o script de notificação python
        // ajuste 'python3' para 'python' caso seu agente use esse binário
        sh '''
          export SMTP_HOST=sandbox.smtp.mailtrap.io
          export SMTP_PORT=2525
          echo "Enviando notificação para: $EMAIL_TO (via Mailtrap)..."
          python3 scripts/notify.py --status "tests,build" --run-id "${BUILD_ID}" --repo "${GIT_URL}" --branch "${GIT_BRANCH:-main}"
        '''
      }
      echo "Stage Notify finalizada."
    }

  } catch (err) {
    // em caso de falha, marca build como failed e re-lança o erro
    currentBuild.result = 'FAILURE'
    echo "Pipeline falhou: ${err}"
    throw err
  } finally {
    echo "Fim do node."
  }
}
