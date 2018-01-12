#!groovy

def startTests(suite, shard) {
  return {
    echo "I am ${suite}:${shard}, and the worker is yet to be started!"

    node("${suite}-${shard}-worker") {
      // Cleaning up previous builds. Heads up! Not sure if `WsCleanup` actually works.
      step([$class: 'WsCleanup'])

      checkout scm

      sh 'git log --oneline | head'

      timeout(time: 55, unit: 'MINUTES') {
        echo "Hi, it is me ${suite}:${shard} again, the worker just started!"

        try {
          if (suite == 'accessibility') {
            sh './scripts/accessibility-tests.sh'
          } else {
            withEnv(["TEST_SUITE=${suite}", "SHARD=${shard}"]) {
              sh './scripts/all-tests.sh'
            }
          }
        } finally {
          archiveArtifacts 'reports/**, test_root/log/**'
	  stash includes: 'reports/**, test_root/log/**', name: "artifacts-${suite}-${shard}"

          try {
            junit 'reports/**/*.xml'
          } finally {
            // This works, but only for the current build files.
            deleteDir()
          }
        }
      }
    }
  }
}

def getSuites() {
  return [
    [name: 'lms-unit', 'shards': [
      1,
      2,
      3,
      4,
    ]],
    [name: 'cms-unit', 'shards': ['all']],
  ]
}

def buildParallelSteps() {
  def parallelSteps = [:]

  for (def suite in getSuites()) {
    def name = suite['name']

    for (def shard in suite['shards']) {
      parallelSteps["${name}_${shard}"] = startTests(name, shard)
    }
  }

  return parallelSteps
}

stage('Prepare') {
  echo 'Starting the build...'
}

stage('Unit tests') {
  
}

stage('Coverage') {
  node('coverage-report-worker') {
      // Cleaning up previous builds. Heads up! Not sure if `WsCleanup` actually works.
      step([$class: 'WsCleanup'])

      checkout scm

      sh 'git log --oneline | head'
      sh 'git log --oneline --graph'
	  
      sh "git rev-parse HEAD > .git/head-id"                        
      head_id = readFile('.git/head-id')
      echo "${head_id}"
	  
      sh "git rev-parse HEAD^1 > .git/head1-id"                        
      head1_id = readFile('.git/head1-id')
      echo "${head1_id}"
      
      sh "git rev-parse HEAD^2 > .git/head2-id"                        
      head2_id = readFile('.git/head2-id')
      echo "${head2_id}"

      timeout(time: 55, unit: 'MINUTES') {
        echo "Hi, it is me coverage agent again, the worker just started!"
     
        try {
	  unstash 'artifacts-lms-unit-1'
	  unstash 'artifacts-lms-unit-2'
	  unstash 'artifacts-lms-unit-3'
	  unstash 'artifacts-lms-unit-4'
	  unstash 'artifacts-cms-unit-all' 
	  withCredentials([string(credentialsId: '73037323-f1a4-44e2-8054-04d2a9580240', variable: 'report_token')]) {
	    withEnv(["TARGET_BRANCH=${head_id}", "CODE_COV_TOKEN=${report_token}", "CI_BRANCH=${merge_id}"]) {
              sh './scripts/jenkins-report.sh'
            }
	  }
	} finally {	
          archiveArtifacts 'reports/**, test_root/log/**'
 	  cobertura autoUpdateHealth: false, autoUpdateStability: false, coberturaReportFile: 'reports/coverage.xml', conditionalCoverageTargets: '70, 0, 0', failUnhealthy: false, failUnstable: false, lineCoverageTargets: '80, 0, 0', maxNumberOfBuilds: 0, methodCoverageTargets: '80, 0, 0', onlyStable: false, sourceEncoding: 'ASCII', zoomCoverageChart: false
          }
      }
    }
}

stage('Done') {
  echo 'Done! :)'
}
