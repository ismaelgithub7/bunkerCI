pipeline {
  agent any
  stages {
    stage('build') {
      steps {
        sh '''cd /opt/docker/bunkerCI
'''
      }
    }

    stage('git-aggregate') {
      steps {
        sh 'docker-compose up -d'
      }
    }

    stage('') {
      steps {
        sleep 10
      }
    }

  }
}