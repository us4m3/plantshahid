#!/bin/sh
# create_env_file.sh
# Create or overwrite the .env file
echo "Creating .env file with environment variables..."

# Clear existing .env file if it exists
> .env

# Iterate over environment variables and write them to the .env file
for var in $(printenv)
do
  # Extract the variable name and value
  key=$(echo $var | cut -d'=' -f1)
  value=$(echo $var | cut -d'=' -f2-)

  # Write to .env in the format KEY=VALUE
  echo "$key=$value" >> .env
done

echo ".env file created."
