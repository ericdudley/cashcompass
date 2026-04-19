from fasthtml.common import *
from src.models import Category


def category_card(cat: Category):
    return Div(
        Div(
            P(cat.label, cls="text-sm font-medium text-slate-100"),
            Button(
                "✎",
                cls="rounded p-1 text-slate-400 hover:text-slate-100 hover:bg-slate-700 transition",
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
                cls="rounded px-2 py-1 text-xs text-red-400/70 border border-slate-700 hover:border-red-400/50 hover:text-red-400 transition ml-auto",
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
        cls="relative rounded-xl border border-emerald-200/20 bg-slate-900/70 p-4 flex flex-col gap-3",
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
            cls="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-100 focus:border-emerald-400 focus:outline-none",
        ),
        Div(
            Button(
                "Save",
                cls="rounded px-3 py-1.5 text-xs font-semibold bg-emerald-400 text-slate-950 hover:bg-emerald-300 transition",
                hx_put=f"/categories/{cat.id}/label",
                hx_include=f"#label-{cat.id}",
                hx_target=f"#category-{cat.id}",
                hx_swap="outerHTML",
            ),
            Button(
                "Cancel",
                cls="rounded px-3 py-1.5 text-xs text-slate-400 border border-slate-700 hover:text-slate-100 transition",
                hx_get=f"/partials/categories/{cat.id}",
                hx_target=f"#category-{cat.id}",
                hx_swap="outerHTML",
            ),
            cls="flex gap-2",
        ),
        id=f"category-{cat.id}",
        data_label=cat.label,
        data_testid="category-card",
        cls="rounded-xl border border-emerald-400/40 bg-slate-900/70 p-4 flex flex-col gap-3",
    )


def categories_list(cats: list[Category]):
    if cats:
        cards = [category_card(c) for c in cats]
    else:
        cards = [Div("No categories yet.", cls="rounded-xl border border-dashed border-slate-700 p-6 text-sm text-slate-400")]

    return Div(
        *cards,
        id="category-list",
        data_testid="categories",
        cls="grid gap-3 md:grid-cols-2",
    )


def category_form():
    return Form(
        Div(
            Label("Label", fr="cat-label", cls="text-xs text-slate-400"),
            Input(
                id="cat-label",
                type="text",
                name="label",
                required=True,
                placeholder="e.g. Groceries",
                cls="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-100 focus:border-emerald-400 focus:outline-none",
            ),
            cls="flex flex-col gap-1",
        ),
        Button(
            "Add category",
            type="submit",
            cls="rounded-full bg-emerald-400 px-5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300",
        ),
        hx_post="/categories",
        hx_target="#category-list",
        hx_swap="outerHTML",
        hx_on="htmx:afterRequest: if(event.detail.successful) this.reset()",
        cls="flex flex-wrap items-end gap-3 rounded-xl border border-slate-700 bg-slate-900/50 p-4",
    )


def categories_page(cats: list[Category]):
    return (
        Header(H1("Categories", cls="text-4xl font-semibold text-white"), cls="space-y-2"),
        category_form(),
        categories_list(cats),
    )
