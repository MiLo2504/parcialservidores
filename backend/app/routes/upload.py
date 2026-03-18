from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config.settings import FRONTEND_HOLA_FILE, FRONTEND_TEMPLATES_DIR
from app.services.ftp_service import up_ftp
from app.services.nfs_service import up_nfs
from app.services.s3_service import up_s3
from app.services.smb_service import up_smb

router = APIRouter()
templates = Jinja2Templates(directory=str(FRONTEND_TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    index_template = FRONTEND_TEMPLATES_DIR / "index.html"
    if index_template.exists():
        return templates.TemplateResponse("index.html", {"request": request})

    if FRONTEND_HOLA_FILE.exists():
        return FileResponse(str(FRONTEND_HOLA_FILE), media_type="text/html")

    raise HTTPException(404, "No se encontró index.html ni hola.html en frontend")


@router.post("/upload")
async def upload(protocol: str = Form(...), file: UploadFile = File(...)):
    data = await file.read()
    name = file.filename or "archivo"

    try:
        if protocol == "s3":
            msg = up_s3(data, name)
        elif protocol == "ftp":
            msg = up_ftp(data, name)
        elif protocol == "smb":
            msg = up_smb(data, name)
        elif protocol == "nfs":
            msg = up_nfs(data, name)
        else:
            raise HTTPException(400, f"Protocolo desconocido: {protocol}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))

    return JSONResponse({"status": "ok", "message": msg})
