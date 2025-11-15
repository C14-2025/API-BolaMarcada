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
                    ]]
                ])
            }
        }

        stage('Setup Python Environment') {
            steps {
                echo "🐍 Criando ambiente virtual..."
                sh '''
if command -v $PYTHON &> /dev/null
then
    echo "✅ Python encontrado: $($PYTHON --version)"
else
    echo "❌ Python3 não encontrado no ambiente Jenkins."
    exit 1
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
                pip install -r requirements.txt
                '''
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