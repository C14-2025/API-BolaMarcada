stage('Notify') {
  steps {
    // injeta SMTP user/pass e o EMAIL_TO secret como variáveis de ambiente
    withCredentials([
      usernamePassword(credentialsId: 'mailtrap-smtp', usernameVariable: 'SMTP_USER', passwordVariable: 'SMTP_PASS'),
      string(credentialsId: 'EMAIL_TO', variable: 'EMAIL_TO')
    ]) {
      // define HOST/PORT (não secret) e roda o script Python
      sh '''
        export SMTP_HOST=sandbox.smtp.mailtrap.io
        export SMTP_PORT=2525
        python3 scripts/notify.py \
          --status "tests,build" \
          --run-id "${BUILD_ID}" \
          --repo "${GIT_URL}" \
          --branch "${BRANCH_NAME:-main}"
      '''
    }
  }
}
