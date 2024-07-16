#!/bin/bash

# Get the name of the current directory
PROJECT_NAME=${PWD##*/}

# Create a new directory for the project
PROJECT_DIR="${PROJECT_NAME}_project"
mkdir $PROJECT_DIR
cd $PROJECT_DIR

# Initialize CDK in the new directory
cdk init app --language python

# Remove requirements files since we are using Poetry
rm requirements.txt requirements-dev.txt

# Initialize Poetry in the new directory with Python version >=3.8,<4.0
poetry init --no-interaction --name "$PROJECT_NAME" --dependency "aws-cdk-lib" --dev-dependency "pytest" --python ">=3.8,<4.0"

echo "CDK and Poetry initialization completed in $PROJECT_DIR."

# Move files back to the top-level directory
cd ..
mv $PROJECT_DIR/* .
mv $PROJECT_DIR/.* . 2>/dev/null

# Remove the temporary project directory
rm -rf $PROJECT_DIR

echo "Files moved to the top-level directory and cleaned up."

echo "All steps completed successfully."
