import logging
import os
from typing import Any, List, Optional, Union

import httpx
from pydantic import BaseModel

from .model import (
    Task,
    UploadFileData,
    SuccessTaskData,
    BalanceData,
    TaskInput,
    FileToken,
    MultiviewFileTokens,
    ModelVersion,
)


logger = logging.getLogger(__name__)


class DownloadedModelData(BaseModel):
    model: Optional[bytes]
    rendered_image: Optional[bytes]

    def save(self, path: str) -> None:
        if self.model is None:
            raise ValueError("Model is not downloaded")
        with open(path, "wb") as f:
            f.write(self.model)
        if self.rendered_image:
            with open(path.replace(".glb", ".png"), "wb") as f:
                f.write(self.rendered_image)


class APIError(Exception):
    """API Error"""

    def __init__(
        self,
        status_code: int,
        code: int,
        message: str,
        suggestion: Optional[str] = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.suggestion = suggestion
        super().__init__(f"API Error {code}: {message} (HTTP {status_code})")


class Client:
    """Tripo API Client"""

    def __init__(
        self,
        base_url: str = "https://api.tripo3d.ai/v2/openapi",
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url
        self.api_key = api_key or os.getenv("TRIPO_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Please provide it or set TRIPO_API_KEY environment variable."
            )

        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.client = httpx.Client(base_url=self.base_url, headers=self.headers)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.client.close()

    def close(self):
        self.client.close()

    def get_task(self, task_id: str) -> Task:
        """
        Get the status of a task.
        """
        url = f"/task/{task_id}"
        response = self.client.get(url)
        if response.status_code != 200:
            raise APIError(response.status_code, response.status_code, response.text)
        data = response.json()
        if data.get("code") != 0:
            raise APIError(
                status_code=response.status_code,
                code=data.get("code"),
                message=data.get("message", "Unknown error"),
                suggestion=data.get("suggestion"),
            )
        return Task(**data.get("data"))

    def try_download_model(self, task_id: str) -> Optional[DownloadedModelData]:
        task = self.get_task(task_id)
        model = None
        rendered_image = None
        logger.debug(f"Task: {task}")
        if task.status == "success":
            if task.input["pbr"]:
                if task.output.pbr_model is not None:
                    model = self._download_model(task.output.pbr_model)
            else:
                if task.output.model is not None:
                    model = self._download_model(task.output.model)
            if task.output.rendered_image is not None:
                rendered_image = self._download_model(task.output.rendered_image)
            return DownloadedModelData(model=model, rendered_image=rendered_image)
        else:
            return None

    def upload_file(self, file: Union[str, bytes, Any]) -> FileToken:
        """
        Upload a file.
        """
        url = "/upload"

        if isinstance(file, str):
            with open(file, "rb") as f:
                files = {"file": (file, f, f"image/{os.path.splitext(file)[1][1:]}")}
                response = self.client.post(url, files=files)
        else:
            files = {"file": file}
            response = self.client.post(url, files=files)
        if response.status_code != 200:
            raise APIError(response.status_code, response.status_code, response.text)
        data = response.json()
        if data.get("code") != 0:
            raise APIError(
                status_code=response.status_code,
                code=data.get("code"),
                message=data.get("message", "Unknown error"),
                suggestion=data.get("suggestion"),
            )
        data = UploadFileData(**data.get("data"))
        return FileToken(type=os.path.splitext(file)[1][1:], file_token=data.image_token)

    def create_task(self, task_input: TaskInput) -> SuccessTaskData:
        """
        Create a new task.
        """
        url = "/task"
        response = self.client.post(url, json=task_input.dict(exclude_unset=True))
        if response.status_code != 200:
            raise APIError(response.status_code, response.status_code, response.text)
        data = response.json()
        if data.get("code") != 0:
            raise APIError(
                status_code=response.status_code,
                code=data.get("code"),
                message=data.get("message", "Unknown error"),
                suggestion=data.get("suggestion"),
            )
        return SuccessTaskData(**data.get("data"))

    def get_balance(self) -> BalanceData:
        """
        Get the balance of the user.
        """
        url = "/user/balance"
        response = self.client.get(url)
        if response.status_code != 200:
            raise APIError(response.status_code, response.status_code, response.text)
        data = response.json()
        if data.get("code") != 0:
            raise APIError(
                status_code=response.status_code,
                code=data.get("code"),
                message=data.get("message", "Unknown error"),
                suggestion=data.get("suggestion"),
            )
        return BalanceData(**data.get("data"))

    def text_to_model(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        model_version: Optional[ModelVersion] = None,
        face_limit: Optional[int] = None,
        texture: Optional[bool] = None,
        pbr: Optional[bool] = None,
    ) -> SuccessTaskData:
        """
        Create a task to generate a model from text.
        """
        task_input = TaskInput(
            type="text_to_model",
            prompt=prompt,
            negative_prompt=negative_prompt,
            model_version=model_version,
            face_limit=face_limit,
            texture=texture,
            pbr=pbr,
        )
        return self.create_task(task_input)

    def image_to_model(
        self,
        file_token: FileToken,
        model_version: Optional[ModelVersion] = None,
        face_limit: Optional[int] = None,
        texture: Optional[bool] = None,
        pbr: Optional[bool] = None,
    ) -> SuccessTaskData:
        """
        Create a task to generate a model from an image.
        """
        task_input = TaskInput(
            type="image_to_model",
            file=file_token,
            model_version=model_version,
            face_limit=face_limit,
            texture=texture,
            pbr=pbr,
        )
        return self.create_task(task_input)

    def multiview_to_model(
        self,
        file_tokens: MultiviewFileTokens,
        model_version: Optional[ModelVersion] = None,
        face_limit: Optional[int] = None,
        texture: Optional[bool] = None,
        pbr: Optional[bool] = None,
    ) -> SuccessTaskData:
        """
        Create a task to generate a model from multiple views.
        """
        task_input = TaskInput(
            type="multiview_to_model",
            files=file_tokens.to_list(),
            model_version=model_version,
            face_limit=face_limit,
            texture=texture,
            pbr=pbr,
        )
        return self.create_task(task_input)

    def refine_model(
        self,
        draft_model_task_id: str,
    ) -> SuccessTaskData:
        """
        Create a task to refine a model.
        """
        task_input = TaskInput(
            type="refine_model",
            draft_model_task_id=draft_model_task_id,
        )
        return self.create_task(task_input)

    def stylize_model(
        self,
        style: str,
        original_model_task_id: str,
        block_size: Optional[int] = None,
    ) -> SuccessTaskData:
        """
        Create a task to stylize a model.
        """
        task_input = TaskInput(
            type="stylize_model",
            style=style,
            original_model_task_id=original_model_task_id,
            block_size=block_size,
        )
        return self.create_task(task_input)

    def convert_model(
        self,
        format: str,
        original_model_task_id: str,
        quad: Optional[bool] = None,
        force_symmetry: Optional[bool] = None,
        face_limit: Optional[int] = None,
        flatten_bottom: Optional[bool] = None,
        flatten_bottom_threshold: Optional[float] = None,
        texture_size: Optional[int] = None,
        texture_format: Optional[str] = None,
        pivot_to_center_bottom: Optional[bool] = None,
    ) -> SuccessTaskData:
        """
        Create a task to convert a model.
        """
        task_input = TaskInput(
            type="convert_model",
            format=format,
            original_model_task_id=original_model_task_id,
            quad=quad,
            force_symmetry=force_symmetry,
            face_limit=face_limit,
            flatten_bottom=flatten_bottom,
            flatten_bottom_threshold=flatten_bottom_threshold,
            texture_size=texture_size,
            texture_format=texture_format,
            pivot_to_center_bottom=pivot_to_center_bottom,
        )
        return self.create_task(task_input)

    def _download_model(self, url: str) -> bytes:
        logger.debug(f"Downloading model from {url}")
        response = self.client.get(url)
        if response.status_code == 200:
            return response.content
        else:
            raise APIError(response.status_code, response.status_code, response.text)


class AsyncClient:
    """Async Tripo API Client"""

    def __init__(
        self,
        base_url: str = "https://api.tripo3d.ai/v2/openapi",
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url
        self.api_key = api_key or os.getenv("TRIPO_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Please provide it or set TRIPO_API_KEY environment variable."
            )
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def close(self):
        await self.client.aclose()

    async def get_task(self, task_id: str) -> Task:
        """
        Get the status of a task asynchronously.
        """
        url = f"/task/{task_id}"
        response = await self.client.get(url)
        if response.status_code != 200:
            raise APIError(response.status_code, response.status_code, response.text)
        data = response.json()
        if data.get("code") != 0:
            raise APIError(
                status_code=response.status_code,
                code=data.get("code"),
                message=data.get("message", "Unknown error"),
                suggestion=data.get("suggestion"),
            )
        return Task(**data.get("data"))

    async def try_download_model(self, task_id: str) -> Optional[DownloadedModelData]:
        task = await self.get_task(task_id)
        model = None
        rendered_image = None
        logger.debug(f"Task: {task}")
        if task.status == "success":
            if task.input["pbr"]:
                if task.output.pbr_model is not None:
                    model = await self._download_model(task.output.pbr_model)
            else:
                if task.output.model is not None:
                    model = await self._download_model(task.output.model)
            if task.output.rendered_image is not None:
                rendered_image = await self._download_model(task.output.rendered_image)
            return DownloadedModelData(model=model, rendered_image=rendered_image)
        else:
            return None

    async def upload_file(self, file: Union[str, bytes, Any]) -> FileToken:
        """
        Upload a file asynchronously.
        """
        url = "/upload"

        if isinstance(file, str):
            with open(file, "rb") as f:
                files = {"file": (file, f, f"image/{os.path.splitext(file)[1][1:]}")}
                response = await self.client.post(url, files=files)
        else:
            files = {"file": file}
            response = await self.client.post(url, files=files)
        if response.status_code != 200:
            raise APIError(response.status_code, response.status_code, response.text)
        data = response.json()
        if data.get("code") != 0:
            raise APIError(
                status_code=response.status_code,
                code=data.get("code"),
                message=data.get("message", "Unknown error"),
                suggestion=data.get("suggestion"),
            )
        data = UploadFileData(**data.get("data"))
        return FileToken(type=os.path.splitext(file)[1][1:], file_token=data.image_token)

    async def create_task(self, task_input: TaskInput) -> SuccessTaskData:
        """
        Create a new task asynchronously.
        """
        url = "/task"
        response = await self.client.post(url, json=task_input.dict(exclude_unset=True))
        if response.status_code != 200:
            raise APIError(
                response.status_code, response.status_code, await response.text()
            )
        data = response.json()
        if data.get("code") != 0:
            raise APIError(
                status_code=response.status_code,
                code=data.get("code"),
                message=data.get("message", "Unknown error"),
                suggestion=data.get("suggestion"),
            )
        return SuccessTaskData(**data.get("data"))

    async def get_balance(self) -> BalanceData:
        """
        Get the balance of the user asynchronously.
        """
        url = "/user/balance"
        response = await self.client.get(url)
        if response.status_code != 200:
            raise APIError(
                response.status_code, response.status_code, await response.text()
            )
        data = response.json()
        if data.get("code") != 0:
            raise APIError(
                status_code=response.status_code,
                code=data.get("code"),
                message=data.get("message", "Unknown error"),
                suggestion=data.get("suggestion"),
            )
        return BalanceData(**data.get("data"))

    async def text_to_model(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        model_version: Optional[ModelVersion] = None,
        face_limit: Optional[int] = None,
        texture: Optional[bool] = None,
        pbr: Optional[bool] = None,
    ) -> SuccessTaskData:
        """
        Create a task to generate a model from text asynchronously.
        """
        task_input = TaskInput(
            type="text_to_model",
            prompt=prompt,
            negative_prompt=negative_prompt,
            model_version=model_version,
            face_limit=face_limit,
            texture=texture,
            pbr=pbr,
        )
        return await self.create_task(task_input)

    async def image_to_model(
        self,
        file_token: FileToken,
        model_version: Optional[ModelVersion] = None,
        face_limit: Optional[int] = None,
        texture: Optional[bool] = None,
        pbr: Optional[bool] = None,
    ) -> SuccessTaskData:
        """
        Create a task to generate a model from an image asynchronously.
        """
        task_input = TaskInput(
            type="image_to_model",
            file=file_token,
            model_version=model_version,
            face_limit=face_limit,
            texture=texture,
            pbr=pbr,
        )
        return await self.create_task(task_input)

    async def multiview_to_model(
        self,
        file_tokens: MultiviewFileTokens,
        model_version: Optional[ModelVersion] = None,
        face_limit: Optional[int] = None,
        texture: Optional[bool] = None,
        pbr: Optional[bool] = None,
    ) -> SuccessTaskData:
        """
        Create a task to generate a model from multiple views asynchronously.
        """
        task_input = TaskInput(
            type="multiview_to_model",
            files=file_tokens.to_list(),
            model_version=model_version,
            face_limit=face_limit,
            texture=texture,
            pbr=pbr,
        )
        return await self.create_task(task_input)

    async def refine_model(
        self,
        draft_model_task_id: str,
    ) -> SuccessTaskData:
        """
        Create a task to refine a model asynchronously.
        """
        task_input = TaskInput(
            type="refine_model",
            draft_model_task_id=draft_model_task_id,
        )
        return await self.create_task(task_input)

    async def stylize_model(
        self,
        style: str,
        original_model_task_id: str,
        block_size: Optional[int] = None,
    ) -> SuccessTaskData:
        """
        Create a task to stylize a model asynchronously.
        """
        task_input = TaskInput(
            type="stylize_model",
            style=style,
            original_model_task_id=original_model_task_id,
            block_size=block_size,
        )
        return await self.create_task(task_input)

    async def convert_model(
        self,
        format: str,
        original_model_task_id: str,
        quad: Optional[bool] = None,
        force_symmetry: Optional[bool] = None,
        face_limit: Optional[int] = None,
        flatten_bottom: Optional[bool] = None,
        flatten_bottom_threshold: Optional[float] = None,
        texture_size: Optional[int] = None,
        texture_format: Optional[str] = None,
        pivot_to_center_bottom: Optional[bool] = None,
    ) -> SuccessTaskData:
        """
        Create a task to convert a model asynchronously.
        """
        task_input = TaskInput(
            type="convert_model",
            format=format,
            original_model_task_id=original_model_task_id,
            quad=quad,
            force_symmetry=force_symmetry,
            face_limit=face_limit,
            flatten_bottom=flatten_bottom,
            flatten_bottom_threshold=flatten_bottom_threshold,
            texture_size=texture_size,
            texture_format=texture_format,
            pivot_to_center_bottom=pivot_to_center_bottom,
        )
        return await self.create_task(task_input)

    async def _download_model(self, url: str) -> bytes:
        logger.debug(f"Downloading model from {url}")
        response = await self.client.get(url)
        if response.status_code == 200:
            return response.content
        else:
            raise APIError(
                response.status_code, response.status_code, await response.text()
            )
