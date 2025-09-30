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
    IMAGE_NAME = 'ci-api'               // nome lógico local da imagem
    IMAGE_TAG  = ''                     // será setado no Checkout
    SMTP_HOST  = 'smtp.mailtrap.io'
    SMTP_PORT  = '2525'
    // COMPOSE_PROJECT_NAME será calculado no stage Checkout (via script {})
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
        script {
          // Evita 'def' e evita usar 'short' como nome
          env.GIT_SHORT = sh(script: 'git rev-parse --short HEAD || echo local', returnStdout: true).trim()
          env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_SHORT}"

          // Calcula um project name seguro p/ docker compose
          def raw = "ci_${env.JOB_NAME}_${env.BUILD_NUMBER}"
          env.COMPOSE_PROJECT_NAME = raw.replaceAll('[^a-zA-Z0-9]', '').toLowerCase()
          echo "COMPOSE_PROJECT_NAME=${env.COMPOSE_PROJECT_NAME}"
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

          # Detecta docker compose vs docker-compose
          compose_cmd="docker compose"
          if ! docker compose version >/dev/null 2>&1; then
            if command -v docker-compose >/dev/null 2>&1; then
              compose_cmd="docker-compose"
            fi
          fi
          echo "Usando: $compose_cmd"

          # Sobe apenas o DB
          $compose_cmd up -d db

          # Roda testes dentro do serviço api
          $compose_cmd run --rm api sh -lc '
            set -e
            # Espera DB sem depender do pg_isready (usa Python puro)
            python - <<PY
import os, socket, time
host="db"; port=5432
for i in range(120):
    try:
        with socket.create_connection((host, port), timeout=1):
            print("db pronto"); break
    except Exception as e:
        print("aguardando db...", e)
        time.sleep(1)
else:
    raise SystemExit("db nao respondeu")
PY
            mkdir -p reports
            pytest --junitxml=reports/junit.xml -q
          '

          # Derruba os serviços de teste
          $compose_cmd down -v || true
        '''
      }
      post {
        always {
          // Publica JUnit e arquiva relatórios (mesmo se falhar)
          junit allowEmptyResults: true, testResults: 'reports/junit.xml'
          archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
      }
    }

    stage('Build & Package (Docker)') {
      steps {
        sh '''
          set -e
          docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -f Dockerfile .
          docker image ls ${IMAGE_NAME}:${IMAGE_TAG}
          docker save -o artifacts/${IMAGE_NAME}_${IMAGE_TAG}.tar ${IMAGE_NAME}:${IMAGE_TAG}
        '''
        archiveArtifacts artifacts: 'artifacts/*.tar', onlyIfSuccessful: true
      }
    }
  }

  post {
    always {
      // Notificação via scripts/notify.py (usa credenciais Mailtrap e EMAIL_TO)
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

          # Executa notify.py dentro de um container Python (sem depender do agente)
          docker run --rm -v "$PWD:/app" -w /app \
            -e SMTP_HOST="${SMTP_HOST}" -e SMTP_PORT="${SMTP_PORT}" \
            -e SMTP_USER="$SMTP_USER" -e SMTP_PASS="$SMTP_PASS" -e EMAIL_TO="$EMAIL_TO" \
            python:3.13-slim sh -lc "python scripts/notify.py --status \\"$STATUS\\" --run-id \\"$RUNID\\" --repo \\"$REPO\\" --branch \\"$BRANCH\\""
        '''
      }
      // Limpeza leve
      sh 'docker system prune -f || true'
    }
  }
}
