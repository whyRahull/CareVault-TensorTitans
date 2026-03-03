"""
Lost Child Search Router
POST /api/lost_child/search — placeholder until face-recognition models are available.
"""
from fastapi import APIRouter, UploadFile, File
from schemas import LostChildResponse

router = APIRouter()



@router.post("/search", response_model=LostChildResponse, summary="Search for a lost child (face match)")
async def search_lost_child(
    file: UploadFile = File(..., description="Image of the child to search for"),
):
    """
    Accepts an image and attempts to match it against a database of lost children.

    > **Note**: Face-recognition model not yet available — returns a placeholder response.
    """
    # read (and discard) the file so multipart parsing completes cleanly
    await file.read()

    return LostChildResponse(
        status="not_implemented",
        message="Lost child face-search model is not yet available. "
                "Upload the face-recognition model to ml_service/models/ to enable this feature.",
    )
