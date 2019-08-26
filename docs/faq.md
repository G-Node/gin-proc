## Frequently Asked Questions

Q: Drone throws `permission denied (publickey)` error. How do I resolve this?

A: Add the line `- ssh -Tv git@172.19.0.2 -p 22 -i /root/.ssh/id_rsa` in your clone job in .drone.yml file before running `git clone`. It will present you with complete debug logs of the SSH connection drone tries to make from its container to your GIN container. Errors presented there can help you resolve the issue faster.

---

Q: I get a `Host Key authenticated failed` error during `git clone` in drone pipeline.

A: Either your SSH keys that you have added to GIN and to Drone as a secret don't match, or you can also check if the key pairs you installed needed your sudo password to unlock the keys. If that's the case, create new key pairs without passphrases. And install them.