pipeline {
  agent {
    node {
      label 'label1'
    }

  }
  stages {
    stage('build') {
      steps {
        sh 'uname -r'
      }
    }

    stage('CD') {
      steps {
        sh '''cd /opt/docker/bunkerCI
docker-compose up -d'''
      }
    }

  }
}