import ftplib
import io
import ssl

from app.config.settings import FTP_CFG


def up_ftp(data: bytes, name: str) -> str:
    def file_exists(ftp_client: ftplib.FTP, filename: str) -> bool:
        try:
            names = ftp_client.nlst()
            return filename in names
        except ftplib.all_errors:
            try:
                ftp_client.size(filename)
                return True
            except ftplib.all_errors:
                return False

    def upload_file(ftp_client: ftplib.FTP, filename: str, payload: bytes, passive: bool) -> None:
        ftp_client.set_pasv(passive)
        try:
            ftp_client.storbinary(f"STOR {filename}", io.BytesIO(payload))
        except ftplib.all_errors as exc:
            if "425" in str(exc) and file_exists(ftp_client, filename):
                return
            raise

    def upload_with_client(use_tls: bool) -> tuple[str, str]:
        if use_tls:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            ftp_client = ftplib.FTP_TLS(context=context)
        else:
            ftp_client = ftplib.FTP()
        try:
            ftp_client.connect(FTP_CFG["host"], FTP_CFG["port"], timeout=15)
            ftp_client.login(FTP_CFG["user"], FTP_CFG["password"])

            if use_tls:
                ftp_client.prot_p()

            target_dir = FTP_CFG["upload_dir"]
            try:
                ftp_client.cwd(target_dir)
            except ftplib.error_perm:
                try:
                    ftp_client.cwd("/")
                    target_dir = "/"
                except ftplib.error_perm as exc:
                    raise RuntimeError(
                        f"No se pudo acceder al directorio FTP configurado '{FTP_CFG['upload_dir']}' ni al root '/': {exc}"
                    )

            try:
                upload_file(ftp_client, name, data, passive=True)
            except ftplib.all_errors as exc:
                if "425" not in str(exc):
                    raise
                upload_file(ftp_client, name, data, passive=False)

            protocol = "FTPS" if use_tls else "FTP"
            return protocol, target_dir
        finally:
            try:
                ftp_client.quit()
            except ftplib.all_errors:
                try:
                    ftp_client.close()
                except ftplib.all_errors:
                    pass

    try:
        protocol, target_dir = upload_with_client(FTP_CFG["use_tls"])
    except ftplib.all_errors as exc:
        if "425" in str(exc):
            raise RuntimeError(
                "FTPS conectado pero falló canal de datos (425). En TrueNAS configura Passive Ports y, si aplica, Masquerade Address con la IP del servidor."
            )
        raise

    return f"{protocol}: '{name}' subido a {target_dir} (usuario: {FTP_CFG['user']})"
