pip install --upgrade pip
pip3 install -r .devcontainer/requirements-dev.txt
pip3 install -r src/gui_svc/requirements.txt
pip3 install -r src/movie_gallery_svc/requirements.txt
pip3 install -r src/movie_generator_svc/requirements.txt
pip3 install -r src/movie_poster_svc/requirements.txt
# install pack cli
(curl -sSL "https://github.com/buildpacks/pack/releases/download/v0.36.0/pack-v0.36.0-linux.tgz" | sudo tar -C /usr/local/bin/ --no-same-owner -xzv pack)
# upgrade az cli to latest version  (0.32) to get access the deployer() function
#az upgrade --yes
#curl -fsSL https://aka.ms/install-azd.sh | bash




