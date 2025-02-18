pip install --upgrade pip
pip3 install -r .devcontainer/requirements-dev.txt -r src/azurerambi/requirements.txt -r src/movie_generator_svc/requirements.txt -r src/movie_poster_svc/requirements.txt

(curl -sSL "https://github.com/buildpacks/pack/releases/download/v0.36.0/pack-v0.36.0-linux.tgz" | sudo tar -C /usr/local/bin/ --no-same-owner -xzv pack)