import io

import paramiko

from app.config.settings import NFS_CFG


def up_nfs(data: bytes, name: str) -> str:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=NFS_CFG["ssh_host"],
        username=NFS_CFG["ssh_user"],
        password=NFS_CFG["ssh_pass"],
        timeout=10,
    )

    nfs_source = f"{NFS_CFG['host']}:{NFS_CFG['export']}"
    mount_point = NFS_CFG["mount_base"]
    remote_file = f"{mount_point}/{name}"

    try:
        ssh.exec_command(f"mkdir -p {mount_point}")

        _, _, stderr = ssh.exec_command(
            f"sudo mount -t nfs -o vers=3,nolock {nfs_source} {mount_point}"
        )
        stderr.channel.recv_exit_status()
        err = stderr.read().decode().strip()
        if err:
            raise RuntimeError(f"mount falló: {err}")

        sftp = ssh.open_sftp()
        sftp.putfo(io.BytesIO(data), remote_file)
        sftp.close()
    finally:
        ssh.exec_command(f"sudo umount {mount_point}")
        ssh.close()

    return f"NFS: '{name}' subido a {nfs_source} (usuario: usernfs)"
