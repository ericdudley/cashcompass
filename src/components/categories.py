from fasthtml.common import *
from src.components.layout import crud_page_layout
from src.models import Category


def category_card(cat: Category):
    return Div(
        Div(
            P(cat.label, cls="text-sm font-medium text-base-content"),
            Button(
                "✎",
                cls="btn btn-ghost btn-sm",
                title="Edit label",
                hx_get=f"/partials/categories/{cat.id}/edit",
                hx_target=f"#category-{cat.id}",
                hx_swap="outerHTML",
            ),
            cls="flex items-start justify-between gap-2",
        ),
        Div(
            Button(
                "Delete",
                cls="btn btn-ghost btn-xs text-error ml-auto",
                hx_delete=f"/categories/{cat.id}",
                hx_target=f"#category-{cat.id}",
                hx_swap="outerHTML",
                hx_confirm=f"Delete category '{cat.label}'? This cannot be undone.",
            ),
            cls="flex items-center gap-2",
        ),
        id=f"category-{cat.id}",
        data_label=cat.label,
        data_testid="category-card",
        cls="card cc-glass p-4 flex flex-col gap-3",
    )


def category_card_edit(cat: Category):
    return Div(
        Input(
            type="text",
            id=f"label-{cat.id}",
            name="label",
            value=cat.label,
            autofocus=True,
            onkeydown="if(event.key==='Enter'){event.preventDefault();this.closest('[id^=category-]').querySelector('button[hx-put]').click()}",
            cls="input input-bordered input-sm w-full",
        ),
        Div(
            Button(
                "Save",
                cls="btn btn-primary btn-sm",
                hx_put=f"/categories/{cat.id}/label",
                hx_include=f"#label-{cat.id}",
                hx_target=f"#category-{cat.id}",
                hx_swap="outerHTML",
            ),
            Button(
                "Cancel",
                cls="btn btn-ghost btn-sm",
                hx_get=f"/partials/categories/{cat.id}",
                hx_target=f"#category-{cat.id}",
                hx_swap="outerHTML",
            ),
            cls="flex gap-2",
        ),
        id=f"category-{cat.id}",
        data_label=cat.label,
        data_testid="category-card",
        cls="card cc-glass p-4 flex flex-col gap-3",
    )


def categories_list(cats: list[Category]):
    if cats:
        cards = [category_card(c) for c in cats]
    else:
        cards = [Div("No categories yet.", cls="rounded-xl border border-dashed border-base-300 p-6 text-sm cc-muted")]

    return Div(
        *cards,
        id="category-list",
        data_testid="categories",
        cls="grid gap-3 md:grid-cols-2",
    )


def category_form():
    return Div(
        H2("Add Category", cls="text-sm font-semibold text-base-content/80"),
        Form(
            Div(
                Label("Label", fr="cat-label", cls="label-text"),
                Input(
                    id="cat-label",
                    type="text",
                    name="label",
                    required=True,
                    placeholder="e.g. Groceries",
                    cls="input input-bordered w-full",
                ),
                cls="flex flex-col gap-1",
            ),
            Div(
                Button(
                    "Add category",
                    type="submit",
                    cls="btn btn-primary w-full sm:w-auto",
                ),
                cls="cc-form-actions",
            ),
            hx_post="/categories",
            hx_target="#category-list",
            hx_swap="outerHTML",
            hx_on="htmx:afterRequest: if(event.detail.successful) this.reset()",
            cls="cc-form-stack",
        ),
        cls="cc-crud-panel",
    )


def categories_page(cats: list[Category]):
    header = Header(H1("Categories", cls="cc-page-title text-4xl font-semibold text-base-content"), cls="space-y-2")
    return crud_page_layout(
        header,
        category_form(),
        categories_list(cats),
    )
