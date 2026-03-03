"""
SOS Alert Router
================
Validates and formats emergency alert payloads.
Email delivery is handled by the Django backend — not here.

POST /api/sos/send      — generic emergency SOS payload
POST /api/sos/travel    — travel-details alert payload
"""
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from schemas import SOSResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/send", response_model=SOSResponse, summary="Build emergency SOS alert payload")
async def send_sos(
    receiver_emails: str = Form(..., description="Comma-separated recipient emails"),
    message: str = Form(..., description="Emergency message body"),
    image: Optional[UploadFile] = File(None, description="Optional image attachment"),
):
    """
    Validates the SOS alert payload and returns structured data.
    **Email delivery is handled by Django** — call this endpoint to get a
    validated response before dispatching the email from the Django backend.
    """
    email_list = [e.strip() for e in receiver_emails.split(",") if e.strip()]
    if not email_list:
        raise HTTPException(status_code=422, detail="No valid recipient emails provided.")
    if not message.strip():
        raise HTTPException(status_code=422, detail="message must not be empty.")

    image_filename = image.filename if image else None

    return SOSResponse(
        subject="🚨 URGENT: Emergency Assistance Needed!",
        recipients=email_list,
        body=message.strip(),
        image_filename=image_filename,
    )


@router.post("/travel", response_model=SOSResponse, summary="Build travel-details alert payload")
async def send_travel_alert(
    receiver_emails: str = Form(...),
    vehicle_number: str = Form(...),
    vehicle_type: str = Form(...),
    vehicle_color: str = Form(...),
    driver_name: str = Form(...),
    location: str = Form(...),
    message: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
):
    """
    Validates and formats a travel-details emergency alert payload.
    **Email delivery is handled by the Django backend.**
    """
    email_list = [e.strip() for e in receiver_emails.split(",") if e.strip()]
    if not email_list:
        raise HTTPException(status_code=422, detail="No valid recipient emails provided.")

    body = (
        f"🚨 Emergency Alert from CareVault SOS Hub\n\n"
        f"Vehicle Details:\n"
        f"  Number : {vehicle_number}\n"
        f"  Type   : {vehicle_type}\n"
        f"  Color  : {vehicle_color}\n\n"
        f"Driver  : {driver_name}\n"
        f"Location: {location}\n\n"
        f"Additional Message:\n{message.strip() if message else 'No additional information provided.'}"
    )

    image_filename = image.filename if image else None

    return SOSResponse(
        subject="🚨 CareVault Emergency Travel Alert",
        recipients=email_list,
        body=body,
        image_filename=image_filename,
    )
