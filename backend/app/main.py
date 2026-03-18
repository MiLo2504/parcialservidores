import os
import io
import ssl
import ftplib
import subprocess
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

HOST = os.getenv("TRUENAS_HOST", "192.168.56.103")

MINIO_CFG = {
    "endpoint":   os.getenv("MINIO_ENDPOINT",   "localhost:9000"),
    "access_key": os.getenv("MINIO_ACCESS_KEY", "users3"),
    "secret_key": os.getenv("MINIO_SECRET_KEY", "demo1234"),
    "bucket":     os.getenv("MINIO_BUCKET",     "demo-bucket"),
    "secure":     os.getenv("MINIO_SECURE",     "false").lower() == "true",
}

FTP_CFG = {
    "host":       os.getenv("FTP_HOST",       HOST),
    "port":       int(os.getenv("FTP_PORT",   "21")),
    "user":       os.getenv("FTP_USER",       "userftp"),
    "password":   os.getenv("FTP_PASS",       "Demo1234!"),
    "use_tls":    os.getenv("FTP_USE_TLS",    "true").lower() == "true",
    "upload_dir": os.getenv("FTP_UPLOAD_DIR", "/mnt/camiloykarol/ftp_data"),
}

SMB_CFG = {
    "host":     os.getenv("SMB_HOST",   HOST),
    "share":    os.getenv("SMB_SHARE",  "smb_data"),
    "user":     os.getenv("SMB_USER",   "usersmb"),
    "password": os.getenv("SMB_PASS",   "Demo1234!"),
    "domain":   os.getenv("SMB_DOMAIN", "WORKGROUP"),
}

NFS_CFG = {
    "ssh_host":   os.getenv("NFS_SSH_HOST",   "192.168.56.104"),
    "ssh_user":   os.getenv("NFS_SSH_USER",   "milo"),
    "ssh_pass":   os.getenv("NFS_SSH_PASS",   "milo"),
    "host":       os.getenv("NFS_HOST",       HOST),
    "export":     os.getenv("NFS_EXPORT",     "/mnt/camiloykarol/nfs_data"),
    "mount_base": os.getenv("NFS_MOUNT_BASE", "/tmp/nfs_demo"),
}


# ── Rutas ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload(protocol: str = Form(...), file: UploadFile = File(...)):
    data = await file.read()
    name = file.filename or "archivo"
    try:
        if   protocol == "s3":  msg = up_s3(data, name)
        elif protocol == "ftp": msg = up_ftp(data, name)
        elif protocol == "smb": msg = up_smb(data, name)
        elif protocol == "nfs": msg = up_nfs(data, name)
        else: raise HTTPException(400, f"Protocolo desconocido: {protocol}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    return JSONResponse({"status": "ok", "message": msg})


# ── S3 / MinIO ───────────────────────────────────────────────────────────────

def up_s3(data: bytes, name: str) -> str:
    from minio import Minio
    c = Minio(
        MINIO_CFG["endpoint"],
        access_key=MINIO_CFG["access_key"],
        secret_key=MINIO_CFG["secret_key"],
        secure=MINIO_CFG["secure"]
    )
    b = MINIO_CFG["bucket"]
    if not c.bucket_exists(b):
        c.make_bucket(b)
    c.put_object(b, name, io.BytesIO(data), len(data))
    return f"S3/MinIO: '{name}' subido al bucket '{b}'"


# ── FTP / FTPS ───────────────────────────────────────────────────────────────

def up_ftp(data: bytes, name: str) -> str:
    if FTP_CFG["use_tls"]:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ftp = ftplib.FTP_TLS(context=ctx)
    else:
        ftp = ftplib.FTP()

    ftp.connect(FTP_CFG["host"], FTP_CFG["port"], timeout=15)
    ftp.login(FTP_CFG["user"], FTP_CFG["password"])

    if FTP_CFG["use_tls"]:
        ftp.prot_p()

    try:
        ftp.cwd(FTP_CFG["upload_dir"])
    except ftplib.error_perm:
        ftp.mkd(FTP_CFG["upload_dir"])
        ftp.cwd(FTP_CFG["upload_dir"])

    ftp.storbinary(f"STOR {name}", io.BytesIO(data))
    ftp.quit()

    proto = "FTPS" if FTP_CFG["use_tls"] else "FTP"
    return f"{proto}: '{name}' subido a {FTP_CFG['upload_dir']} (usuario: userftp)"


# ── SMB ──────────────────────────────────────────────────────────────────────

def up_smb(data: bytes, name: str) -> str:
    from smb.SMBConnection import SMBConnection
    conn = SMBConnection(
        SMB_CFG["user"],
        SMB_CFG["password"],
        "fastapi-client",
        SMB_CFG["host"],
        domain=SMB_CFG["domain"],
        use_ntlm_v2=True
    )
    if not conn.connect(SMB_CFG["host"], 445, timeout=10):
        raise RuntimeError("No se pudo conectar a SMB")
    try:
        conn.storeFile(SMB_CFG["share"], name, io.BytesIO(data))
    finally:
        conn.close()
    return f"SMB: '{name}' subido al share '{SMB_CFG['share']}' (usuario: usersmb)"


# ── NFS via SSH ──────────────────────────────────────────────────────────────

def up_nfs(data: bytes, name: str) -> str:
    import paramiko

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=NFS_CFG["ssh_host"],
        username=NFS_CFG["ssh_user"],
        password=NFS_CFG["ssh_pass"],
        timeout=10
    )

    nfs_src  = f"{NFS_CFG['host']}:{NFS_CFG['export']}"
    mount_pt = NFS_CFG["mount_base"]
    remote_file = f"{mount_pt}/{name}"

    try:
        # Crear punto de montaje
        ssh.exec_command(f"mkdir -p {mount_pt}")

        # Montar NFS
        _, stdout, stderr = ssh.exec_command(
            f"sudo mount -t nfs -o vers=3,nolock {nfs_src} {mount_pt}"
        )
        stderr.channel.recv_exit_status()
        err = stderr.read().decode().strip()
        if err:
            raise RuntimeError(f"mount falló: {err}")

        # Copiar archivo via SFTP
        sftp = ssh.open_sftp()
        sftp.putfo(io.BytesIO(data), remote_file)
        sftp.close()

    finally:
        ssh.exec_command(f"sudo umount {mount_pt}")
        ssh.close()

    return f"NFS: '{name}' subido a {nfs_src} (usuario: usernfs)"