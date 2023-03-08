pipeline {
  agent any
  stages {
    stage('error') {
      steps {
        sh '''cd /opt/docker/bunkerCI
invoke img-build'''
      }
    }

  }
  environment {
    linux = '1'
  }
}