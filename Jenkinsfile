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
        sh 'invoke git-aggergate'
      }
    }

  }
}