from fasthtml.common import Div


def form_error():
    return Div(role="alert", data_form_error="true", cls="hidden basis-full text-sm text-error")
