pipeline {
  agent any
  stages {
    stage('prueba') {
      steps {
        sh '''cd /opt/docker/bunkerCI
ls
rm docker-compose.yml
cp devel.yaml docker-compose.yml
ls -lh
'''
      }
    }

  }
}