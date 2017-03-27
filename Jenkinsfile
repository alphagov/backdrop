#!/usr/bin/env groovy

REPOSITORY = 'backdrop'

node ('mongodb-2.4') {

  def govuk = load '/var/lib/jenkins/groovy_scripts/govuk_jenkinslib.groovy'

  try {
    stage("Checkout") {
       checkout scm
    }

    stage("Build") {
       sh "${WORKSPACE}/jenkins.sh"
    }

    stage("Push release tag") {
       govuk.pushTag(REPOSITORY, env.BRANCH_NAME, 'release_' + env.BUILD_NUMBER)
    }

    stage("Deploy on Integration") {
      govuk.deployIntegration("write.backdrop", env.BRANCH_NAME, 'release', 'deploy')
      govuk.deployIntegration("read.backdrop", env.BRANCH_NAME, 'release', 'deploy')
    }

  } catch (e) {
    currentBuild.result = "FAILED"
    step([$class: 'Mailer',
          notifyEveryUnstableBuild: true,
          recipients: 'govuk-ci-notifications@digital.cabinet-office.gov.uk',
          sendToIndividuals: true])
    throw e
  }
}
