from datetime import date, datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    admin = "admin"
    doctor = "doctor"
    radiologist = "radiologist"


class ScanType(str, Enum):
    chest_xray = "chest_xray"
    brain_mri = "brain_mri"
    brain_ct = "brain_ct"
    chest_ct = "chest_ct"
    abdomen_ct = "abdomen_ct"


class ReportStatus(str, Enum):
    pending = "pending"
    ai_generated = "ai_generated"
    reviewed = "reviewed"
    finalized = "finalized"
    amended = "amended"


class SeverityLevel(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


# ---------- Auth ----------
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole = UserRole.doctor
    specialty: Optional[str] = None
    license_number: Optional[str] = None


class AdminCreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole
    specialty: Optional[str] = None
    license_number: Optional[str] = None
    hospital_affiliation: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class CurrentUser(BaseModel):
    id: str
    email: Optional[str] = None
    role: UserRole
    full_name: Optional[str] = None


# ---------- Users ----------
class UserProfile(BaseModel):
    id: str
    email: Optional[str] = None
    full_name: str
    role: UserRole
    specialty: Optional[str] = None
    license_number: Optional[str] = None
    hospital_affiliation: Optional[str] = None
    is_active: bool = True


# ---------- Patients ----------
class PatientCreate(BaseModel):
    patient_code: str
    full_name: str
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[EmailStr] = None
    medical_history: dict[str, Any] = Field(default_factory=dict)


class PatientOut(PatientCreate):
    id: str
    created_at: datetime


# ---------- Medical Images ----------
class MedicalImageOut(BaseModel):
    id: str
    patient_id: str
    scan_type: ScanType
    storage_path: str
    original_filename: str
    file_format: str
    uploaded_at: datetime


# ---------- AI Predictions ----------
class DiseasePrediction(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=100)


class AIPredictionOut(BaseModel):
    model_config = {"protected_namespaces": ()}

    id: str
    image_id: str
    model_name: str
    model_version: str
    predictions: list[DiseasePrediction]
    top_prediction: Optional[str] = None
    top_confidence: Optional[float] = None
    heatmap_storage_path: Optional[str] = None


# ---------- Reports ----------
class ReportOut(BaseModel):
    id: str
    patient_id: str
    image_id: str
    status: ReportStatus
    severity: Optional[SeverityLevel] = None
    examination: Optional[str] = None
    clinical_findings: Optional[str] = None
    image_findings: Optional[str] = None
    impression: Optional[str] = None
    recommendation: Optional[str] = None
    suggested_followup: Optional[str] = None
    confidence_summary: Optional[str] = None
    pdf_storage_path: Optional[str] = None
    created_at: datetime
