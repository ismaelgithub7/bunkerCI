pipeline {
  agent {
    node {
      label 'label1'
    }

  }
  stages {
    stage('build') {
      steps {
        sh 'cd /opt/docker/bunkerCI'
        build(job: 'docker-compose up', wait: true)
      }
    }

  }
}