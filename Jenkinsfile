pipeline {
  agent any

  options {
    timestamps()
    ansiColor('xterm')
    buildDiscarder(logRotator(numToKeepStr: '20'))
    disableConcurrentBuilds()
  }

  parameters {
    booleanParam(name: 'ENABLE_GH_RELEASE', defaultValue: true, description: 'Publicar image-<commit>.tar como asset em um Release do GitHub')
  }

  environment {
    // DB para testes
    PGUSER   = 'postgres'
    PGPASS   = 'postgres'
    PGDB     = 'bolamarcadadb'
    PGHOST   = 'ci-db'
    PGPORT   = '55432'

    // Relatórios/artefatos
    JUNIT_XML    = 'report-junit.xml'
    COVERAGE_XML = 'coverage.xml'
  }

  stages {
    stage('Checkout & Vars') {
      steps {
        checkout scm
        script {
          env.COMMIT     = sh(script: 'git rev-parse --short=8 HEAD', returnStdout: true).trim()
          env.IMAGE      = "app:${env.COMMIT}"
          env.IMAGE_TAR  = "image-${env.COMMIT}.tar"
          env.BRANCH     = env.BRANCH_NAME ?: sh(script: 'git rev-parse --abbrev-ref HEAD', returnStdout: true).trim()
        }
      }
    }

    stage('Build image') {
      steps {
        sh '''
          set -eux
          docker build --pull -t ${IMAGE} -t app:latest .
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
                  // variáveis da app (sem hardcode)
                  string(credentialsId: 'app-secret-key', variable: 'SECRET_KEY'),
                  string(credentialsId: 'access-token-expire', variable: 'ACCESS_TOKEN_EXPIRE_MINUTES')
                ]) {
                  sh """
                    set -eux

                    docker network create ci_net || true

                    docker rm -f ci-db || true
                    docker run -d --name ci-db --network ci_net \
                      -e POSTGRES_USER=${PGUSER} -e POSTGRES_PASSWORD=${PGPASS} -e POSTGRES_DB=${PGDB} \
                      -p ${PGPORT}:5432 postgres:17-alpine

                    for i in \$(seq 1 60); do
                      docker exec ci-db pg_isready -U ${PGUSER} -d ${PGDB} && break || sleep 1
                    done

                    # roda pytest na SUA imagem, conectando ao DB da rede ci_net
                    docker run --rm --network ci_net \
                      -e POSTGRES_SERVER=${PGHOST} -e POSTGRES_HOST=${PGHOST} \
                      -e POSTGRES_USER=${PGUSER} -e POSTGRES_PASSWORD=${PGPASS} -e POSTGRES_DB=${PGDB} \
                      -e DATABASE_URL=postgresql+psycopg2://${PGUSER}:${PGPASS}@${PGHOST}:5432/${PGDB} \
                      -e SECRET_KEY="\${SECRET_KEY}" \
                      -e ACCESS_TOKEN_EXPIRE_MINUTES="\${ACCESS_TOKEN_EXPIRE_MINUTES}" \
                      -v "\$PWD":/workspace -w /app ${IMAGE} \
                      sh -c "pytest -q --junit-xml=/workspace/${JUNIT_XML} --cov=. --cov-report=xml:/workspace/${COVERAGE_XML}"

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
              sh '''
                docker rm -f ci-db || true
                docker network rm ci_net || true
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
                sh """
                  set -eux
                  docker save ${IMAGE} -o ${IMAGE_TAR}
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
          expression { return env.BRANCH == 'feat/CICD/Jenkins' }  // roda só nessa branch
        }
      }
      steps {
        withCredentials([usernamePassword(credentialsId: 'github-pat', usernameVariable: 'GH_USER', passwordVariable: 'GH_PAT')]) {
          sh """
            set -eux
            chmod +x scripts/upload_github_release.sh
            docker run --rm -v "\$PWD":/w -w /w alpine:3.20 sh -c '
              apk add --no-cache curl jq
              GITHUB_TOKEN="\${GH_PAT}" \
              GITHUB_REPO="C14-2025/API-BolaMarcada" \
              TAG="ci-${COMMIT}" \
              ASSET_PATH="${IMAGE_TAR}" \
              scripts/upload_github_release.sh
            '
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
            // Mailtrap SMTP e destinatário
            usernamePassword(credentialsId: 'mailtrap-smtp', usernameVariable: 'SMTP_USERNAME', passwordVariable: 'SMTP_PASSWORD'),
            string(credentialsId: 'EMAIL_TO', variable: 'TO_EMAIL')
          ]) {
            sh """
              set -eux
              docker run --rm \
                -e TO_EMAIL="\${TO_EMAIL}" \
                -e SMTP_SERVER="smtp.mailtrap.io" \
                -e SMTP_PORT="2525" \
                -e FROM_EMAIL="" \
                -e SMTP_USERNAME="\${SMTP_USERNAME}" \
                -e SMTP_PASSWORD="\${SMTP_PASSWORD}" \
                -e TESTS_STATUS="${testsStatus}" \
                -e PACKAGE_STATUS="${packageStatus}" \
                -e GIT_SHA="${COMMIT}" \
                -e GIT_BRANCH="${BRANCH}" \
                -e GITHUB_RUN_ID="${env.BUILD_ID}" \
                -e GITHUB_RUN_NUMBER="${env.BUILD_NUMBER}" \
                -v "\$PWD":/w -w /w python:3.12-alpine \
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
