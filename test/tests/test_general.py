import pytest
import os


@pytest.mark.parametrize("docker", ["PIHOLE_UID=456"], indirect=True)
def test_pihole_uid_env_var(docker):
    func = docker.run("echo ${PIHOLE_UID}")
    assert "456" in func.stdout
    func = docker.run(
        """
        id -u pihole
        """
    )
    assert "456" in func.stdout


@pytest.mark.parametrize("docker", ["PIHOLE_GID=456"], indirect=True)
def test_pihole_gid_env_var(docker):
    func = docker.run("echo ${PIHOLE_GID}")
    assert "456" in func.stdout
    func = docker.run(
        """
        id -g pihole
        """
    )
    assert "456" in func.stdout


def test_pihole_ftl_version(docker):
    func = docker.run("pihole-FTL -vv")
    assert func.rc == 0
    assert "Version:" in func.stdout


def test_pihole_ftl_architecture(docker):
    func = docker.run("pihole-FTL -vv")
    assert func.rc == 0
    assert "Architecture:" in func.stdout
    # Get the expected architecture from PLATFORM environment variable
    platform = os.environ.get("PLATFORM")
    assert platform in func.stdout


# Wait 5 seconds for startup, then kill the start.sh script
# Finally, grep the FTL log to see if it has been shut down cleanly
def test_pihole_ftl_clean_shutdown(docker):
    func = docker.run(
        """
        sleep 5
        killall --signal 15 start.sh
        sleep 5
        grep 'terminated' /var/log/pihole/FTL.log
    """
    )
    assert "INFO: ########## FTL terminated after" in func.stdout
    assert "(code 0)" in func.stdout


def test_cronfile_valid(docker):
    func = docker.run(
        """
        /usr/bin/crontab /crontab.txt
        crond -d 8 -L /cron.log
        grep 'parse error' /cron.log
    """
    )
    assert "parse error" not in func.stdout
