pipeline {
  agent any

  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 45, unit: 'MINUTES')
  }

  environment {
    DOCKER_BUILDKIT = '1'
    IMAGE_NAME = 'ci-api'     // nome lógico local
    IMAGE_TAG  = ''           // setado no Checkout
    SMTP_HOST  = 'smtp.mailtrap.io'
    SMTP_PORT  = '2525'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        script {
          env.GIT_SHORT = sh(script: 'git rev-parse --short HEAD || echo local', returnStdout: true).trim()
          env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_SHORT}"
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
            # Espera db responder (sem depender de pg_isready)
            python - <<PY
import socket, time
host="db"; port=5432
for i in range(120):
    try:
        with socket.create_connection((host, port), timeout=1):
            print("db pronto"); break
    except Exception:
        print("aguardando db..."); time.sleep(1)
else:
    raise SystemExit("db nao respondeu")
PY
            mkdir -p reports
            pytest --junitxml=reports/junit.xml -q
          '

          # Derruba serviços usados nos testes
          $compose_cmd down -v || true
        '''
      }
      post {
        always {
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

          docker run --rm -v "$PWD:/app" -w /app \
            -e SMTP_HOST="${SMTP_HOST}" -e SMTP_PORT="${SMTP_PORT}" \
            -e SMTP_USER="$SMTP_USER" -e SMTP_PASS="$SMTP_PASS" -e EMAIL_TO="$EMAIL_TO" \
            python:3.13-slim sh -lc "python scripts/notify.py --status \\"$STATUS\\" --run-id \\"$RUNID\\" --repo \\"$REPO\\" --branch \\"$BRANCH\\""
        '''
      }
      sh 'docker system prune -f || true'
    }
  }
}
