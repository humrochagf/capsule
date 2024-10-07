import json
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.datastructures import Headers
from fastapi.routing import APIRoute


class MultiContentTypeRequest(Request):
    async def body(self) -> bytes:
        if not hasattr(self, "_body"):
            body = await super().body()
            content_type = (
                self.headers.get("content-type", "").split(";", 1)[0].lower().strip()
            )

            if content_type == "application/x-www-form-urlencoded":
                form = await super().form()
                body = json.dumps(form._dict).encode()
                headers = self.headers.mutablecopy()
                headers["content-type"] = "application/json"

                self._headers = Headers(headers)

            self._body = body
        return self._body


class MultiContentTypeRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request = MultiContentTypeRequest(request.scope, request.receive)
            return await original_route_handler(request)

        return custom_route_handler
