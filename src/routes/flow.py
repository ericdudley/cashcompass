from __future__ import annotations

from fasthtml.common import *

from src.components.flow import flow_page
from src.components.layout import page_layout
from src.services.flow import FlowService


def register(rt, flow_svc: FlowService):
    @rt("/flow", methods=["GET"])
    def get(req: Request):
        data = flow_svc.build(req.query_params.get("year", ""))
        return page_layout("flow", *flow_page(data))
