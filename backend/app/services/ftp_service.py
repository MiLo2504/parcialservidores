import ftplib
import io
import ssl

from app.config.settings import FTP_CFG


def up_ftp(data: bytes, name: str) -> str:
    if FTP_CFG["use_tls"]:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        ftp = ftplib.FTP_TLS(context=context)
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

    protocol = "FTPS" if FTP_CFG["use_tls"] else "FTP"
    return f"{protocol}: '{name}' subido a {FTP_CFG['upload_dir']} (usuario: userftp)"
