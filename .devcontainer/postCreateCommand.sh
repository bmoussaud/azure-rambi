pip3 install -r .devcontainer/requirements-dev.txt
#pip3 install -e src


(curl -sSL "https://github.com/buildpacks/pack/releases/download/v0.36.0/pack-v0.36.0-linux.tgz" | sudo tar -C /usr/local/bin/ --no-same-owner -xzv pack)