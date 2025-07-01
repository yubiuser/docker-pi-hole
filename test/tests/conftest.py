import pytest
import subprocess
import testinfra
import testinfra.backend.docker


# Monkeypatch sh to bash, if they ever support non hard code /bin/sh this can go away
# https://github.com/pytest-dev/pytest-testinfra/blob/master/testinfra/backend/docker.py
def run_bash(self, command, *args, **kwargs):
    cmd = self.get_command(command, *args)
    if self.user is not None:
        out = self.run_local(
            "docker exec -u %s %s /bin/bash -c %s", self.user, self.name, cmd
        )
    else:
        out = self.run_local("docker exec %s /bin/bash -c %s", self.name, cmd)
    out.command = self.encode(cmd)
    return out


testinfra.backend.docker.DockerBackend.run = run_bash


@pytest.fixture()
def args_env():
    return '-e TZ="Europe/London" -e FTLCONF_dns_upstreams="8.8.8.8"'


@pytest.fixture()
def args(args_env):
    return "{}".format(args_env)


@pytest.fixture()
def test_args():
    """test override fixture to provide arguments separate from our core args"""
    return ""


# scope='session' uses the same container for all the tests;
# scope='function' uses a new container per test function.
@pytest.fixture(scope="function")
def docker(request, test_args, args):
    # build the docker run command with args and test_args
    cmd = ["docker", "run", "-d", "-t"]

    # add args if provided
    if args.strip():
        cmd.extend(args.split())

    # add test_args if provided
    if test_args.strip():
        cmd.extend(test_args.split())

    # ensure PYTEST=1 is set
    if not any("PYTEST=1" in arg for arg in cmd):
        cmd.extend(["-e", "PYTEST=1"])

    # add the image name
    cmd.append("pihole:CI_container")

    # run a container
    docker_id = subprocess.check_output(cmd).decode().strip()
    # return a testinfra connection to the container
    yield testinfra.get_host("docker://" + docker_id)
    # at the end of the test suite, destroy the container
    subprocess.check_call(["docker", "rm", "-f", docker_id])
