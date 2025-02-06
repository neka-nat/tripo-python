from typing import Any, Literal

from pydantic import BaseModel, validator, model_validator


ModelVersion = Literal[
    "default",
    "v2.5-20250123",
    "v2.0-20240919",
    "v1.4-20240625",
]


class FileToken(BaseModel):
    """File Token"""

    type: str | None = None
    file_token: str | None = None


class MultiviewFileTokens(BaseModel):
    """Multiview File Token"""

    front: FileToken | None = None
    left: FileToken | None = None
    back: FileToken | None = None
    right: FileToken | None = None

    def to_list(self) -> list[FileToken]:
        return [
            self.front or FileToken(),
            self.left or FileToken(),
            self.back or FileToken(),
            self.right or FileToken(),
        ]


class TaskInput(BaseModel):
    """Task Input"""

    type: str | None = None
    prompt: str | None = None
    negative_prompt: str | None = None
    model_version: str | None = None
    face_limit: int | None = None
    texture: bool | None = None
    pbr: bool | None = None
    file: FileToken | None = None
    files: list[FileToken] | None = None
    mode: str | None = None
    orthographic_projection: bool | None = None
    draft_model_task_id: str | None = None
    original_model_task_id: str | None = None
    out_format: str | None = None
    animation: str | None = None
    style: str | None = None
    block_size: int | None = None
    format: str | None = None
    quad: bool | None = None
    force_symmetry: bool | None = None
    flatten_bottom: bool | None = None
    flatten_bottom_threshold: float | None = None
    texture_size: int | None = None
    texture_format: str | None = None
    pivot_to_center_bottom: bool | None = None

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
            if not self.files:
                raise ValueError("files are required for type multiview_to_model")
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
    model: str | None = None
    base_model: str | None = None
    pbr_model: str | None = None
    rendered_image: str | None = None


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
