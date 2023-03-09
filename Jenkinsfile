pipeline {
  agent any
  stages {
    stage('build') {
      steps {
        sh 'cd /opt/docker/bunkerCI'
        dir(path: '/opt/docker/bunkerCI') {
          sh 'invoke git-aggregate'
        }

      }
    }

  }
}