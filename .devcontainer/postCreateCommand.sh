pip3 install -r .devcontainer/requirements-dev.txt
pip3 install -e src

# git config
git config --global --add safe.directory /workspaces/azure-rambi
git config alias.co checkout
git config alias.br branch
git config alias.ci commit
git config alias.st status
git config alias.lg "log --color --graph --pretty=format:'%Cred%h%Creset --%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue) %Creset' --abbrev-commit"
git config alias.lg2 "log --oneline --graph --all"
git config alias.lga "log --oneline --graph --all --decorate"
git config alias.lgb "log --oneline --graph --all --decorate --branches"
git config alias.lgt "log --oneline --graph --all --decorate --tags"
git config alias.lgtb "log --oneline --graph --all --decorate --tags --branches"
git config alias.latest "for-each-ref --sort=-committerdate --format='%(refname:short) %(committerdate:short)' refs/heads"
git config color.branch auto
git config color.diff auto
git config color.status auto
