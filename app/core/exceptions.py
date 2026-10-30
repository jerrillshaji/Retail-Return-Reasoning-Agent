"""Shared HTTP exception helpers."""

from fastapi import HTTPException, status


def not_found(item: str) -> HTTPException:
	return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{item} not found")
