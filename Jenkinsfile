pipeline {
  agent any
  stages {
    stage('error') {
      steps {
        sh '''cd /opt/docker/bunkerCI
ls -lh
touch prueba
ls
rm prueba'''
      }
    }

  }
}