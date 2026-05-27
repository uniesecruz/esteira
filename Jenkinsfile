pipeline {
    agent any

    environment {
        DATABRICKS_HOST     = credentials('databricks-token')
        SONAR_TOKEN         = credentials('sonar-token')
        PYTHON_VENV         = '/opt/venv'
        PATH                = "${PYTHON_VENV}/bin:${env.PATH}"
    }

    options {
        timestamps()
        ansiColor('xterm')
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "Branch: ${env.BRANCH_NAME}"
            }
        }

        stage('Setup') {
            steps {
                sh '''
                    python3 --version
                    pip install -r requirements.txt 2>/dev/null || true
                '''
            }
        }

        stage('Quality Gates') {
            parallel {
                stage('Lint - flake8') {
                    steps {
                        sh 'flake8 src/ tests/ --max-line-length 100 --statistics --format=pylint'
                    }
                }

                stage('Lint - black') {
                    steps {
                        sh 'black --check --line-length 100 src/ tests/'
                    }
                }

                stage('Security - Bandit') {
                    steps {
                        sh '''
                            bandit -r src/ -f json -o bandit-report.json || true
                            bandit -r src/ --severity-level medium
                        '''
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'bandit-report.json', allowEmptyArchive: true
                        }
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        sonar-scanner \
                            -Dsonar.projectKey=esteira-ml-pipeline \
                            -Dsonar.projectName="Esteira ML Pipeline" \
                            -Dsonar.sources=src/ \
                            -Dsonar.tests=tests/ \
                            -Dsonar.python.coverage.reportPaths=coverage.xml \
                            -Dsonar.language=py \
                            -Dsonar.sourceEncoding=UTF-8
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Tests') {
            steps {
                sh '''
                    pytest tests/ -v --tb=short \
                        --cov=src \
                        --cov-report=term-missing \
                        --cov-report=xml:coverage.xml \
                        --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                    archiveArtifacts artifacts: 'coverage.xml', allowEmptyArchive: true
                }
            }
        }

        stage('Fortify Scan') {
            when {
                environment name: 'RUN_FORTIFY', value: 'true'
            }
            steps {
                sh '''
                    echo "Running Fortify Static Code Analyzer..."
                    if command -v sourceanalyzer &> /dev/null; then
                        sourceanalyzer -b esteira -clean
                        sourceanalyzer -b esteira src/**/*.py
                        sourceanalyzer -b esteira -scan -f fortify-results.fpr
                        echo "Fortify scan complete: fortify-results.fpr"
                    else
                        echo "WARNING: Fortify SCA not installed. Skipping scan."
                        echo "To enable, install Fortify SCA and set RUN_FORTIFY=true"
                    fi
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'fortify-results.fpr', allowEmptyArchive: true
                }
            }
        }

        stage('Deploy to Databricks') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([string(credentialsId: 'databricks-token', variable: 'DATABRICKS_TOKEN')]) {
                    sh '''
                        echo "Deploying to Databricks..."
                        python3 scripts/deploy_to_databricks.py
                    '''
                }
            }
        }

        stage('Run Databricks Job') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([string(credentialsId: 'databricks-token', variable: 'DATABRICKS_TOKEN')]) {
                    sh '''
                        echo "Triggering Databricks job..."
                        python3 scripts/run_databricks_job.py
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check the logs for details.'
        }
        always {
            cleanWs()
        }
    }
}
