import os
import shutil
import logging
from fastapi import UploadFile, HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.allowed_extensions = settings.parsed_allowed_extensions
        self.max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        os.makedirs(self.upload_dir, exist_ok=True)

    def validate_file(self, file: UploadFile):
        """
        Validate file extension and size.
        """
        filename = file.filename or ""
        ext = os.path.splitext(filename)[1].replace(".", "").lower()
        
        if ext not in self.allowed_extensions:
            logger.warning(f"File validation failed: '{filename}' extension '.{ext}' is not allowed.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '.{ext}' is not allowed. Supported: {', '.join(self.allowed_extensions)}"
            )

    async def save_file(self, file: UploadFile) -> str:
        """
        Save the uploaded file to disk and return the path.
        """
        self.validate_file(file)
        
        filename = file.filename or "unknown_file"
        file_path = os.path.join(self.upload_dir, filename)
        
        try:
            logger.info(f"Saving uploaded file: {filename} to {file_path}")
            # Stream upload in chunks to prevent memory bloat
            with open(file_path, "wb") as buffer:
                # Track size during saving to enforce max file size limit
                total_bytes = 0
                while True:
                    content = await file.read(1024 * 1024)  # Read in chunks of 1MB
                    if not content:
                        break
                    total_bytes += len(content)
                    if total_bytes > self.max_size_bytes:
                        # Clean up partial file
                        buffer.close()
                        os.remove(file_path)
                        logger.warning(f"File upload size limit exceeded: {filename}")
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
                        )
                    buffer.write(content)
            return file_path
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving file '{filename}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not save file to disk: {str(e)}"
            )

    def delete_file(self, filename: str) -> bool:
        """
        Delete a file from the uploads directory.
        """
        file_path = os.path.join(self.upload_dir, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"File deleted from storage: {file_path}")
                return True
            except Exception as e:
                logger.error(f"Error deleting file from disk: {e}")
                return False
        logger.warning(f"File to delete not found: {file_path}")
        return False

storage_service = StorageService()

def get_storage_service() -> StorageService:
    return storage_service
