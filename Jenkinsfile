pipeline {
  agent any

  options {
    timestamps()
    ansiColor('xterm')
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 45, unit: 'MINUTES')
  }

  environment {
    DOCKER_BUILDKIT = '1'
    IMAGE_NAME = 'ci-api'                     // nome lógico local da imagem
    IMAGE_TAG  = ''                           // setado no Checkout
    SMTP_HOST  = 'smtp.mailtrap.io'
    SMTP_PORT  = '2525'
    // Isola nomes do compose por build
    COMPOSE_PROJECT_NAME = "ci_${env.JOB_NAME}_${env.BUILD_NUMBER}".replaceAll('[^a-zA-Z0-9]', '').toLowerCase()
  }

  stages {
    stage('Checkout') {
      steps {
        // Se o job já usa "SCM: Git", mantenha 'checkout scm'.
        // Se preferir forçar PAT: descomente a linha abaixo e ajuste a URL:
        // git credentialsId: 'github-pat', url: 'https://github.com/ORG/REPO.git', branch: 'main'
        checkout scm
        script {
          def short = sh(script: 'git rev-parse --short HEAD || echo local', returnStdout: true).trim()
          env.IMAGE_TAG = "${env.BUILD_NUMBER}-${short}"
        }
      }
    }

    stage('Preparar .env') {
      steps {
        withCredentials([file(credentialsId: 'env-file', variable: 'ENV_FILE')]) {
          sh '''
            set -e
            cp "$ENV_FILE" ./.env
            echo "[ci] .env copiado para workspace"
          '''
        }
      }
    }

    stage('Testes (pytest)') {
      steps {
        sh '''
          set -e
          mkdir -p reports artifacts
          # Sobe somente o banco
          docker compose up -d db
        '''
        // roda pytest dentro do serviço api (usa env_file .env)
        sh '''
          set -e
          # Aguarda o Postgres ficar pronto a partir do container da api (que herda env_file)
          docker compose run --rm api sh -lc '
            until pg_isready -h db -p 5432 -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
              echo "Aguardando Postgres..." && sleep 1
            done
            mkdir -p reports
            pytest --junitxml=reports/junit.xml -q
          '
          # Copia relatórios do volume (./ -> /app) já estão no host por causa do bind mount
        '''
      }
      post {
        always {
          // Publica JUnit e guarda relatórios (mesmo se falhar)
          junit allowEmptyResults: true, testResults: 'reports/junit.xml'
          archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
          sh 'docker compose down -v || true'
        }
      }
    }

    stage('Build & Package (Docker)') {
      steps {
        sh '''
          set -e
          # Build direto pelo Dockerfile (mais simples de etiquetar)
          docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -f Dockerfile .
          docker image ls ${IMAGE_NAME}:${IMAGE_TAG}
          # Empacota a imagem como artefato .tar
          docker save -o artifacts/${IMAGE_NAME}_${IMAGE_TAG}.tar ${IMAGE_NAME}:${IMAGE_TAG}
        '''
        archiveArtifacts artifacts: 'artifacts/*.tar', onlyIfSuccessful: true
      }
    }
  }

  post {
    always {
      // Notificação por e-mail via scripts/notify.py dentro de um contêiner Python
      withCredentials([
        usernamePassword(credentialsId: 'mailtrap-smtp', usernameVariable: 'SMTP_USER', passwordVariable: 'SMTP_PASS'),
        string(credentialsId: 'EMAIL_TO', variable: 'EMAIL_TO')
      ]) {
        sh '''
          set -e
          STATUS="${currentBuild.currentResult}"
          REPO="$(git config --get remote.origin.url || echo unknown)"
          BRANCH="$(git rev-parse --abbrev-ref HEAD || echo unknown)"
          RUNID="${BUILD_URL:-${JOB_NAME}#${BUILD_NUMBER}}"

          # roda notify.py sem depender de Python no agente
          docker run --rm -v "$PWD:/app" -w /app \
            -e SMTP_HOST="${SMTP_HOST}" -e SMTP_PORT="${SMTP_PORT}" \
            -e SMTP_USER="$SMTP_USER" -e SMTP_PASS="$SMTP_PASS" -e EMAIL_TO="$EMAIL_TO" \
            python:3.13-slim sh -lc "pip install --no-cache-dir --disable-pip-version-check --quiet smtplib || true; python scripts/notify.py --status \\"$STATUS\\" --run-id \\"$RUNID\\" --repo \\"$REPO\\" --branch \\"$BRANCH\\""
        '''
      }
      // Limpeza leve (não remove a imagem empacotada porque já viramos artefato .tar)
      sh 'docker system prune -f || true'
    }
  }
}
