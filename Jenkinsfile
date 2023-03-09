pipeline {
  agent any
  stages {
    stage('build') {
      steps {
        sh 'uname -r'
      }
    }

    stage('CD') {
      steps {
        sh '''cd /op/docker/bunkerCI
docker-compose up -d'''
      }
    }

  }
}