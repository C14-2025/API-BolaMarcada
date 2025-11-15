pipeline {
    agent any

    environment {
        VENV_DIR = "venv"
        PYTHON = "python3"
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
                ]],  // ← vírgula adicionada aqui
                extensions: [[$class: 'WipeWorkspace']]
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

        // stage('Build') {
        //     steps {
        //         echo "🏗️ Realizando build do projeto..."
        //         sh '''
        //         . $VENV_DIR/bin/activate
        //         pip install build
        //         python -m build || echo "⚠️ Nenhum processo de build necessário."
        //         '''
        //     }
        // }

        // stage('Run Tests') {
        //     steps {
        //         echo "🧪 Executando testes unitários com pytest..."
        //         sh '''
        //         . $VENV_DIR/bin/activate
        //         mkdir -p reports
        //         pytest tests/ --maxfail=1 --disable-warnings \
        //             --junitxml=reports/report.xml \
        //             --html=reports/report.html
        //         '''
        //     }
        // }

        // stage('Archive Artifacts') {
        //     steps {
        //         echo "📦 Armazenando artefatos do build e relatórios..."
        //         archiveArtifacts artifacts: 'dist/*.whl, dist/*.tar.gz, tests/**/report*.xml, reports/**/*.html', fingerprint: true
        //     }
        // }

        // stage('Notification'){

        //     steps {
        //         echo '📩 Enviando notificação por e-mail...'
        //         withCredentials([
        //             string(credentialsId: 'EMAIL_DESTINO', variable: 'EMAIL_DESTINO'),
        //             usernamePassword(credentialsId: 'mailtrap-smtp', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')
        //         ]) {
        //             sh '''
        //                 cd scripts
        //                 chmod 775 shell.sh
        //                 ./shell.sh
        //             '''
        //         }
        //     }
        // }
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