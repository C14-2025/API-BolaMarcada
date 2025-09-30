// Jenkinsfile (Scripted) — usa caminho absoluto do Python no Windows
node {
  // Caminho absoluto do python no Windows (ajuste aqui se mudar)
  def WIN_PY = 'C:\\\\Users\\\\jmxd\\\\AppData\\\\Local\\\\Programs\\\\Python\\\\Python313\\\\python.exe'

  try {
    stage('Checkout') {
      checkout scm
      echo "Checkout realizado."
    }

    stage('Tests') {
      echo "Instalando dependências e rodando testes (pytest)..."
      if (isUnix()) {
        sh '''
          python3 -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip3 install -r requirements.txt; fi
          pytest -q
        '''
      } else {
        bat """
          @echo off
          "${WIN_PY}" -m pip install --upgrade pip
          if exist requirements.txt (
            "${WIN_PY}" -m pip install -r requirements.txt
          )
          "${WIN_PY}" -m pytest -q
        """
      }
      echo "Testes finalizados."
    }

    stage('Build') {
      echo "Empacotamento / Build (ajuste conforme necessário)..."
      if (isUnix()) {
        sh '''
          if [ -f pyproject.toml ]; then
            python3 -m pip install --upgrade pip build
            python3 -m build
          else
            echo "Sem pyproject.toml — pulando build python."
          fi
        '''
      } else {
        bat """
          @echo off
          if exist pyproject.toml (
            "${WIN_PY}" -m pip install --upgrade pip build
            "${WIN_PY}" -m build
          ) else (
            echo Sem pyproject.toml - pulando build p
