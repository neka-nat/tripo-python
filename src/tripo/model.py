from typing import Any, Literal, Optional

from pydantic import BaseModel, validator, model_validator


ModelVersion = Literal[
    "default",
    "v2.0-20240919",
    "v1.4-20240625",
    "v1.3-20240522",
]


class FileToken(BaseModel):
    """File Token"""

    type: str
    file_token: str


class TaskInput(BaseModel):
    """Task Input"""

    type: str
    prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    model_version: Optional[str] = None
    face_limit: Optional[int] = None
    texture: Optional[bool] = None
    pbr: Optional[bool] = None
    file: Optional[FileToken] = None
    files: Optional[list[FileToken]] = None
    mode: Optional[str] = None
    orthographic_projection: Optional[bool] = None
    draft_model_task_id: Optional[str] = None
    original_model_task_id: Optional[str] = None
    out_format: Optional[str] = None
    animation: Optional[str] = None
    style: Optional[str] = None
    block_size: Optional[int] = None
    format: Optional[str] = None
    quad: Optional[bool] = None
    force_symmetry: Optional[bool] = None
    flatten_bottom: Optional[bool] = None
    flatten_bottom_threshold: Optional[float] = None
    texture_size: Optional[int] = None
    texture_format: Optional[str] = None
    pivot_to_center_bottom: Optional[bool] = None

    @validator("type")
    def validate_type(cls, v):
        allowed_types = [
            "text_to_model",
            "image_to_model",
            "multiview_to_model",
            "refine_model",
            "animate_prerigcheck",
            "animate_rig",
            "animate_retarget",
            "stylize_model",
            "convert_model",
        ]
        if v not in allowed_types:
            raise ValueError(f"Invalid type: {v}")
        return v

    @model_validator(mode="after")
    def check_required_fields(self):
        task_type = self.type
        if task_type == "text_to_model":
            if not self.prompt:
                raise ValueError("prompt is required for type text_to_model")
        elif task_type == "image_to_model":
            if not self.file:
                raise ValueError("file is required for type image_to_model")
        elif task_type == "multiview_to_model":
            if not self.files or not self.mode:
                raise ValueError(
                    "files and mode are required for type multiview_to_model"
                )
        elif task_type == "refine_model":
            if not self.draft_model_task_id:
                raise ValueError(
                    "draft_model_task_id is required for type refine_model"
                )
        elif task_type == "animate_prerigcheck":
            if not self.original_model_task_id:
                raise ValueError(
                    "original_model_task_id is required for type animate_prerigcheck"
                )
        elif task_type == "animate_rig":
            if not self.original_model_task_id:
                raise ValueError(
                    "original_model_task_id is required for type animate_rig"
                )
        elif task_type == "animate_retarget":
            if not self.original_model_task_id or not self.animation:
                raise ValueError(
                    "original_model_task_id and animation are required for type animate_retarget"
                )
        elif task_type == "stylize_model":
            if not self.style or not self.original_model_task_id:
                raise ValueError(
                    "style and original_model_task_id are required for type stylize_model"
                )
        elif task_type == "convert_model":
            if not self.format or not self.original_model_task_id:
                raise ValueError(
                    "format and original_model_task_id are required for type convert_model"
                )
        return self


class TaskOutput(BaseModel):
    model: Optional[str] = None
    base_model: Optional[str] = None
    pbr_model: Optional[str] = None
    rendered_image: Optional[str] = None


class Task(BaseModel):
    task_id: str
    type: str
    status: str
    input: dict[str, Any]
    output: TaskOutput
    progress: int
    create_time: int


class SuccessTaskData(BaseModel):
    task_id: str


class SuccessTask(BaseModel):
    code: int
    data: SuccessTaskData


class BalanceData(BaseModel):
    balance: float
    frozen: float


class Balance(BaseModel):
    code: int
    data: BalanceData


class UploadFileData(BaseModel):
    image_token: str


class UploadFileResponse(BaseModel):
    code: int
    data: UploadFileData
