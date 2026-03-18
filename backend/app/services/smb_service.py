import io

from smb.SMBConnection import SMBConnection

from app.config.settings import SMB_CFG


def up_smb(data: bytes, name: str) -> str:
    remote_name_candidates = [
        SMB_CFG.get("server_name", ""),
        SMB_CFG["host"],
        "TRUENAS",
        "truenas",
    ]
    remote_names = []
    for candidate in remote_name_candidates:
        if candidate and candidate not in remote_names:
            remote_names.append(candidate)

    connection = None
    for remote_name in remote_names:
        candidate_connection = SMBConnection(
            SMB_CFG["user"],
            SMB_CFG["password"],
            "fastapi-client",
            remote_name,
            domain=SMB_CFG["domain"],
            use_ntlm_v2=True,
            is_direct_tcp=True,
        )
        if candidate_connection.connect(SMB_CFG["host"], 445, timeout=10):
            connection = candidate_connection
            break

    if connection is None:
        raise RuntimeError(
            "No se pudo conectar a SMB. Define SMB_SERVER_NAME en .env con el nombre del servidor SMB (ej: truenas)."
        )

    try:
        connection.storeFile(SMB_CFG["share"], name, io.BytesIO(data))
    finally:
        connection.close()

    return f"SMB: '{name}' subido al share '{SMB_CFG['share']}' (usuario: usersmb)"
