SSH_PORT = 22
SSH_BOOTSTRAP_PATH = "/opt/polyaxon/bin/bootstrap-ssh.sh"
SSH_IDLE_COMMAND = ["tail", "-f", "/dev/null"]

SSH_ETC_PATH = "/opt/polyaxon/etc"
SSH_HOST_KEY_PATH = "{}/ssh_host_ed25519_key".format(SSH_ETC_PATH)
SSH_AUTHORIZED_KEYS_PATH = "{}/authorized_keys".format(SSH_ETC_PATH)
