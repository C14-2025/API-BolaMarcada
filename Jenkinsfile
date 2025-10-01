pipeline {
  agent any

  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    disableConcurrentBuilds()
  }

  parameters {
    booleanParam(name: 'ENABLE_GH_RELEASE', defaultValue: true,
      description: 'Publicar image-<commit>.tar como asset em um Release do GitHub (opcional)')
  }

  environment {
    // DB para testes
    PGUSER = 'postgres'
    PGPASS = 'postgres'
    PGDB   = 'bolamarcadadb'
    PGHOST = 'ci-db'
    PGPORT = '55432'

    // Relatórios/artefatos
    JUNIT_XML    = 'report-junit.xml'
    COVERAGE_XML = 'coverage.xml'
  }

  stages {
    stage('Checkout & Vars') {
      steps {
        checkout scm
        script {
          // captura a última linha do output do bat
          def commitOut = bat(script: 'git rev-parse --short=8 HEAD', returnStdout: true).trim().readLines()
          def branchOut = bat(script: 'git rev-parse --abbrev-ref HEAD', returnStdout: true).trim().readLines()
          env.COMMIT    = commitOut[commitOut.size()-1].trim()
          env.BRANCH    = branchOut[branchOut.size()-1].trim()
          env.IMAGE     = "app:${env.COMMIT}"
          env.IMAGE_TAR = "image-${env.COMMIT}.tar"
        }
      }
    }

    stage('Build image') {
      steps {
        bat '''
          @echo on
          docker version
          docker build --pull -t %IMAGE% -t app:latest .
        '''
      }
    }

    stage('CI (parallel)') {
      failFast false
      parallel {
        stage('Testes') {
          steps {
            script {
              catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                withCredentials([
                  string(credentialsId: 'app-secret-key',        variable: 'SECRET_KEY'),
                  string(credentialsId: 'access-token-expire',  variable: 'ACCESS_TOKEN_EXPIRE_MINUTES')
                ]) {
                  bat """
                    @echo on
                    rem -- rede dedicada
                    docker network create ci_net 2>nul || echo net exists

                    rem -- sobe Postgres
                    docker rm -f ci-db 2>nul
                    docker run -d --name ci-db --network ci_net -e POSTGRES_USER=%PGUSER% -e POSTGRES_PASSWORD=%PGPASS% -e POSTGRES_DB=%PGDB% -p %PGPORT%:5432 postgres:17-alpine

                    rem -- espera Postgres (até 60s)
                    setlocal EnableDelayedExpansion
                    for /L %%i in (1,1,60) do (
                      docker exec ci-db pg_isready -U %PGUSER% -d %PGDB%
                      if !errorlevel! EQU 0 (
                        echo DB OK
                        goto :dbready
                      )
                      timeout /t 1 >nul
                    )
                    echo Postgres nao ficou pronto a tempo
                    exit /b 1
                    :dbready

                    rem -- executa pytest dentro da SUA imagem, montando o workspace
                    docker run --rm --network ci_net ^
                      -e POSTGRES_SERVER=%PGHOST% -e POSTGRES_HOST=%PGHOST% ^
                      -e POSTGRES_USER=%PGUSER% -e POSTGRES_PASSWORD=%PGPASS% -e POSTGRES_DB=%PGDB% ^
                      -e DATABASE_URL=postgresql+psycopg2://%PGUSER%:%PGPASS%@%PGHOST%:5432/%PGDB% ^
                      -e SECRET_KEY=%SECRET_KEY% ^
                      -e ACCESS_TOKEN_EXPIRE_MINUTES=%ACCESS_TOKEN_EXPIRE_MINUTES% ^
                      -v "%cd%":/workspace -w /app %IMAGE% ^
                      sh -c "pytest -q --junit-xml=/workspace/%JUNIT_XML% --cov=. --cov-report=xml:/workspace/%COVERAGE_XML%"

                    echo SUCCESS > status_tests.txt
                  """
                }
              }
            }
          }
          post {
            always {
              junit allowEmptyResults: true, testResults: "${JUNIT_XML}"
              archiveArtifacts allowEmptyArchive: true, artifacts: "${JUNIT_XML}, ${COVERAGE_XML}"
              bat '''
                @echo off
                docker rm -f ci-db 2>nul
                docker network rm ci_net 2>nul
              '''
              script {
                if (!fileExists('status_tests.txt')) {
                  writeFile file: 'status_tests.txt', text: 'FAILURE'
                }
              }
            }
          }
        }

        stage('Empacotamento') {
          steps {
            script {
              catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                bat """
                  @echo on
                  docker save %IMAGE% -o %IMAGE_TAR%
                  echo SUCCESS > status_package.txt
                """
              }
            }
          }
          post {
            always {
              archiveArtifacts allowEmptyArchive: true, artifacts: "${IMAGE_TAR}"
              script {
                if (!fileExists('status_package.txt')) {
                  writeFile file: 'status_package.txt', text: 'FAILURE'
                }
              }
            }
          }
        }
      }
    }

    stage('Upload GitHub Release (opcional)') {
      when {
        allOf {
          expression { return params.ENABLE_GH_RELEASE }
          expression { return env.BRANCH == 'feat/CICD/Jenkins' }
        }
      }
      steps {
        withCredentials([usernamePassword(credentialsId: 'github-pat', usernameVariable: 'GH_USER', passwordVariable: 'GH_PAT')]) {
          bat """
            @echo on
            rem executa dentro de um container Alpine (Linux), com o workspace montado
            docker run --rm -v "%cd%":/w -w /w alpine:3.20 sh -lc "apk add --no-cache curl jq dos2unix && dos2unix scripts/upload_github_release.sh && GITHUB_TOKEN=%GH_PAT% GITHUB_REPO=C14-2025/API-BolaMarcada TAG=ci-%COMMIT% ASSET_PATH=%IMAGE_TAR% scripts/upload_github_release.sh"
          """
        }
      }
    }

    stage('Notificação') {
      steps {
        script {
          def testsStatus   = readFile('status_tests.txt').trim()
          def packageStatus = readFile('status_package.txt').trim()
          withCredentials([
            usernamePassword(credentialsId: 'mailtrap-smtp', usernameVariable: 'SMTP_USERNAME', passwordVariable: 'SMTP_PASSWORD'),
            string(credentialsId: 'EMAIL_TO', variable: 'TO_EMAIL')
          ]) {
            bat """
              @echo on
              docker run --rm ^
                -e TO_EMAIL=%TO_EMAIL% ^
                -e SMTP_SERVER=smtp.mailtrap.io ^
                -e SMTP_PORT=2525 ^
                -e FROM_EMAIL= ^
                -e SMTP_USERNAME=%SMTP_USERNAME% ^
                -e SMTP_PASSWORD=%SMTP_PASSWORD% ^
                -e TESTS_STATUS=${testsStatus} ^
                -e PACKAGE_STATUS=${packageStatus} ^
                -e GIT_SHA=%COMMIT% ^
                -e GIT_BRANCH=%BRANCH% ^
                -e GITHUB_RUN_ID=%BUILD_ID% ^
                -e GITHUB_RUN_NUMBER=%BUILD_NUMBER% ^
                -v "%cd%":/w -w /w python:3.12-alpine ^
                python scripts/notify_email.py
            """
          }
        }
      }
    }
  }

  post {
    always {
      echo "Pipeline finalizado."
    }
  }
}
