def success_response(data, meta: dict | None = None, message: str | None = None) -> dict:
    return {
        "success": True,
        "data": data,
        "message": message,
        "meta": meta or {},
    }


def pagination_meta(
    limit: int,
    offset: int,
    total: int,
) -> dict:
    return {
        "limit": limit,
        "offset": offset,
        "total": total,
        "has_more": offset + limit < total,
    }