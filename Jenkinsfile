pipeline {
  agent any

  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 45, unit: 'MINUTES')
  }

  environment {
    DOCKER_BUILDKIT = '1'
    IMAGE_NAME = 'ci-api'
    IMAGE_TAG  = ''
    SMTP_HOST  = 'smtp.mailtrap.io'
    SMTP_PORT  = '2525'
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
        script {
          // pega o hash curto do git no Windows
          bat '@echo off\r\ngit rev-parse --short HEAD > gitshort.txt 2>nul\r\nif errorlevel 1 (echo local>gitshort.txt)\r\n'
          env.GIT_SHORT = readFile('gitshort.txt').trim()
          env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_SHORT}"
        }
      }
    }

    stage('Preparar .env') {
      steps {
        withCredentials([file(credentialsId: 'env-file', variable: 'ENV_FILE')]) {
          bat '@echo off\r\ncopy /Y "%ENV_FILE%" ".\\.env"\r\necho [ci] .env copiado\r\n'
        }
      }
    }

    stage('Testes (pytest)') {
      steps {
        // cria um script simples para esperar o DB dentro do container
        script {
          writeFile file: 'scripts/wait_db.py', text: '''
import socket, time, sys
host='db'; port=5432
for i in range(120):
    try:
        s=socket.create_connection((host,port),1); s.close(); print('db pronto'); break
    except Exception:
        print('aguardando db...'); time.sleep(1)
else:
    sys.exit('db nao respondeu')
'''.stripIndent()
        }

        bat """@echo off
setlocal enabledelayedexpansion
if not exist reports mkdir reports
if not exist artifacts mkdir artifacts

REM Detecta docker compose vs docker-compose
set COMPOSE_CMD=docker compose
docker compose version >NUL 2>&1
if errorlevel 1 (
  where docker-compose >NUL 2>&1
  if errorlevel 1 (
    echo ERRO: docker compose/docker-compose nao encontrado.
    exit /b 2
  ) else (
    set COMPOSE_CMD=docker-compose
  )
)
echo Usando: !COMPOSE_CMD!

REM Sobe apenas o DB
!COMPOSE_CMD! up -d db
if errorlevel 1 exit /b %ERRORLEVEL%

REM Roda o wait + pytest dentro do serviço api
!COMPOSE_CMD! run --rm api sh -lc "python scripts/wait_db.py && mkdir -p reports && pytest --junitxml=reports/junit.xml -q"
set EXITCODE=%ERRORLEVEL%

REM Derruba containers usados nos testes (e volumes)
!COMPOSE_CMD! down -v

exit /b %EXITCODE%
"""
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
        bat """@echo off
docker build -t %IMAGE_NAME%:%IMAGE_TAG% -f Dockerfile .
if errorlevel 1 exit /b %ERRORLEVEL%

docker image ls %IMAGE_NAME%:%IMAGE_TAG%

if not exist artifacts mkdir artifacts
docker save -o artifacts\\%IMAGE_NAME%_%IMAGE_TAG%.tar %IMAGE_NAME%:%IMAGE_TAG%
"""
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
        script {
          def status = currentBuild.currentResult
          def repo   = bat(returnStdout:true, script:'@echo off\r\ngit config --get remote.origin.url 2>nul\r\n').trim()
          def branch = bat(returnStdout:true, script:'@echo off\r\ngit rev-parse --abbrev-ref HEAD 2>nul\r\n').trim()
          def runid  = env.BUILD_URL ? env.BUILD_URL : "${env.JOB_NAME}#${env.BUILD_NUMBER}"

          bat """@echo off
docker run --rm -v "%CD%:/app" -w /app ^
  -e SMTP_HOST=%SMTP_HOST% -e SMTP_PORT=%SMTP_PORT% ^
  -e SMTP_USER=%SMTP_USER% -e SMTP_PASS=%SMTP_PASS% -e EMAIL_TO=%EMAIL_TO% ^
  python:3.13-slim sh -lc "python scripts/notify.py --status \\"${status}\\" --run-id \\"${runid}\\" --repo \\"${repo}\\" --branch \\"${branch}\\""
"""
        }
      }
      // limpeza leve; ignora erro se docker não estiver presente
      bat 'docker system prune -f >NUL 2>&1 || exit /b 0'
    }
  }
}
