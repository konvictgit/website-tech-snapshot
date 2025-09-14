{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/nixos-24.05.tar.gz") {} }:
pkgs.mkShell {
  buildInputs = [
    pkgs.nodejs_20
    pkgs.python310Full
    pkgs.postgresql
  ];
  shellHook = ''
    export DB_DSN="postgresql://webtech:webtechpass@localhost:5432/webtech"
    if [ ! -d .venv ]; then
      python -m venv .venv
      . .venv/bin/activate
      pip3 install -r scanner/requirements.txt
      pip3 install -r api/requirements.txt
    else
      . .venv/bin/activate
    fi
  '';
}
