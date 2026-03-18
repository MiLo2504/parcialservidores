import io

from smb.SMBConnection import SMBConnection

from app.config.settings import SMB_CFG


def up_smb(data: bytes, name: str) -> str:
    connection = SMBConnection(
        SMB_CFG["user"],
        SMB_CFG["password"],
        "fastapi-client",
        SMB_CFG["host"],
        domain=SMB_CFG["domain"],
        use_ntlm_v2=True,
    )

    if not connection.connect(SMB_CFG["host"], 445, timeout=10):
        raise RuntimeError("No se pudo conectar a SMB")

    try:
        connection.storeFile(SMB_CFG["share"], name, io.BytesIO(data))
    finally:
        connection.close()

    return f"SMB: '{name}' subido al share '{SMB_CFG['share']}' (usuario: usersmb)"
