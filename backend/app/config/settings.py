import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("TRUENAS_HOST", "192.168.56.103")

BASE_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BASE_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_TEMPLATES_DIR = PROJECT_ROOT / "frontend" / "templates"
FRONTEND_HOLA_FILE = FRONTEND_DIR / "hola.html"

MINIO_CFG = {
    "endpoint": os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    "access_key": os.getenv("MINIO_ACCESS_KEY", "users3"),
    "secret_key": os.getenv("MINIO_SECRET_KEY", "demo1234"),
    "bucket": os.getenv("MINIO_BUCKET", "demo-bucket"),
    "secure": os.getenv("MINIO_SECURE", "false").lower() == "true",
}

FTP_CFG = {
    "host": os.getenv("FTP_HOST", HOST),
    "port": int(os.getenv("FTP_PORT", "21")),
    "user": os.getenv("FTP_USER", "userftp"),
    "password": os.getenv("FTP_PASS", "Demo1234!"),
    "use_tls": os.getenv("FTP_USE_TLS", "true").lower() == "true",
    "upload_dir": os.getenv("FTP_UPLOAD_DIR", "/mnt/camiloykarol/ftp_data"),
}

SMB_CFG = {
    "host": os.getenv("SMB_HOST", HOST),
    "share": os.getenv("SMB_SHARE", "smb_data"),
    "user": os.getenv("SMB_USER", "usersmb"),
    "password": os.getenv("SMB_PASS", "Demo1234!"),
    "domain": os.getenv("SMB_DOMAIN", "WORKGROUP"),
}

NFS_CFG = {
    "ssh_host": os.getenv("NFS_SSH_HOST", "192.168.56.104"),
    "ssh_user": os.getenv("NFS_SSH_USER", "milo"),
    "ssh_pass": os.getenv("NFS_SSH_PASS", "milo"),
    "host": os.getenv("NFS_HOST", HOST),
    "export": os.getenv("NFS_EXPORT", "/mnt/camiloykarol/nfs_data"),
    "mount_base": os.getenv("NFS_MOUNT_BASE", "/tmp/nfs_demo"),
}
