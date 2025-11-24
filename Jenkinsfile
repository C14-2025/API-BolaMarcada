pipeline {
    agent any

    environment {
        VENV_DIR = "venv"
        PYTHON = "python"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "📦 Clonando repositório..."
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/C14-2025/API-BolaMarcada.git',
                        credentialsId: 'PAT_Jenkins'
                    ]]
                ])
            }
        }

        stage('Setup Python Environment') {
            steps {
              echo "🐍 Criando ambiente virtual..."
              sh '''
              if [ -d "$VENV_DIR" ]; then
                  rm -rf $VENV_DIR
              fi

              $PYTHON -m venv $VENV_DIR
              . $VENV_DIR/bin/activate
              python -m pip install --upgrade pip
              '''
            }
        }

        stage('Install Dependencies') {
            steps {
                echo "📚 Instalando dependências..."
                sh '''
                . $VENV_DIR/bin/activate
                ls -l
                cat requirements.txt
                pip cache purge
                pip install --upgrade pip
                pip install psycopg2-binary==2.9.10 --no-cache-dir
                pip install --no-cache-dir -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo "🧪 Executando testes unitários com pytest..."
                withCredentials([
                    usernamePassword(credentialsId: 'pg-db', usernameVariable: 'POSTGRES_USER', passwordVariable: 'POSTGRES_PASSWORD'),
                    string(credentialsId: 'postgres-server', variable: 'POSTGRES_SERVER'),
                    string(credentialsId: 'postgres-dbname', variable: 'POSTGRES_DB'),
                    string(credentialsId: 'app-secret-key', variable: 'SECRET_KEY')
                ]) {
                    sh '''
                    . $VENV_DIR/bin/activate
                    mkdir -p reports
                    pytest tests/ --maxfail=1 --disable-warnings \
                        --junitxml=reports/report.xml \
                        --html=reports/report.html
                    '''
                }
            }
        }

        stage('Build') {
            steps {
                echo "🏗️ Realizando build do projeto..."
                sh '''
                . $VENV_DIR/bin/activate
                pip install build
                python -m build || echo "⚠️ Nenhum processo de build necessário."
                '''
            }
        }

        stage('Archive Artifacts') {
            steps {
                echo "📦 Armazenando artefatos do build e relatórios..."
                archiveArtifacts artifacts: 'dist/*.whl, dist/*.tar.gz, tests/**/report*.xml, reports/**/*.html', fingerprint: true
            }
        }

        stage('Create GitHub Release') {
            steps {
                withCredentials([string(credentialsId: 'GITHUB_TOKEN', variable: 'GH_TOKEN')]) {
                    sh """
                    # Cria release usando a API do GitHub via curl
                    curl -X POST -H "Authorization: token \$GH_TOKEN" \
                        -H "Content-Type: application/json" \
                        -d \"{
                            \\\"tag_name\\\": \\\"v\$BUILD_NUMBER\\\",
                            \\\"name\\\": \\\"v\$BUILD_NUMBER\\\",
                            \\\"body\\\": \\\"Build automatizado via Jenkins\\\"
                        }\" \
                        https://api.github.com/repos/C14-2025/API-BolaMarcada/releases
                    """
                }
            }
        }

        stage('Notification'){

            steps {
                echo '📩 Enviando notificação por e-mail...'
                withCredentials([
                    string(credentialsId: 'EMAIL_DESTINO', variable: 'EMAIL_DESTINO'),
                    usernamePassword(credentialsId: 'mailtrap-smtp', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')
                ]) {
                    sh '''
                        cd scripts
                        chmod 775 shell.sh
                        ./shell.sh
                    '''
                }
            }
        }

        
    }

    post {
        success {
            echo "✅ Pipeline concluído com sucesso!"
        }
        failure {
            echo "❌ Pipeline falhou. Verifique os logs de erro acima."
        }
    }
}